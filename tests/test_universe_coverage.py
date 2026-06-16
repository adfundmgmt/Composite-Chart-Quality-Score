"""
Tests that the data pipeline successfully covers the entire universe.

Verifies:
  - Every ticker in `data.universe.all_unique_tickers()` is present in the
    OHLCV cache (or in the `failed_tickers.json` explicit-failure list).
  - The unrecovered failure rate is below an acceptable threshold (~3%).
  - Benchmarks SPY and QQQ are present and have current data.
  - Latest date in OHLCV cache is within 5 trading days of today (catches
    stale cache).
  - Data Quality firewall classifies > 90% of the universe as PASS+WARNING.

Run from repo root:
    pytest tests/test_universe_coverage.py -v --tb=short
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
OHLCV_PATH = CACHE_DIR / "ohlcv_daily.parquet"
CCQS_PATH = CACHE_DIR / "ccqs.parquet"
FAILED_TICKERS_PATH = CACHE_DIR / "failed_tickers.json"
DATA_QUALITY_PATH = CACHE_DIR / "data_quality_report.json"


# Thresholds — calibrated to the S&P 500-equivalent Path C universe
# (884 declared tickers, ~5% expected fail rate from delistings).
MAX_UNRECOVERED_FAILURE_RATE = 0.05   # 5% of universe (~44 tickers)
MIN_PASS_OR_WARNING_RATE = 0.90        # 90% must be PASS or WARNING
MAX_DAYS_STALE = 7                     # tolerate up to 7 calendar days (weekends + holidays)
MIN_SCORED_LATEST_DAY = 820            # min tickers with a CCQS on the latest date
MAX_COVERAGE_DROP_PCT = 4.0            # max acceptable day-over-day scored-count drop


@pytest.fixture(scope="module")
def universe():
    from data.universe import all_unique_tickers, BENCHMARKS
    return {
        "all": set(all_unique_tickers()),
        "benchmarks": set(BENCHMARKS),
    }


@pytest.fixture(scope="module")
def ohlcv_cache():
    """Load OHLCV cache; skip test module if cache absent (lets dev run
    tests without a full pipeline rebuild having happened locally)."""
    if not OHLCV_PATH.exists():
        pytest.skip(f"OHLCV cache not present at {OHLCV_PATH}")
    return pd.read_parquet(OHLCV_PATH)


@pytest.fixture(scope="module")
def ccqs_cache():
    """Load the CCQS panel (pipeline output). Skip if absent so devs can run
    coverage tests without a full local rebuild."""
    if not CCQS_PATH.exists():
        pytest.skip(f"CCQS cache not present at {CCQS_PATH}")
    return pd.read_parquet(CCQS_PATH)


@pytest.fixture(scope="module")
def failed_tickers():
    if not FAILED_TICKERS_PATH.exists():
        return {}
    return json.loads(FAILED_TICKERS_PATH.read_text())


@pytest.fixture(scope="module")
def data_quality_report():
    if not DATA_QUALITY_PATH.exists():
        pytest.skip(f"Data quality report not present at {DATA_QUALITY_PATH}")
    return json.loads(DATA_QUALITY_PATH.read_text())


# --------------------------------------------------------------------------
# Coverage tests
# --------------------------------------------------------------------------

def test_benchmarks_present(ohlcv_cache, universe):
    """SPY and QQQ MUST be in the OHLCV cache — pipeline depends on them."""
    cached_tickers = set(ohlcv_cache["ticker"].unique())
    missing = universe["benchmarks"] - cached_tickers
    assert not missing, f"Missing benchmarks: {missing}"


def test_universe_coverage_rate(ohlcv_cache, universe, failed_tickers):
    """Of the declared universe, only a small fraction is allowed to be
    missing from the OHLCV cache. `failed_tickers.json` is the explicit
    failure list — but any ticker that doesn't appear in EITHER the cache
    OR the failure list is an unrecovered / silent failure."""
    cached = set(ohlcv_cache["ticker"].unique())
    declared = universe["all"]
    explicit_failed = set(failed_tickers.keys()) if isinstance(failed_tickers, dict) else set(failed_tickers)
    silent_missing = declared - cached - explicit_failed
    total = len(declared)
    fail_rate = (len(declared - cached)) / max(total, 1)
    assert fail_rate <= MAX_UNRECOVERED_FAILURE_RATE, (
        f"Coverage too low: {fail_rate:.2%} missing from cache "
        f"(threshold {MAX_UNRECOVERED_FAILURE_RATE:.0%}). "
        f"Silent missing (not in failed_tickers.json): {sorted(silent_missing)[:20]}"
    )


def test_ohlcv_recency(ohlcv_cache):
    """Latest date in OHLCV cache must be within `MAX_DAYS_STALE` days
    of today (tolerates weekends + market holidays)."""
    latest = ohlcv_cache["date"].max()
    today = pd.Timestamp(datetime.now(tz=None).date())
    days_stale = (today - pd.Timestamp(latest)).days
    assert days_stale <= MAX_DAYS_STALE, (
        f"OHLCV cache stale: latest date {latest.date()}, "
        f"{days_stale} days behind today {today.date()} "
        f"(threshold {MAX_DAYS_STALE} days)"
    )


def test_no_critical_silent_failures(ohlcv_cache, universe, failed_tickers):
    """Any ticker missing from the cache MUST be listed in failed_tickers.json
    so we have an audit trail. Silent misses are a pipeline bug."""
    cached = set(ohlcv_cache["ticker"].unique())
    declared = universe["all"]
    explicit_failed = set(failed_tickers.keys()) if isinstance(failed_tickers, dict) else set(failed_tickers)
    silent_missing = declared - cached - explicit_failed
    # Allow up to 5 silent failures (rare yfinance flakiness); more than that
    # signals a systemic issue worth surfacing.
    assert len(silent_missing) <= 5, (
        f"{len(silent_missing)} silent failures — these tickers are "
        f"declared in the universe but not in OHLCV cache OR failed_tickers.json: "
        f"{sorted(silent_missing)[:20]}"
    )


# --------------------------------------------------------------------------
# Scored-coverage tests — presence in OHLCV is NOT enough. A truncated frame
# (too few bars for 50/200d features) IS present in the cache but silently
# fails to produce a CCQS. These assert *sufficiency*, on the latest date, and
# block the commit on a single-day collapse (the 2026-06-15 regression).
# --------------------------------------------------------------------------

def test_latest_day_scored_coverage(ccqs_cache):
    """The most recent date must have ≥ MIN_SCORED_LATEST_DAY tickers with a
    non-NaN CCQS. Catches batches of truncated frames that are present in OHLCV
    but lack the history to be scored."""
    dates = sorted(ccqs_cache.index.get_level_values("date").unique())
    d_last = dates[-1]
    scored = int(ccqs_cache.xs(d_last, level="date")["ccqs"].notna().sum())
    assert scored >= MIN_SCORED_LATEST_DAY, (
        f"Only {scored} tickers scored on latest date {d_last.date()} "
        f"(threshold {MIN_SCORED_LATEST_DAY}). A truncated-fetch batch likely "
        f"dropped names from CCQS — check loader self-heal / ohlcv_meta self_heal stats."
    )


def test_scored_coverage_no_daily_collapse(ccqs_cache):
    """Scored-ticker count must not fall > MAX_COVERAGE_DROP_PCT day-over-day.
    This is the gate that the 30-day-window check #11 in sanity_checks misses."""
    dates = sorted(ccqs_cache.index.get_level_values("date").unique())
    if len(dates) < 2:
        pytest.skip("need ≥2 dates")
    cur = int(ccqs_cache.xs(dates[-1], level="date")["ccqs"].notna().sum())
    prev = int(ccqs_cache.xs(dates[-2], level="date")["ccqs"].notna().sum())
    drop_pct = (prev - cur) / prev * 100.0 if prev else 0.0
    assert drop_pct <= MAX_COVERAGE_DROP_PCT, (
        f"Scored coverage collapsed {drop_pct:.1f}% in one day "
        f"({prev} on {dates[-2].date()} → {cur} on {dates[-1].date()}; "
        f"threshold {MAX_COVERAGE_DROP_PCT}%). Likely a truncated-fetch regression."
    )


