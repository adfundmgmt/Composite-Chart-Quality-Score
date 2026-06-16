"""
CCQS V1 — Data Layer (SPEC Section 4)

yfinance batch fetcher for ~892 universe tickers + 2 benchmarks (SPY/QQQ).

Behavior:
  - ~7-year lookback (LOOKBACK_DAYS = 7*365 + 60 ≈ 1,824 calendar days;
    supports CCQS history back to 2020-01-01 after 252d feature warm-up)
  - Batch download (max 100 per batch) to play nice with Yahoo throttling
  - 3-attempt retry per batch with exponential backoff
  - Parquet caching with 3-hour TTL (market hours) / 18-hour TTL (after close)
  - Last-good fallback if a refresh fails entirely
  - Validates returned data shape and required columns
  - Logs failed tickers for downstream awareness

Outputs to data/cache/:
  - ohlcv_daily.parquet     (long-format: ticker, date, open, high, low, close,
                             adj_close, volume)
  - ohlcv_meta.json         (pull timestamp, ticker counts, date range)
  - failed_tickers.json     (tickers that failed fetch and why)

Run standalone:
    python -m compute.loader
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from loguru import logger

from data.universe import BENCHMARKS, all_unique_tickers

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
LOG_DIR = PROJECT_ROOT / "logs"

OHLCV_PATH = CACHE_DIR / "ohlcv_daily.parquet"
META_PATH = CACHE_DIR / "ohlcv_meta.json"
FAILED_PATH = CACHE_DIR / "failed_tickers.json"

LOOKBACK_DAYS = 7 * 365 + 60  # ~7 years calendar — supports CCQS history back to 2020-01-01 after 252d feature warm-up
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5

# Self-heal: a frame with fewer than this many bars cannot produce the 200d MA
# (or 50d/60d-vol features) and would silently drop from CCQS scoring. yfinance
# intermittently returns such truncated frames for a subset of a batch — they
# pass the lenient per-ticker validation but lack history. We re-fetch each one
# individually (there is no persisted last-good OHLCV on CI to fall back on) and
# keep whichever attempt has the most bars. Genuine recent IPOs simply re-confirm
# their true short history. Root cause of the 2026-06-15 coverage regression.
SUSPICIOUS_MIN_BARS = 210  # just above the 200d-MA requirement
REFETCH_MAX_ATTEMPTS = 2

TTL_MARKET_HOURS = timedelta(hours=3)
TTL_AFTER_CLOSE = timedelta(hours=18)

REQUIRED_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(sys.stdout, level="INFO", format="<level>{level: <8}</level> | {message}")
logger.add(LOG_DIR / "ccqs.log", level="DEBUG", rotation="10 MB", retention="30 days")


# ---------------------------------------------------------------------------
# Cache TTL logic
# ---------------------------------------------------------------------------

def _is_market_hours(now: datetime) -> bool:
    """Rough US market hours check (9:30am-4pm ET, Mon-Fri). Used only for TTL."""
    et = now.astimezone(timezone(timedelta(hours=-5)))  # rough EST/EDT
    if et.weekday() >= 5:
        return False
    minutes = et.hour * 60 + et.minute
    return 9 * 60 + 30 <= minutes <= 16 * 60


def _cache_is_fresh() -> bool:
    if not OHLCV_PATH.exists() or not META_PATH.exists():
        return False
    try:
        meta = json.loads(META_PATH.read_text())
        pulled_at = datetime.fromisoformat(meta["pulled_at"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return False
    now = datetime.now(timezone.utc)
    ttl = TTL_MARKET_HOURS if _is_market_hours(now) else TTL_AFTER_CLOSE
    return (now - pulled_at) < ttl


# ---------------------------------------------------------------------------
# yfinance batch download
# ---------------------------------------------------------------------------

def _normalize_yf_frame(df: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
    """
    yfinance returns either a multi-index DataFrame (multiple tickers) or a flat
    DataFrame (single ticker). Normalize to {ticker -> DataFrame[OHLCV]}.
    """
    out: dict[str, pd.DataFrame] = {}

    if df is None or df.empty:
        return out

    # Multi-ticker: columns are MultiIndex (field, ticker) — preferred with
    # group_by='column'. We unstack into per-ticker frames.
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance has used both orderings historically. Detect which level
        # holds the tickers.
        level0 = set(df.columns.get_level_values(0))
        if any(t in level0 for t in tickers):
            ticker_level = 0
            field_level = 1
        else:
            ticker_level = 1
            field_level = 0

        for ticker in tickers:
            if ticker not in df.columns.get_level_values(ticker_level):
                continue
            if ticker_level == 0:
                sub = df[ticker].copy()
            else:
                sub = df.xs(ticker, axis=1, level=ticker_level).copy()
            sub.columns = [str(c).lower().replace(" ", "_") for c in sub.columns]
            out[ticker] = sub
    else:
        # Single-ticker frame
        sub = df.copy()
        sub.columns = [str(c).lower().replace(" ", "_") for c in sub.columns]
        if len(tickers) == 1:
            out[tickers[0]] = sub

    return out


def _validate_ticker_frame(ticker: str, frame: pd.DataFrame) -> tuple[bool, str]:
    """Lightweight validation — full quality firewall lives in data_quality.py."""
    if frame is None or frame.empty:
        return False, "empty_frame"
    # yfinance returns 'adj close' which we lowercased to 'adj_close' already
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        return False, f"missing_columns:{','.join(missing)}"
    # Need at least *some* non-null closes
    if frame["close"].dropna().empty:
        return False, "all_close_nan"
    return True, "ok"


def _download_batch(
    tickers: list[str], start: str, end: str, attempt: int
) -> dict[str, pd.DataFrame]:
    """One yfinance batch download attempt."""
    logger.debug(f"Batch download: {len(tickers)} tickers (attempt {attempt})")
    df = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=True,
        group_by="column",
    )
    return _normalize_yf_frame(df, tickers)


def fetch_batch_with_retry(
    tickers: list[str], start: str, end: str
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """
    Returns (successful_frames, failed_reasons) for one batch.
    Retries the whole batch up to MAX_RETRIES times on exception.
    """
    last_error: str = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            frames = _download_batch(tickers, start, end, attempt)
            failed: dict[str, str] = {}
            ok: dict[str, pd.DataFrame] = {}
            for t in tickers:
                f = frames.get(t)
                valid, reason = _validate_ticker_frame(t, f)
                if valid:
                    ok[t] = f
                else:
                    failed[t] = reason
            return ok, failed
        except Exception as exc:  # noqa: BLE001 — yfinance can raise many types
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning(
                f"Batch attempt {attempt}/{MAX_RETRIES} failed: {last_error}"
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    # Total batch failure
    return {}, {t: f"batch_exception:{last_error}" for t in tickers}


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def fetch_all(
    tickers: list[str], lookback_days: int = LOOKBACK_DAYS
) -> tuple[pd.DataFrame, dict[str, str], dict[str, Any]]:
    """
    Fetch all tickers in batches.

    Returns
    -------
    long_df : pd.DataFrame
        Long-format frame with columns: ticker, date, open, high, low, close,
        adj_close, volume. Sorted by (ticker, date).
    failed : dict[str, str]
        ticker -> reason for failure.
    self_heal : dict
        {n_suspicious, n_healed, still_short} — truncated-fetch recovery stats.
    """
    end_dt = datetime.now(timezone.utc).date() + timedelta(days=1)
    start_dt = end_dt - timedelta(days=lookback_days)
    start = start_dt.isoformat()
    end = end_dt.isoformat()

    logger.info(
        f"Fetching {len(tickers)} tickers from {start} to {end} "
        f"in batches of {BATCH_SIZE}"
    )

    all_frames: dict[str, pd.DataFrame] = {}
    all_failed: dict[str, str] = {}

    n_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(tickers), BATCH_SIZE):
        batch_idx = i // BATCH_SIZE + 1
        batch = tickers[i : i + BATCH_SIZE]
        logger.info(f"  Batch {batch_idx}/{n_batches} ({len(batch)} tickers)")
        ok, failed = fetch_batch_with_retry(batch, start, end)
        all_frames.update(ok)
        all_failed.update(failed)
        logger.info(
            f"    -> {len(ok)} ok, {len(failed)} failed "
            f"(running total: {len(all_frames)} ok, {len(all_failed)} failed)"
        )

    # ---- Self-heal: re-fetch suspiciously-short (truncated) frames ---------
    # A frame that passed validation but carries < SUSPICIOUS_MIN_BARS bars
    # cannot produce 50/200d features and would silently drop from CCQS. Re-
    # fetch each individually and keep the fullest result. (See constant note.)
    def _bars(frame: pd.DataFrame | None) -> int:
        return 0 if frame is None else int(frame["close"].dropna().shape[0])

    suspicious = [t for t, f in all_frames.items() if _bars(f) < SUSPICIOUS_MIN_BARS]
    n_healed = 0
    if suspicious:
        logger.warning(
            f"Self-heal: {len(suspicious)} ticker(s) returned <{SUSPICIOUS_MIN_BARS} "
            f"bars; re-fetching individually to rule out truncation"
        )
        for t in suspicious:
            best, best_bars = all_frames.get(t), _bars(all_frames.get(t))
            for _ in range(REFETCH_MAX_ATTEMPTS):
                ok, _f = fetch_batch_with_retry([t], start, end)
                cand = ok.get(t)
                if _bars(cand) > best_bars:
                    best, best_bars = cand, _bars(cand)
                if best_bars >= SUSPICIOUS_MIN_BARS:
                    break
            if best is not None and best_bars > _bars(all_frames.get(t)):
                all_frames[t] = best
                n_healed += 1
        logger.info(
            f"Self-heal: recovered fuller history for {n_healed}/{len(suspicious)} "
            f"ticker(s); still-short are genuine recent IPOs"
        )
    still_short = sorted(t for t in suspicious if _bars(all_frames.get(t)) < SUSPICIOUS_MIN_BARS)
    self_heal = {"n_suspicious": len(suspicious), "n_healed": n_healed, "still_short": still_short}

    # Convert per-ticker frames to long format
    pieces: list[pd.DataFrame] = []
    for ticker, frame in all_frames.items():
        f = frame[REQUIRED_COLUMNS].copy()
        f.index = pd.to_datetime(f.index).tz_localize(None)
        f.index.name = "date"
        f = f.reset_index()
        f.insert(0, "ticker", ticker)
        pieces.append(f)

    if pieces:
        long_df = pd.concat(pieces, ignore_index=True)
        long_df = long_df.sort_values(["ticker", "date"]).reset_index(drop=True)
    else:
        long_df = pd.DataFrame(
            columns=["ticker", "date", *REQUIRED_COLUMNS]
        )

    return long_df, all_failed, self_heal


def write_outputs(
    long_df: pd.DataFrame,
    failed: dict[str, str],
    universe_size: int,
    benchmark_count: int,
    self_heal: dict[str, Any] | None = None,
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    long_df.to_parquet(OHLCV_PATH, index=False, compression="snappy")

    if long_df.empty:
        date_min = date_max = None
    else:
        date_min = long_df["date"].min().date().isoformat()
        date_max = long_df["date"].max().date().isoformat()

    meta: dict[str, Any] = {
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "universe_size": universe_size,
        "benchmark_count": benchmark_count,
        "n_loaded": int(long_df["ticker"].nunique()) if not long_df.empty else 0,
        "n_failed": len(failed),
        "self_heal": self_heal or {"n_suspicious": 0, "n_healed": 0, "still_short": []},
        "date_min": date_min,
        "date_max": date_max,
        "rows": int(len(long_df)),
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    FAILED_PATH.write_text(json.dumps(failed, indent=2, sort_keys=True))

    logger.info(f"Wrote {OHLCV_PATH} ({len(long_df):,} rows)")
    logger.info(f"Wrote {META_PATH}")
    logger.info(f"Wrote {FAILED_PATH} ({len(failed)} failed tickers)")


def load_cached_ohlcv() -> pd.DataFrame:
    """Public helper for downstream modules: read cached parquet."""
    if not OHLCV_PATH.exists():
        raise FileNotFoundError(
            f"OHLCV cache not found at {OHLCV_PATH}. Run `python -m compute.loader` first."
        )
    return pd.read_parquet(OHLCV_PATH)


def main(force: bool = False) -> int:
    universe = all_unique_tickers()
    full = universe + sorted(BENCHMARKS)

    if not force and _cache_is_fresh():
        meta = json.loads(META_PATH.read_text())
        logger.info(
            f"Cache fresh (pulled_at={meta['pulled_at']}, "
            f"n_loaded={meta['n_loaded']}). Use force=True to refresh."
        )
        return 0

    logger.info(
        f"Universe: {len(universe)} tickers + {len(BENCHMARKS)} benchmarks "
        f"= {len(full)} total"
    )

    t0 = time.time()
    long_df, failed, self_heal = fetch_all(full)
    elapsed = time.time() - t0

    n_loaded = int(long_df["ticker"].nunique()) if not long_df.empty else 0
    logger.info(
        f"Fetch complete in {elapsed:.1f}s — "
        f"{n_loaded}/{len(full)} ok, {len(failed)} failed"
    )

    if long_df.empty and OHLCV_PATH.exists():
        logger.error("Pull returned no data; keeping last-good cache.")
        return 1

    write_outputs(
        long_df=long_df,
        failed=failed,
        universe_size=len(universe),
        benchmark_count=len(BENCHMARKS),
        self_heal=self_heal,
    )
    if self_heal["n_suspicious"]:
        logger.info(
            f"Self-heal summary: {self_heal['n_healed']}/{self_heal['n_suspicious']} "
            f"recovered; {len(self_heal['still_short'])} genuinely short "
            f"(recent IPOs): {self_heal['still_short'][:10]}"
        )

    # Console summary
    print()
    print("=" * 60)
    print("LOADER SUMMARY")
    print("=" * 60)
    print(f"Tickers requested:  {len(full)} "
          f"({len(universe)} universe + {len(BENCHMARKS)} benchmarks)")
    print(f"Tickers loaded:     {n_loaded}")
    print(f"Tickers failed:     {len(failed)}")
    if not long_df.empty:
        print(f"Date range:         "
              f"{long_df['date'].min().date()} to {long_df['date'].max().date()}")
        print(f"Rows:               {len(long_df):,}")
    print(f"Elapsed:            {elapsed:.1f}s")
    print("=" * 60)

    if failed:
        sample = list(failed.items())[:10]
        print("Failed tickers (first 10):")
        for t, reason in sample:
            print(f"  {t:10s} -> {reason}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more (see {FAILED_PATH})")
        print()

    # Show last 5 closes for NVDA + benchmarks
    print()
    print("Last 5 closing prices:")
    print("-" * 60)
    for tkr in ["NVDA", "SPY", "QQQ"]:
        sub = long_df[long_df["ticker"] == tkr].tail(5)
        if sub.empty:
            print(f"{tkr}: <no data>")
            continue
        print(f"\n{tkr}:")
        for _, row in sub.iterrows():
            print(
                f"  {row['date'].date()}   "
                f"close={row['close']:>10.2f}   "
                f"adj_close={row['adj_close']:>10.2f}   "
                f"vol={int(row['volume']):>14,}"
            )
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
