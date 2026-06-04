"""Build a slim dashboard cache for shipping with the Streamlit app.

Full cache at data/cache/*.parquet is 6GB and contains pipeline intermediates
that the dashboard never touches. This script writes a compact subset to
data/cache/dashboard/ (~20-30MB) suitable for committing to git so Streamlit
Cloud deploys with data already in place.

Schema is identical to the full files — same MultiIndex (date, ticker) and the
column subset the dashboard reads. The loader will pick this up first if
present (see app/utils/data_loader.py).

Phase 3d (2026-05-25) — also writes `regime_context.json` summarizing the
display-layer regime warnings (market vol tercile, per-ticker dollar-volume
quintile). The dashboard reads this to surface honest "where CCQS is less
reliable" chips per Priority 2b findings, without needing the full
ohlcv_daily.parquet at deploy time.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "cache"
DST = ROOT / "data" / "cache" / "dashboard"


# Columns the dashboard actually reads (see app/utils/data_loader.py).
# Phase 24 — added is_partial / weight_present / n_valid_components so the
# stock detail page can surface a disclaimer for tickers whose CCQS was
# computed via renormalization (recent IPOs / spin-offs with insufficient
# long-window history).
HISTORY_COLS = {
    "ccqs.parquet":       ["ccqs", "grade", "is_partial", "weight_present", "n_valid_components"],
    "state.parquet":      ["primary_state", "state_confidence"],
    "leadership.parquet": ["leadership_tier"],
    "setups.parquet":     ["setup"],
}

LATEST_ONLY_COLS = {
    "features.parquet": [
        "rs_rating_spy", "information_ratio_252d",
        "pct_ma_50", "pct_ma_200", "pct_from_52w_high",
        "adx_14", "rsi_14", "realized_vol_60",
        "within_basket_z_21d", "distribution_days_25",
    ],
    "components.parquet": [
        "s_rs", "s_rs_leadership", "s_residual_momentum",
        "s_rsl", "s_trend_slope",
        "s_structure", "s_mtf", "s_extension",
        "s_momentum", "s_volume",
    ],
}

LATEST_ONLY_ALL_COLS = ["theme_aggregates.parquet"]

COPY_AS_IS = ["benchmarks.parquet"]

JSON_FILES = ["oos_ic_summary.json", "sanity_checks.json", "anomalies.json"]


# Priority 2b basket-level 60d IC bottom-10 baskets — used by the dashboard
# to flag stocks in sectors where the composite has documented weak signal.
# Frozen here so the dashboard doesn't need to recompute it at run time.
# Update only when a re-run of /tmp/p2b_conditional_ic.py demonstrates a
# materially different bottom set on fresh data.
DEFENSIVE_BASKETS: tuple[str, ...] = (
    "Household and Personal Care",
    "Gold Royalty and Streamers",
    "Integrated Energy Majors",
    "Gaming Publishers",
    "Offshore Drilling",
    "Railroads",
    "Diagnostics and Life Science Tools",
    "LNG and LPG Shipping",
    "Beverages and Tobacco",
    "Industrial Automation",
)


def _market_vol_thresholds(benchmarks_path: Path) -> dict:
    """Compute SPY 20d realized vol terciles (LOW / MID / HIGH) using the full
    history, then label the latest date's regime."""
    bench = pd.read_parquet(benchmarks_path)
    spy = bench[bench['ticker'] == 'SPY'].sort_values('date').copy()
    if spy.empty:
        return {}
    spy['log_ret'] = np.log(spy['adj_close'].astype(float)).diff()
    spy['vol_20d'] = spy['log_ret'].rolling(20, min_periods=15).std() * np.sqrt(252)
    spy = spy.dropna(subset=['vol_20d'])
    if spy.empty:
        return {}
    t_lo, t_hi = float(spy['vol_20d'].quantile(0.33)), float(spy['vol_20d'].quantile(0.67))
    latest_vol = float(spy['vol_20d'].iloc[-1])
    if latest_vol <= t_lo:
        regime = "LOW"
    elif latest_vol >= t_hi:
        regime = "HIGH"
    else:
        regime = "MID"
    return {
        "latest_date": spy['date'].iloc[-1].strftime("%Y-%m-%d"),
        "spy_vol_20d_latest": round(latest_vol, 4),
        "tercile_lo": round(t_lo, 4),
        "tercile_hi": round(t_hi, 4),
        "current_regime": regime,
    }


