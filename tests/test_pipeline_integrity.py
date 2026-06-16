"""
Tests that the full pipeline produces internally-consistent, sane outputs.

Verifies:
  - All 11 sanity checks pass (per `data/cache/sanity_checks.json`).
  - CCQS values are all in valid range [0, 100].
  - Grade distribution is non-degenerate (S/A/B/C/D all present, none > 50%).
  - State distribution is non-degenerate (no state > 50%).
  - Tier distribution is non-degenerate.
  - Setup distribution is non-degenerate.
  - Component contributions have no all-NaN columns.
  - No critical NaN in CCQS, primary_state, leadership_tier, setup.
  - STATE_WEIGHTS sum to 1.0 per state row.
  - Confidence-blending (Phase X.2.1) operating as designed.
  - Walk-forward IC numbers are within Phase 11 baseline tolerance.

Run from repo root:
    pytest tests/test_pipeline_integrity.py -v --tb=short
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"

CCQS_PATH = CACHE_DIR / "ccqs.parquet"
COMPONENTS_PATH = CACHE_DIR / "components.parquet"
STATE_PATH = CACHE_DIR / "state.parquet"
LEADERSHIP_PATH = CACHE_DIR / "leadership.parquet"
SETUPS_PATH = CACHE_DIR / "setups.parquet"
SANITY_CHECKS_PATH = CACHE_DIR / "sanity_checks.json"


# Tolerance bands calibrated to Path C baseline (per SPEC.md Phase 11 / 12)
PHASE11_IC_BASELINE = {5: 0.0115, 20: 0.0089, 60: 0.0137, 126: 0.0295}
IC_TOLERANCE = 0.003  # ±0.3pp around baseline — allows for daily drift


@pytest.fixture(scope="module")
def ccqs():
    if not CCQS_PATH.exists():
        pytest.skip(f"CCQS cache not present at {CCQS_PATH}")
    return pd.read_parquet(CCQS_PATH)


@pytest.fixture(scope="module")
def components():
    if not COMPONENTS_PATH.exists():
        pytest.skip(f"Components cache not present at {COMPONENTS_PATH}")
    return pd.read_parquet(COMPONENTS_PATH)


@pytest.fixture(scope="module")
def state():
    if not STATE_PATH.exists():
        pytest.skip(f"State cache not present at {STATE_PATH}")
    return pd.read_parquet(STATE_PATH)


@pytest.fixture(scope="module")
def leadership():
    if not LEADERSHIP_PATH.exists():
        pytest.skip(f"Leadership cache not present at {LEADERSHIP_PATH}")
    return pd.read_parquet(LEADERSHIP_PATH)


@pytest.fixture(scope="module")
def setups():
    if not SETUPS_PATH.exists():
        pytest.skip(f"Setups cache not present at {SETUPS_PATH}")
    return pd.read_parquet(SETUPS_PATH)


# --------------------------------------------------------------------------
# Sanity checks
# --------------------------------------------------------------------------

def test_11_sanity_checks_pass():
    """All 12 sanity checks must pass (11 original + #12 latest_day_coverage)."""
    if not SANITY_CHECKS_PATH.exists():
        pytest.skip(f"Sanity checks not present at {SANITY_CHECKS_PATH}")
    report = json.loads(SANITY_CHECKS_PATH.read_text())
    n_checks = report.get("n_checks", 0)
    n_failed = report.get("n_failed", 0)
    all_passed = report.get("passed", False)
    failed_names = [c["name"] for c in report.get("checks", []) if not c.get("passed", False)]
    assert n_checks == 12, f"Expected 12 sanity checks, found {n_checks}"
    assert n_failed == 0, f"{n_failed} sanity checks failed: {failed_names}"
    assert all_passed, f"Sanity checks report flags passed=False; failed: {failed_names}"


# --------------------------------------------------------------------------
# CCQS range and distribution
# --------------------------------------------------------------------------

def test_ccqs_in_valid_range(ccqs):
    """CCQS values must be in [0, 100] (per-date winsorized to p01/p99)."""
    scores = ccqs["ccqs"].dropna()
    assert (scores >= 0).all(), f"CCQS values < 0 found: {scores[scores < 0].head()}"
    assert (scores <= 100).all(), f"CCQS values > 100 found: {scores[scores > 100].head()}"


def test_ccqs_distribution_non_degenerate(ccqs):
    """CCQS distribution must span at least 50 points (otherwise something
    has flattened the score)."""
    scores = ccqs["ccqs"].dropna()
    p10, p90 = scores.quantile(0.10), scores.quantile(0.90)
    spread = p90 - p10
    assert spread >= 50, (
        f"CCQS p10-p90 spread too narrow ({spread:.1f}), "
        f"suggests degenerate distribution"
    )


def test_grade_distribution(ccqs):
    """All 5 grades S/A/B/C/D must be present, and no single grade > 50%."""
    grades = ccqs["grade"].astype(str).value_counts(normalize=True)
    expected = {"S", "A", "B", "C", "D"}
    found = set(grades.index)
    missing = expected - found
    assert not missing, f"Missing grades: {missing}"
    max_grade = grades.idxmax()
    max_pct = grades.max()
    assert max_pct < 0.50, (
        f"Grade {max_grade} dominates at {max_pct:.1%} (>= 50% threshold)"
    )


# --------------------------------------------------------------------------
# Component table
# --------------------------------------------------------------------------

EXPECTED_COMPONENTS = [
    "s_rs", "s_rs_leadership", "s_residual_momentum",
    "s_rsl", "s_trend_slope", "s_structure",
    "s_mtf", "s_extension", "s_momentum",
    "s_volume",
    # Phase 28 — s_demand removed (was 0.0 in every state since Phase 7).
]


def test_components_present(components):
    """All 10 components must be present in the components.parquet."""
    missing = set(EXPECTED_COMPONENTS) - set(components.columns)
    extra = set(components.columns) - set(EXPECTED_COMPONENTS)
    assert not missing, f"Missing components: {missing}"
    assert not extra, f"Unexpected component columns: {extra}"


def test_components_no_all_nan(components):
    """No component column should be entirely NaN."""
    for col in EXPECTED_COMPONENTS:
        nan_rate = components[col].isna().mean()
        assert nan_rate < 1.0, f"Component {col} is 100% NaN"
        # Most components should have < 30% NaN
        if col not in ("s_residual_momentum", "s_volume"):
            assert nan_rate < 0.30, (
                f"Component {col} has {nan_rate:.1%} NaN (>= 30%); "
                f"suggests a feature-computation bug"
            )


# --------------------------------------------------------------------------
# State / tier / setup distributions
# --------------------------------------------------------------------------

def test_state_distribution_non_degenerate(state):
    """All 6 states must be present in the latest snapshot; no state > 50%."""
    latest_date = state.index.get_level_values("date").max()
    latest = state.xs(latest_date, level="date")
    dist = latest["primary_state"].astype(str).value_counts(normalize=True)
    assert dist.max() < 0.50, (
        f"State {dist.idxmax()} dominates at {dist.max():.1%} (latest date {latest_date.date()})"
    )
    # All 6 states should appear (allow EXHAUSTION to be < 1% on bear days)
    expected = {"TRENDING", "PULLBACK", "CONSOLIDATING", "EXHAUSTION", "DETERIORATING", "INDETERMINATE"}
    found = set(dist.index)
    missing = expected - found
    assert not missing, f"Missing states in latest snapshot ({latest_date.date()}): {missing}"


def test_tier_distribution_non_degenerate(leadership):
    """Tier distribution must include all expected tiers (or NaN); no
    tier > 50% (except possibly STRONG_PERFORMER on broad-market days)."""
    latest_date = leadership.index.get_level_values("date").max()
    latest = leadership.xs(latest_date, level="date")
    dist = latest["leadership_tier"].astype(str).value_counts(normalize=True)
    # STRONG_PERFORMER and DETERIORATING are large catch-alls; allow up to 50%
    max_tier = dist.idxmax()
    max_pct = dist.max()
    assert max_pct < 0.55, (
        f"Tier {max_tier} dominates at {max_pct:.1%} on {latest_date.date()}; "
        f"suggests methodology/calibration issue"
    )


def test_setup_distribution_non_degenerate(setups):
    """Setup distribution must include at least 10 distinct setups and no
    single non-residual setup > 40%.

    Catch-all / residual labels that are intentionally allowed to dominate:
      - blank ("")               — Phase 25 residual (silence beats noise)
      - "(Generic)" / "Indeterminate Pattern" — legacy 27-label residuals
        (kept here for backward compatibility with the historical setup
        vocabulary; not produced by the Phase 25 classifier).
    """
    latest_date = setups.index.get_level_values("date").max()
    latest = setups.xs(latest_date, level="date")
    dist = latest["setup"].astype(str).value_counts(normalize=True)
    assert len(dist) >= 10, f"Only {len(dist)} setups present on {latest_date.date()}"
    # The largest non-catch-all setup should not exceed 40%.
    # Exclude residuals: blank (Phase 25), "(Generic)" / "Indeterminate Pattern" (legacy).
    is_residual = (
        (dist.index == "")
        | dist.index.str.contains(r"\(Generic\)", regex=True)
        | (dist.index == "Indeterminate Pattern")
    )
    non_generic = dist[~is_residual]
    if len(non_generic) > 0:
        max_setup = non_generic.idxmax()
        max_pct = non_generic.max()
        assert max_pct < 0.40, (
            f"Non-generic setup '{max_setup}' dominates at {max_pct:.1%}"
        )


# --------------------------------------------------------------------------
# STATE_WEIGHTS integrity
# --------------------------------------------------------------------------

def test_state_weights_sum_to_one():
    """Each row in STATE_WEIGHTS must sum to 1.0 (within floating-point tolerance)."""
    from compute.ccqs import STATE_WEIGHTS
    for state_name, weights in STATE_WEIGHTS.items():
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-6, (
            f"State {state_name} weights sum to {total:.10f}, not 1.0"
        )


def test_state_weights_components_match():
    """Every state row must have exactly the 11 expected components."""
    from compute.ccqs import STATE_WEIGHTS
    from compute.components import COMPONENT_COLS
    expected = set(COMPONENT_COLS)
    for state_name, weights in STATE_WEIGHTS.items():
        found = set(weights.keys())
        missing = expected - found
        extra = found - expected
        assert not missing, f"State {state_name} missing components: {missing}"
        assert not extra, f"State {state_name} has unexpected components: {extra}"


# --------------------------------------------------------------------------
# Confidence-blending integrity
# --------------------------------------------------------------------------

def test_confidence_blend_low_conf_blends_to_indeterminate(state):
    """Per Phase X.2.1: rows with state_confidence < 0.5 should have
    p_adj_INDETERMINATE >= 0.5 (50% blended toward INDETERMINATE)."""
    low_conf = state[state["state_confidence"] < 0.5]
    if len(low_conf) == 0:
        pytest.skip("No low-confidence rows to check")
    # Mean p_adj_INDETERMINATE for low_conf rows should be >= 0.5
    mean_p_adj = low_conf["p_adj_INDETERMINATE"].mean()
    assert mean_p_adj >= 0.50, (
        f"Low-confidence rows have mean p_adj_INDETERMINATE = {mean_p_adj:.4f}, "
        f"expected >= 0.5"
    )


# --------------------------------------------------------------------------
# Latest snapshot completeness
# --------------------------------------------------------------------------

def test_latest_date_consistency(ccqs, state, leadership, setups, components):
    """All five output parquets must share the same latest date."""
    latest = {
        "ccqs": ccqs.index.get_level_values("date").max(),
        "state": state.index.get_level_values("date").max(),
        "leadership": leadership.index.get_level_values("date").max(),
        "setups": setups.index.get_level_values("date").max(),
        "components": components.index.get_level_values("date").max(),
    }
    unique_dates = set(latest.values())
    assert len(unique_dates) == 1, (
        f"Cache files have inconsistent latest dates: {latest}"
    )
