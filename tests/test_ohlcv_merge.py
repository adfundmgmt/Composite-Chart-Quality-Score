"""Regression tests for the last-good OHLCV union merge (coverage stability).

Guards the fix where a fresh yfinance frame with >= SUSPICIOUS_MIN_BARS *total*
bars but a SPARSE RECENT window (a long tail + a lone recent stub) used to be
taken as-is, so lookback features couldn't compute and CCQS nulled out — silently
dropping thin foreign ADRs from coverage (835 vs the healthy 858).
"""
import pandas as pd

from compute import loader


def _frame(ticker, dates, close):
    return pd.DataFrame({"ticker": ticker, "date": pd.to_datetime(list(dates)), "close": float(close)})


def test_union_backfills_sparse_recent_window(tmp_path, monkeypatch):
    # last-good cache: complete daily history through the prior trading day
    cached = _frame("NTDOY", pd.date_range("2026-04-01", "2026-06-22", freq="D"), 1.0)
    seed = tmp_path / "ohlcv_daily.parquet"
    cached.to_parquet(seed)
    monkeypatch.setattr(loader, "OHLCV_PATH", seed)

    # fresh fetch: long tail (passes the old bar-count gate) + only a lone recent stub
    fresh_dates = list(pd.date_range("2019-01-01", "2026-05-15", freq="D")) + [pd.Timestamp("2026-06-23")]
    fresh = _frame("NTDOY", fresh_dates, 2.0)
    assert len(fresh) >= loader.SUSPICIOUS_MIN_BARS, "fixture must clear the total-bar gate"

    merged, recovered = loader.merge_with_last_good(fresh, {})
    m = merged[merged["ticker"] == "NTDOY"]
    present = set(m["date"])

    # the recent window must be continuous through the fresh stub (gap filled from cache)
    for d in pd.date_range("2026-05-16", "2026-06-23", freq="D"):
        assert d in present, f"union should backfill {d.date()} from last-good cache"
    assert m["date"].max() == pd.Timestamp("2026-06-23")
    assert "NTDOY" in recovered, "cache-assisted ticker should be flagged as recovered"


def test_healthy_fresh_is_unchanged(tmp_path, monkeypatch):
    # a full continuous fresh frame: cache is a date-subset -> union == fresh, nothing lost
    cached = _frame("AAPL", pd.date_range("2026-05-01", "2026-06-22", freq="D"), 1.0)
    seed = tmp_path / "ohlcv_daily.parquet"
    cached.to_parquet(seed)
    monkeypatch.setattr(loader, "OHLCV_PATH", seed)

    fresh = _frame("AAPL", pd.date_range("2019-01-01", "2026-06-23", freq="D"), 2.0)
    merged, _ = loader.merge_with_last_good(fresh, {})
    m = merged[merged["ticker"] == "AAPL"]

    assert len(m) == len(fresh), "healthy fresh must not gain or lose rows"
    assert m["date"].max() == pd.Timestamp("2026-06-23")
    # fresh wins on any overlapping date
    assert (m.loc[m["date"] == pd.Timestamp("2026-06-01"), "close"] == 2.0).all()


def test_failed_fresh_keeps_cached(tmp_path, monkeypatch):
    # ticker absent from the fresh fetch entirely -> keep cached history rather than vanish
    cached = _frame("RHHBY", pd.date_range("2026-04-01", "2026-06-22", freq="D"), 1.0)
    seed = tmp_path / "ohlcv_daily.parquet"
    cached.to_parquet(seed)
    monkeypatch.setattr(loader, "OHLCV_PATH", seed)

    fresh = _frame("AAPL", pd.date_range("2026-04-01", "2026-06-23", freq="D"), 2.0)  # no RHHBY
    merged, _ = loader.merge_with_last_good(fresh, {})
    assert "RHHBY" in set(merged["ticker"]), "failed fetch should fall back to cached history"