# --------------------------------------------------------------------------
# Data quality firewall tests
# --------------------------------------------------------------------------

def test_data_quality_pass_warning_rate(data_quality_report):
    """≥ MIN_PASS_OR_WARNING_RATE of cached tickers must pass the firewall."""
    results = data_quality_report.get("results", {})
    total = len(results)
    pass_warn = sum(
        1 for r in results.values()
        if r.get("status") in ("PASS", "WARNING")
    )
    rate = pass_warn / max(total, 1)
    assert rate >= MIN_PASS_OR_WARNING_RATE, (
        f"Data quality pass/warn rate too low: {rate:.2%} "
        f"(threshold {MIN_PASS_OR_WARNING_RATE:.0%}); "
        f"FAIL count: {total - pass_warn}/{total}"
    )


def test_benchmarks_pass_data_quality(data_quality_report):
    """SPY and QQQ must PASS the firewall (not WARNING) — they are the
    canonical price references for cross-sectional RS computation."""
    from data.universe import BENCHMARKS
    results = data_quality_report.get("results", {})
    for b in BENCHMARKS:
        if b not in results:
            pytest.fail(f"Benchmark {b} missing from data quality report")
        status = results[b].get("status")
        assert status == "PASS", (
            f"Benchmark {b} status is {status}, expected PASS"
        )
