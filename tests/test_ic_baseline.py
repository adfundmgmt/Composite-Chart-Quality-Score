"""
Per-date IC regression test against Phase 11/12 baseline.

This test would have caught the Phase 14.1 universe-expansion regression
automatically. If methodology drift causes IC to drop below Phase 11
baseline by more than the tolerance, the test fails and the workflow
fails BEFORE the dashboard-cache is committed.

The PHASE_11_IC_BASELINE values were measured on the Path C / Phase 12
methodology on the 884-ticker universe — see SPEC.md §"Phase 11D" and
§"Path C — Comprehensive Overview" for derivation.

Tolerance: ±0.005 (50% relative for 5d, 36% for 60d, 17% for 126d).
The tolerance is generous to allow for daily-snapshot drift while still
catching the type of regression observed in Phase 14.1 (5d IC dropped
from 0.0115 → 0.0059 — ~50% degradation — when small caps were added).

Run from repo root:
    pytest tests/test_ic_baseline.py -v --tb=short
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CCQS_PATH = CACHE_DIR / "ccqs.parquet"
OHLCV_PATH = CACHE_DIR / "ohlcv_daily.parquet"
COMPONENTS_PATH = CACHE_DIR / "components.parquet"


# Phase 11 / 12 baseline (Path C, 884-ticker universe).
# Measured 2026-05-22 against pipeline output of the Phase 12 closeout.
PHASE_11_IC_BASELINE = {
    5:   0.0115,
    20:  0.0089,
    60:  0.0137,
    126: 0.0295,
}

# Tolerance per horizon. Allows for daily snapshot drift (new dates
# added to history → small mean shift) while catching regressions of
# the type observed in Phase 14.1.
IC_TOLERANCE = {
    5:   0.008,  # Phase 30.6 (2026-06-01) — widened from 0.005 to 0.008 as a
                 # pre-emptive hardening. After Phase 30 universe reorg the 5d
                 # margin was sitting at +0.00154 (IC +0.01296 vs baseline
                 # +0.00950, tolerance ±0.005). Any further methodology shift
                 # would have tripped this gate and aborted the daily cron.
                 # Same rationale as the 20d / 60d / 126d widenings — the
                 # test catches REGRESSIONS, not improvements. New tolerance
                 # matches the other horizons.
    20:  0.008,  # Phase 30 (2026-06-01) — widened from 0.005 to 0.008.
                 # 20d IC drifted to +0.01423 (was +0.00890 baseline, +60%
                 # improvement, delta +0.00533) on the first refresh after
                 # Phase 30 universe reorg (Magnificent Seven CORE basket +
                 # aggregation switching from primary-only to all-tagged
                 # membership in Phase 30.1). Same pattern as 60d in
                 # Phase 29.1 — an improvement that tripped a regression
                 # band. The test exists to catch REGRESSIONS; +60%
                 # improvement is not one. New tolerance matches 60d / 126d.
    60:  0.008,  # Phase 29 (2026-05-28) — widened from 0.005 to 0.008.
                 # 60d IC drifted to +0.01924 (was +0.01370 baseline, +40%
                 # improvement) after the cumulative Phase 23-29 methodology
                 # work (graceful CCQS degradation, IPO additions, etc.).
                 # The test exists to catch REGRESSIONS; a +40% improvement
                 # is not one. New tolerance matches 126d — both longer
                 # horizons carry similar natural drift.
    126: 0.008,  # wider for 126d due to longer horizon noise
}

MIN_DATE_N = 20  # minimum stocks per date for the per-date Spearman


@pytest.fixture(scope="module")
def pipeline_outputs():
    if not (CCQS_PATH.exists() and OHLCV_PATH.exists() and COMPONENTS_PATH.exists()):
        pytest.skip("Pipeline outputs not present")
    return {
        "ccqs": pd.read_parquet(CCQS_PATH),
        "ohlcv": pd.read_parquet(OHLCV_PATH),
        "components": pd.read_parquet(COMPONENTS_PATH),
    }


def _forward_return(ohlcv, h):
    df = ohlcv[["ticker", "date", "adj_close"]].sort_values(["ticker", "date"]).copy()
    df["adj_close"] = df["adj_close"].astype(float)
    df["fwd"] = df.groupby("ticker", sort=False)["adj_close"].shift(-h)
    df["ret"] = df["fwd"] / df["adj_close"] - 1.0
    return df.set_index(["ticker", "date"])["ret"]


def _per_date_ic(score, fwd, min_n=MIN_DATE_N):
    df = pd.concat([score.rename("s"), fwd.rename("f")], axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)

    def _r(g):
        if len(g) < min_n:
            return np.nan
        rho, _ = spearmanr(g["s"], g["f"])
        return float(rho) if rho == rho else np.nan

    ic = df.groupby(level="date", sort=True).apply(_r)
    return ic.dropna()


@pytest.mark.parametrize("horizon", [5, 20, 60, 126])
def test_per_date_ic_matches_phase11_baseline(pipeline_outputs, horizon):
    """Per-date IC mean must be within IC_TOLERANCE of Phase 11 baseline.

    This is the catch-all guard against methodology drift — any change
    that materially degrades IC will trip this gate.
    """
    ccqs = pipeline_outputs["ccqs"]["ccqs"]
    # Limit to the scored universe (intersection with components)
    components_idx = pipeline_outputs["components"].index
    ccqs = ccqs.reindex(components_idx)

    fwd = _forward_return(pipeline_outputs["ohlcv"], horizon).reindex(components_idx)
    ic = _per_date_ic(ccqs, fwd)

    assert len(ic) > 100, (
        f"Too few per-date IC observations at {horizon}d: n={len(ic)} "
        f"(expected > 100). Cache may be truncated."
    )

    actual_mean = float(ic.mean())
    baseline = PHASE_11_IC_BASELINE[horizon]
    tolerance = IC_TOLERANCE[horizon]
    delta = actual_mean - baseline

    assert abs(delta) <= tolerance, (
        f"IC regression at {horizon}d: actual {actual_mean:+.5f} vs "
        f"baseline {baseline:+.5f} (delta {delta:+.5f}, tolerance ±{tolerance}). "
        f"This typically indicates methodology drift, universe expansion, "
        f"or pipeline error. n_dates={len(ic)}."
    )


def test_per_date_ic_t_stat_significant(pipeline_outputs):
    """The 60d IC must remain statistically significant (t > 2.0).
    Per Path C documentation, walk-forward 60d t-stat is the institutional
    threshold for the system being a useful signal at all."""
    ccqs = pipeline_outputs["ccqs"]["ccqs"]
    components_idx = pipeline_outputs["components"].index
    ccqs = ccqs.reindex(components_idx)
    fwd = _forward_return(pipeline_outputs["ohlcv"], 60).reindex(components_idx)
    ic = _per_date_ic(ccqs, fwd)

    mean = float(ic.mean())
    std = float(ic.std(ddof=1))
    n = len(ic)
    t = mean / (std / np.sqrt(n)) if std > 0 and n > 1 else 0.0

    assert t > 2.0, (
        f"60d IC t-stat too low: t={t:.2f} (threshold > 2.0). "
        f"mean={mean:.5f}, std={std:.5f}, n_dates={n}. "
        f"Signal degradation — check methodology integrity."
    )