def _dollar_volume_quintiles(ohlcv_path: Path) -> dict[str, int]:
    """Per-ticker dollar-volume quintile assignment for the LATEST date.
    Returns {ticker: 1..5}. Q5 = highest dollar volume (mega-caps)."""
    if not ohlcv_path.exists():
        return {}
    oh = pd.read_parquet(ohlcv_path, columns=['ticker','date','close','volume'])
    oh = oh.sort_values(['ticker', 'date']).copy()
    oh['dvol'] = oh['close'].astype(float) * oh['volume'].astype(float)
    oh['dvol_20d'] = oh.groupby('ticker', sort=False)['dvol'].transform(
        lambda x: x.rolling(20, min_periods=10).mean()
    )
    latest = oh['date'].max()
    snap = oh[oh['date'] == latest].dropna(subset=['dvol_20d'])
    if snap.empty:
        return {}
    # Cross-sectional rank → quintile
    r = snap['dvol_20d'].rank(method='first', pct=True)
    q = pd.Series(np.nan, index=snap.index)
    q[r <= 0.20] = 1
    q[(r > 0.20) & (r <= 0.40)] = 2
    q[(r > 0.40) & (r <= 0.60)] = 3
    q[(r > 0.60) & (r <= 0.80)] = 4
    q[r > 0.80] = 5
    return {row['ticker']: int(qv) for (_, row), qv in zip(snap.iterrows(), q) if not pd.isna(qv)}


def _design_space_regime(benchmarks_path: Path) -> dict:
    """Phase 17 — empirically-derived CCQS design-space regime.

    Phase 16-17 empirical evidence established that the CCQS composite
    signal is regime-conditional: it works in "trending market" conditions
    and fails in deep drawdowns. The deployment gate is empirically defined
    as `dd_lt_15pct` — SPY drawdown from its 252-day high is shallower than
    15%.

    Phase 17.0 empirical justification:
      • t-statistic 8.74, p < 0.0001 vs other candidate regime indicators
      • IC differential at 63d: +0.093 (in-regime +0.027 vs off-regime −0.066)
      • Walk-forward validation: regime-on periods at 126d horizon are the
        only configuration where CCQS survives OOS robustness criteria
        (Phase 17.4)
      • Real-time computable from SPY closing price + 252-day rolling max

    Three-state classification:
      GREEN  — dd_lt_15pct=TRUE AND SPY > 200d MA  (design space, high confidence)
      YELLOW — dd_lt_15pct=TRUE AND SPY ≤ 200d MA  (in-regime but trend uncertain)
      RED    — dd_lt_15pct=FALSE                   (out of design space; apply discretion)
    """
    bench = pd.read_parquet(benchmarks_path)
    spy = bench[bench['ticker'] == 'SPY'].sort_values('date').copy()
    if spy.empty:
        return {}
    spy['adj_close'] = spy['adj_close'].astype(float)
    # 252-day rolling max and SPY 200d MA
    spy['rolling_max_252d'] = spy['adj_close'].rolling(252, min_periods=63).max()
    spy['dd_from_high'] = (spy['adj_close'] - spy['rolling_max_252d']) / spy['rolling_max_252d']
    spy['ma_200d'] = spy['adj_close'].rolling(200, min_periods=50).mean()
    spy['above_200ma'] = spy['adj_close'] > spy['ma_200d']
    spy = spy.dropna(subset=['dd_from_high', 'above_200ma'])
    if spy.empty:
        return {}
    latest = spy.iloc[-1]
    dd = float(latest['dd_from_high'])
    above_200 = bool(latest['above_200ma'])
    in_regime = dd > -0.15
    if not in_regime:
        state, label = "RED", "Out of design space — apply discretion"
    elif above_200:
        state, label = "GREEN", "Design space — high confidence"
    else:
        state, label = "YELLOW", "In-regime but below 200d MA — moderate confidence"
    return {
        "indicator": "dd_lt_15pct",
        "indicator_description": (
            "SPY drawdown from 252-day high is shallower than 15%. "
            "Empirically derived gate for CCQS predictive validity."
        ),
        "latest_date": latest['date'].strftime("%Y-%m-%d"),
        "spy_close": round(float(latest['adj_close']), 2),
        "spy_252d_max": round(float(latest['rolling_max_252d']), 2),
        "spy_dd_from_high": round(dd, 4),
        "spy_above_200ma": above_200,
        "in_regime": in_regime,
        "regime_state": state,
        "regime_label": label,
        "empirical_basis": {
            "ic_differential_63d": 0.093,
            "t_statistic": 8.74,
            "p_value_lt": 0.0001,
            "on_fraction_full_sample": 0.90,
            "walk_forward_robust_at_126d": True,
            "phase": "17.0",
        },
    }


