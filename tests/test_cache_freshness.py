"""
Tests that all dashboard caches are present, up-to-date, and consistent.

Verifies:
  - All required dashboard cache files exist.
  - Cache files are non-empty.
  - Latest date in dashboard caches is within 5 trading days of today.
  - Slim cache columns include the expected component / display columns.

Run from repo root:
    pytest tests/test_cache_freshness.py -v --tb=short
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = PROJECT_ROOT / "data" / "cache" / "dashboard"


REQUIRED_PARQUETS = [
    "ccqs.parquet",
    "state.parquet",
    "leadership.parquet",
    "setups.parquet",
    "features.parquet",
    "components.parquet",
    "theme_aggregates.parquet",
    "benchmarks.parquet",
]

REQUIRED_JSONS = [
    "anomalies.json",
    "oos_ic_summary.json",
    "sanity_checks.json",
    "regime_context.json",
]


@pytest.mark.parametrize("filename", REQUIRED_PARQUETS + REQUIRED_JSONS)
def test_dashboard_file_present(filename):
    p = DASHBOARD_DIR / filename
    assert p.exists(), f"Missing dashboard file: {p}"


@pytest.mark.parametrize("filename", REQUIRED_PARQUETS)
def test_dashboard_parquet_non_empty(filename):
    p = DASHBOARD_DIR / filename
    if not p.exists():
        pytest.skip(f"File {p} not present (covered by presence test)")
    df = pd.read_parquet(p)
    assert len(df) > 0, f"Dashboard parquet {filename} is empty"


@pytest.mark.parametrize("filename", REQUIRED_JSONS)
def test_dashboard_json_non_empty(filename):
    p = DASHBOARD_DIR / filename
    if not p.exists():
        pytest.skip(f"File {p} not present (covered by presence test)")
    content = json.loads(p.read_text())
    assert content, f"Dashboard JSON {filename} is empty/None/{{}}"


def test_ccqs_latest_date_recent():
    """The latest date in dashboard CCQS must be within 7 calendar days
    (covers weekends + major holidays without alerting falsely)."""
    p = DASHBOARD_DIR / "ccqs.parquet"
    if not p.exists():
        pytest.skip(f"File {p} not present")
    df = pd.read_parquet(p)
    latest = df.index.get_level_values("date").max()
    today = pd.Timestamp(datetime.now(tz=None).date())
    days_stale = (today - pd.Timestamp(latest)).days
    assert days_stale <= 7, (
        f"Dashboard CCQS cache stale: latest {latest.date()} "
        f"({days_stale} days behind today {today.date()})"
    )


def test_components_includes_all_10_columns():
    """Phase 28: s_demand permanently removed (had weight 0.0 in every
    state since Phase 7). Schema is 10 components, not 11."""
    p = DASHBOARD_DIR / "components.parquet"
    if not p.exists():
        pytest.skip(f"File {p} not present")
    df = pd.read_parquet(p)
    expected = {
        "s_rs", "s_rs_leadership", "s_residual_momentum",
        "s_rsl", "s_trend_slope", "s_structure",
        "s_mtf", "s_extension", "s_momentum",
        "s_volume",
    }
    missing = expected - set(df.columns)
    assert not missing, f"Dashboard components.parquet missing columns: {missing}"


def test_dashboard_cache_size_reasonable():
    """Total dashboard cache size should be within expected bounds for the
    Path C 884-ticker universe (~22 MB). Smaller suggests truncated data;
    larger suggests universe expansion artifacts."""
    sizes = {p.name: p.stat().st_size for p in DASHBOARD_DIR.iterdir() if p.is_file()}
    total_mb = sum(sizes.values()) / (1024 * 1024)
    assert 15.0 <= total_mb <= 40.0, (
        f"Dashboard cache total size {total_mb:.1f} MB outside expected "
        f"15-40 MB range. Sizes: {sizes}"
    )


def test_regime_context_current():
    p = DASHBOARD_DIR / "regime_context.json"
    if not p.exists():
        pytest.skip(f"File {p} not present")
    ctx = json.loads(p.read_text())
    assert "dvol_quintile_by_ticker" in ctx, "regime_context missing dvol_quintile_by_ticker"
    assert "market_vol" in ctx, "regime_context missing market_vol"
    assert "current_regime" in ctx["market_vol"], "market_vol missing current_regime"
    # Builder emits LOW / MID / HIGH (see compute/build_dashboard_cache.py
    # _market_vol_thresholds). The middle tercile is "MID", not "MED" — this
    # test previously allowed only "MED", a latent typo exposed on 2026-06-05
    # when the vol regime first landed in the middle tercile in production.
    assert ctx["market_vol"]["current_regime"] in ("LOW", "MID", "HIGH"), (
        f"Invalid market_vol regime: {ctx['market_vol']['current_regime']}"
    )


def test_sanity_checks_all_pass():
    p = DASHBOARD_DIR / "sanity_checks.json"
    if not p.exists():
        pytest.skip(f"File {p} not present")
    report = json.loads(p.read_text())
    n_checks = report.get("n_checks", 0)
    n_failed = report.get("n_failed", 0)
    all_passed = report.get("passed", False)
    failed_names = [c["name"] for c in report.get("checks", []) if not c.get("passed", False)]
    assert n_checks == 12, f"Expected 12 sanity checks, found {n_checks}"
    assert n_failed == 0, f"{n_failed} sanity checks failed: {failed_names}"
    assert all_passed, f"Sanity checks flag passed=False; failed: {failed_names}"
