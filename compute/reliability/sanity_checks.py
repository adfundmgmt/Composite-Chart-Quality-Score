"""
CCQS V1 — Deterministic Sanity Checks (SPEC Section 13, Layer 4)

11 deterministic assertions over the pipeline outputs. Run after a full
pipeline build. Any FAILED assertion is a regression: investigate before
publishing the day's results.

Output: `data/cache/sanity_checks.json` with one entry per assertion:
    {
      "id": int, "name": str,
      "passed": bool,
      "value": <observed>,
      "expected": <human description>,
      "detail": <optional extra info>
    }
A non-zero CLI exit code is returned if any assertion fails.

Run:
    python -m compute.reliability.sanity_checks
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from compute.loader import CACHE_DIR, LOG_DIR

CCQS_PATH = CACHE_DIR / "ccqs.parquet"
COMPONENTS_PATH = CACHE_DIR / "components.parquet"
STATE_PATH = CACHE_DIR / "state.parquet"
LEADERSHIP_PATH = CACHE_DIR / "leadership.parquet"
SETUP_PATH = CACHE_DIR / "setups.parquet"
THEME_PATH = CACHE_DIR / "theme_aggregates.parquet"
FEATURES_PATH = CACHE_DIR / "features.parquet"

OUT_PATH = CACHE_DIR / "sanity_checks.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(sys.stdout, level="INFO", format="<level>{level: <8}</level> | {message}")
logger.add(LOG_DIR / "ccqs.log", level="DEBUG", rotation="10 MB", retention="30 days")


def _check(passed: bool, name: str, observed, expected: str, detail: str = "") -> dict:
    return {
        "name": name,
        "passed": bool(passed),
        "observed": observed,
        "expected": expected,
        "detail": detail,
    }


def run_sanity_checks() -> dict:
    """Run all 11 sanity checks. Returns a dict with `passed: bool` + `checks: list`."""
    ccqs = pd.read_parquet(CCQS_PATH)
    components = pd.read_parquet(COMPONENTS_PATH)
    state = pd.read_parquet(STATE_PATH)
    leadership = pd.read_parquet(LEADERSHIP_PATH)
    setups = pd.read_parquet(SETUP_PATH)
    theme = pd.read_parquet(THEME_PATH) if THEME_PATH.exists() else None
    features = pd.read_parquet(FEATURES_PATH)

    checks: list[dict] = []

    # 1. CCQS in [0, 100] excluding NaN.
    q = ccqs["ccqs"].dropna()
    n_oob = int(((q < 0) | (q > 100)).sum())
    checks.append(
        _check(
            n_oob == 0,
            "ccqs_in_0_100",
            f"{n_oob} out-of-range",
            "0 rows where ccqs is outside [0,100]",
        )
    )

    # 2. State probabilities sum ≈ 1.
    pcols = ["p_TRENDING", "p_PULLBACK", "p_CONSOLIDATING", "p_EXHAUSTION", "p_DETERIORATING", "p_INDETERMINATE"]
    sums = state[pcols].sum(axis=1).dropna()
    bad = int(((sums - 1.0).abs() > 1e-3).sum())
    checks.append(
        _check(bad == 0, "state_probs_sum_to_1", f"{bad} rows", "0 rows where Σp != 1.0 ±1e-3")
    )

    # 3. State p_adj sum ≈ 1.
    p_adj_cols = [f"p_adj_{s.upper()}" for s in ["TRENDING", "PULLBACK", "CONSOLIDATING", "EXHAUSTION", "DETERIORATING", "INDETERMINATE"]]
    sums = state[p_adj_cols].sum(axis=1).dropna()
    bad = int(((sums - 1.0).abs() > 1e-3).sum())
    checks.append(
        _check(bad == 0, "state_p_adj_sum_to_1", f"{bad} rows", "0 rows where Σp_adj != 1.0 ±1e-3")
    )

    # 4. No inf in components.
    comp_num = components.select_dtypes(include=[np.number])
    has_inf = bool(np.isinf(comp_num.to_numpy()).any())
    checks.append(
        _check(not has_inf, "no_inf_components", str(has_inf), "no ±inf in components")
    )

    # 5. Grade distribution: 2% ≤ S ≤ 15%.
    grade_dist = ccqs["grade"].astype(str).value_counts(normalize=True)
    s_pct = float(grade_dist.get("S", 0.0)) * 100.0
    checks.append(
        _check(
            2.0 <= s_pct <= 15.0,
            "grade_s_pct_in_2_15",
            f"{s_pct:.2f}%",
            "S grade % between 2 and 15",
        )
    )

    # 6. Leadership tier ordering — all stored tier values are in TIERS.
    from compute.leadership import TIERS as LEAD_TIERS
    bad_tiers = leadership["leadership_tier"].astype(str).unique().tolist()
    invalid = [t for t in bad_tiers if t not in LEAD_TIERS + ["nan"]]
    checks.append(
        _check(
            len(invalid) == 0,
            "leadership_tier_values_valid",
            invalid or "ok",
            "all tier values in TIERS",
        )
    )

    # 7. Setup confidence in [0, 1].
    sc = setups["setup_confidence"].dropna().astype(float)
    oob = int(((sc < 0) | (sc > 1)).sum())
    checks.append(
        _check(
            oob == 0,
            "setup_confidence_in_0_1",
            f"{oob} rows",
            "setup_confidence ∈ [0,1]",
        )
    )

    # 8. Index alignment — ccqs/components/state/leadership/setups all (ticker,date).
    idxs = {
        "ccqs": ccqs.index,
        "components": components.index,
        "state": state.index,
        "leadership": leadership.index,
        "setups": setups.index,
    }
    same_len = len({len(i) for i in idxs.values()}) == 1
    same_names = all(list(i.names) == ["ticker", "date"] for i in idxs.values())
    checks.append(
        _check(
            same_len and same_names,
            "index_alignment",
            {k: len(v) for k, v in idxs.items()},
            "all (ticker,date) indexes equal length and named",
        )
    )

    # 9. Theme CCQS valid coverage ≥ 50% of theme rows (looser bound — needs
    #    240+ trading days of warmup for r-squared / 252d high).
    if theme is not None:
        tot = len(theme)
        valid = int(theme["theme_ccqs"].notna().sum())
        ratio = valid / tot if tot else 0.0
        checks.append(
            _check(
                ratio >= 0.50,
                "theme_ccqs_coverage",
                f"{ratio*100:.2f}% valid",
                "≥50% of theme rows have a valid theme_ccqs",
            )
        )
    else:
        checks.append(
            _check(False, "theme_ccqs_coverage", "missing", "theme_aggregates.parquet absent")
        )

    # 10. Feature freshness — latest date is ≤ 5 calendar days old.
    today = pd.Timestamp.utcnow().normalize().tz_localize(None)
    feat_max = pd.to_datetime(features.index.get_level_values("date").max())
    days_old = (today - feat_max).days
    checks.append(
        _check(
            days_old <= 5,
            "features_fresh_within_5d",
            f"max date {feat_max.date()} ({days_old}d old)",
            "latest features date within 5 calendar days",
        )
    )

    # 11. Universe coverage — at least 750 unique tickers with at least one
    #     non-NaN CCQS in the last 30 trading days. Threshold accounts for
    #     attrition from delistings, recent IPOs without sufficient history,
    #     and the small failed-fetch list (typically <20 names).
    last_dates = sorted(ccqs.index.get_level_values("date").unique())[-30:]
    recent = ccqs.loc[ccqs.index.get_level_values("date").isin(last_dates)]
    n_with_ccqs = int(recent["ccqs"].dropna().reset_index()["ticker"].nunique())
    checks.append(
        _check(
            n_with_ccqs >= 750,
            "universe_coverage",
            f"{n_with_ccqs} tickers",
            "≥750 unique tickers with a CCQS in the last 30 trading days",
        )
    )

    # 12. Latest-day coverage — the MOST RECENT date must have ≥ 820 tickers
    #     with a non-NaN CCQS, AND must not drop > 4% vs the prior trading day.
    #     Check #11's 30-day window counts a ticker as covered if it scored on
    #     ANY of the last 30 days, so a sudden single-day collapse (e.g. a batch
    #     of truncated yfinance frames lacking 50/200d history) stays invisible
    #     to it. This same-day check catches that regression (2026-06-15: a clean
    #     858 → 790 single-day drop sailed through the green #11 gate).
    all_dates = sorted(ccqs.index.get_level_values("date").unique())
    d_last = all_dates[-1]
    cur_cov = int(ccqs.xs(d_last, level="date")["ccqs"].notna().sum())
    if len(all_dates) >= 2:
        prev_cov = int(ccqs.xs(all_dates[-2], level="date")["ccqs"].notna().sum())
        drop_pct = (prev_cov - cur_cov) / prev_cov * 100.0 if prev_cov else 0.0
    else:
        prev_cov, drop_pct = cur_cov, 0.0
    checks.append(
        _check(
            cur_cov >= 820 and drop_pct <= 4.0,
            "latest_day_coverage",
            f"{cur_cov} scored on {d_last.date()} ({drop_pct:+.1f}% vs prior {prev_cov})",
            "≥820 tickers scored on latest date AND ≤4% day-over-day drop",
        )
    )

    all_passed = all(c["passed"] for c in checks)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": all_passed,
        "n_checks": len(checks),
        "n_failed": sum(1 for c in checks if not c["passed"]),
        "checks": checks,
    }


def main() -> int:
    t0 = time.time()
    out = run_sanity_checks()
    elapsed = time.time() - t0

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))

    print()
    print("=" * 60)
    print("SANITY CHECKS")
    print("=" * 60)
    for i, c in enumerate(out["checks"], 1):
        flag = "PASS" if c["passed"] else "FAIL"
        print(f"  [{i:2d}] {flag}  {c['name']:<32} {c['observed']}")
    print(f"  {out['n_failed']}/{out['n_checks']} failed")
    print(f"Elapsed: {elapsed:.1f}s")
    print("=" * 60)
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