def _build_regime_context() -> dict:
    """Top-level: market vol regime + per-ticker dvol quintile + defensive list."""
    return {
        "schema_version": 2,
        "market_vol": _market_vol_thresholds(SRC / "benchmarks.parquet"),
        "ccqs_design_space": _design_space_regime(SRC / "benchmarks.parquet"),
        "dvol_quintile_by_ticker": _dollar_volume_quintiles(SRC / "ohlcv_daily.parquet"),
        "defensive_baskets": list(DEFENSIVE_BASKETS),
    }


def _read(name: str) -> pd.DataFrame:
    p = SRC / name
    if not p.exists():
        print(f"  skip {name} (missing)")
        return pd.DataFrame()
    return pd.read_parquet(p)


def _write(df: pd.DataFrame, name: str) -> None:
    out = DST / name
    df.to_parquet(out, compression="zstd")
    print(f"  wrote {name:42s} rows={len(df):>10,} size={out.stat().st_size / 1024:.1f}KB")


def _latest_date(df: pd.DataFrame):
    return df.index.get_level_values("date").max()


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"No source cache at {SRC}")
    DST.mkdir(parents=True, exist_ok=True)

    print(f"Building slim dashboard cache → {DST}")

    # 1. History-preserving slim files (full date range, column subset).
    for name, cols in HISTORY_COLS.items():
        df = _read(name)
        if df.empty:
            continue
        keep = [c for c in cols if c in df.columns]
        _write(df[keep], name)

    # 2. Latest-snapshot files with a column subset.
    for name, cols in LATEST_ONLY_COLS.items():
        df = _read(name)
        if df.empty:
            continue
        latest = _latest_date(df)
        slim = df.xs(latest, level="date", drop_level=False)
        keep = [c for c in cols if c in slim.columns]
        _write(slim[keep], name)

    # 3. Latest-snapshot files keeping all columns (theme aggregates etc.).
    for name in LATEST_ONLY_ALL_COLS:
        df = _read(name)
        if df.empty:
            continue
        latest = _latest_date(df)
        slim = df.xs(latest, level="date", drop_level=False)
        _write(slim, name)

    # 4. Copy-as-is small files.
    for name in COPY_AS_IS:
        src = SRC / name
        if not src.exists():
            print(f"  skip {name} (missing)")
            continue
        shutil.copy2(src, DST / name)
        print(f"  copied {name}")

    # 5. JSON sidecars.
    for name in JSON_FILES:
        src = SRC / name
        if not src.exists():
            print(f"  skip {name} (missing)")
            continue
        shutil.copy2(src, DST / name)
        print(f"  copied {name}")

    # 6. Regime context for Priority 3d display-layer warnings.
    rc = _build_regime_context()
    rc_path = DST / "regime_context.json"
    rc_path.write_text(json.dumps(rc, indent=2, default=str))
    n_dv = len(rc.get("dvol_quintile_by_ticker", {}))
    mv = rc.get("market_vol", {})
    print(f"  wrote regime_context.json  ({n_dv} tickers w/ dvol quintile, "
          f"market vol regime = {mv.get('current_regime', '?')})")

    total = sum(f.stat().st_size for f in DST.glob("*"))
    print(f"\nTotal dashboard cache: {total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
