"""Cached data loaders for the single-page dashboard.

All loaders cache for 30 minutes. Each loader returns either a DataFrame
shaped for direct table rendering, or a small dict/series.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Project root so `from data.universe import ...` and `from compute.ccqs import ...` work
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CACHE_DIR = ROOT / "data" / "cache"
DASHBOARD_DIR = CACHE_DIR / "dashboard"
TTL = 1800


def _resolve(name: str) -> Path:
    """Prefer the slim dashboard cache (shipped with the deployed app),
    fall back to the full pipeline cache for local dev.
    """
    slim = DASHBOARD_DIR / name
    if slim.exists():
        return slim
    return CACHE_DIR / name


# ---------------------------------------------------------------------------
# Raw parquet readers (single source of truth, kept thin)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=TTL, show_spinner=False)
def _read_parquet(name: str) -> pd.DataFrame:
    path = _resolve(name)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(ttl=TTL, show_spinner=False)
def _read_json(name: str) -> dict:
    path = _resolve(name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _basket_map() -> dict[str, str]:
    """Ticker → primary basket name."""
    try:
        from data.universe import PRIMARY_BASKETS
        return dict(PRIMARY_BASKETS)
    except Exception:
        return {}


def _all_membership_long() -> pd.DataFrame:
    """Long (ticker, basket) DataFrame of all tagged members across every
    basket. Mirrors `compute/aggregation.py:_basket_membership_long` so the
    dashboard's `top_member` / `members` columns reflect the same
    membership the Themes aggregation uses (Phase 30.1).
    """
    try:
        from data.universe import CATEGORIES
        rows: list[tuple[str, str]] = []
        for _cat, baskets_d in CATEGORIES.items():
            for basket, tickers in baskets_d.items():
                for t in tickers:
                    rows.append((t, basket))
        df = pd.DataFrame(rows, columns=["ticker", "basket"]).drop_duplicates()
        return df
    except Exception:
        return pd.DataFrame(columns=["ticker", "basket"])


# ---------------------------------------------------------------------------
# Dashboard data — one row per ticker at latest snapshot
# ---------------------------------------------------------------------------

@st.cache_data(ttl=TTL, show_spinner=False)
def load_dashboard_data() -> tuple[pd.DataFrame, str]:
    """Combined latest-snapshot frame + latest date string."""
    ccqs = _read_parquet("ccqs.parquet")
    if ccqs.empty:
        return pd.DataFrame(), ""

    states = _read_parquet("state.parquet")
    leadership = _read_parquet("leadership.parquet")
    setups = _read_parquet("setups.parquet")
    features = _read_parquet("features.parquet")

    latest = ccqs.index.get_level_values("date").max()

    ccqs_latest = ccqs.xs(latest, level="date")
    states_latest = states.xs(latest, level="date") if not states.empty else pd.DataFrame()
    leadership_latest = leadership.xs(latest, level="date") if not leadership.empty else pd.DataFrame()
    setups_latest = setups.xs(latest, level="date") if not setups.empty else pd.DataFrame()
    features_latest = features.xs(latest, level="date") if not features.empty else pd.DataFrame()

    # Phase 18 — Δ CCQS at three trading-day horizons (1d, 5d, 21d) replaces
    # the single Δ Today column. Lookbacks step through the sorted unique
    # date index in ccqs.parquet, so offsets are trading-day-accurate
    # regardless of weekends / market holidays.
    dates_sorted = ccqs.index.get_level_values("date").unique().sort_values()

    def _delta(offset: int) -> pd.Series:
        if len(dates_sorted) > offset:
            prior = dates_sorted[-1 - offset]
            ccqs_prior = ccqs.xs(prior, level="date")["ccqs"]
            return ccqs_latest["ccqs"] - ccqs_prior
        return pd.Series(float("nan"), index=ccqs_latest.index)

    ccqs_change_1d = _delta(1)
    ccqs_change_5d = _delta(5)
    ccqs_change_21d = _delta(21)

    basket_map = _basket_map()
    baskets = pd.Series(
        ccqs_latest.index.map(lambda t: basket_map.get(t, "—")),
        index=ccqs_latest.index,
        name="basket",
    )

    combined = pd.DataFrame({
        "ccqs":                   ccqs_latest["ccqs"],
        "grade":                  ccqs_latest["grade"],
        "ccqs_change":            ccqs_change_1d,       # kept for back-compat (1d)
        "ccqs_change_1d":         ccqs_change_1d,
        "ccqs_change_5d":         ccqs_change_5d,
        "ccqs_change_21d":        ccqs_change_21d,
        "leadership_tier":        leadership_latest.get("leadership_tier", pd.Series(index=ccqs_latest.index)),
        "primary_state":          states_latest.get("primary_state", pd.Series(index=ccqs_latest.index)),
        "state_confidence":       states_latest.get("state_confidence", pd.Series(0.0, index=ccqs_latest.index)),
        "setup_label":            setups_latest.get("setup", pd.Series("—", index=ccqs_latest.index)),
        "basket":                 baskets,
        "rs_rating_spy":          features_latest.get("rs_rating_spy", pd.Series(index=ccqs_latest.index)),
        "information_ratio_252d": features_latest.get("information_ratio_252d", pd.Series(0.0, index=ccqs_latest.index)),
        # Phase 24 — partial-history disclosure. is_partial=True when CCQS
        # was computed by renormalizing state weights across the components
        # the ticker has accumulated (typical for IPOs / spin-offs still
        # inside the 504-day long-window-feature warmup).
        "is_partial":             ccqs_latest.get("is_partial", pd.Series(False, index=ccqs_latest.index)).fillna(False).astype(bool),
        "weight_present":         ccqs_latest.get("weight_present", pd.Series(1.0, index=ccqs_latest.index)),
        "n_valid_components":     ccqs_latest.get("n_valid_components", pd.Series(11, index=ccqs_latest.index)),
    })
    combined = combined.dropna(subset=["ccqs"])

    latest_str = latest.strftime("%Y-%m-%d") if hasattr(latest, "strftime") else str(latest)
    return combined, latest_str


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

@st.cache_data(ttl=TTL, show_spinner=False)
def load_themes_data() -> pd.DataFrame:
    themes = _read_parquet("theme_aggregates.parquet")
    if themes.empty:
        return pd.DataFrame()

    latest = themes.index.get_level_values("date").max()
    t_latest = themes.xs(latest, level="date")

    t_latest = t_latest[
        t_latest["theme_ccqs"].notna()
        & (t_latest["n_constituents"] >= 3)
    ].sort_values("theme_ccqs", ascending=False)

    # Phase 18 — also surface the full ticker list per basket (sorted by
    # CCQS descending) so users can cross-reference on charting platforms.
    # Phase 30.2 — switched membership source from PRIMARY_BASKETS only to
    # all tagged members (matches the aggregation in Phase 30.1). Without
    # this, the new "Magnificent Seven" basket showed "—" because only
    # AAPL has it as primary; the other 6 are tagged but had their primary
    # in Hyperscalers / AI Compute / EV. Same effect surfaces ~40 TAG
    # baskets that previously had no top_member.
    ccqs = _read_parquet("ccqs.parquet")
    top_member_map: dict[str, str] = {}
    members_map: dict[str, str] = {}
    if not ccqs.empty:
        ccqs_latest = ccqs.xs(latest, level="date") if latest in ccqs.index.get_level_values("date") else pd.DataFrame()
        if not ccqs_latest.empty:
            membership = _all_membership_long()
            tmp = ccqs_latest[["ccqs"]].reset_index()
            if "ticker" not in tmp.columns:
                tmp = tmp.rename(columns={tmp.columns[0]: "ticker"})
            tmp = tmp.merge(membership, on="ticker", how="inner")
            tmp = tmp.dropna(subset=["basket", "ccqs"])
            tmp = tmp.sort_values("ccqs", ascending=False)
            top_member_map = tmp.groupby("basket").head(1).set_index("basket")["ticker"].to_dict()
            # Comma-joined ticker list per basket, sorted by CCQS desc.
            members_map = (
                tmp.groupby("basket")["ticker"]
                .apply(lambda s: ", ".join(s.astype(str).tolist()))
                .to_dict()
            )

    t_latest = t_latest.copy()
    t_latest["top_member"] = t_latest.index.map(top_member_map).fillna("—")
    t_latest["members"] = t_latest.index.map(members_map).fillna("—")
    t_latest = t_latest.reset_index().rename(columns={"basket": "basket_name"})
    return t_latest


# ---------------------------------------------------------------------------
# Anomalies & derived T-vs-T-1 change lists
# ---------------------------------------------------------------------------

def load_anomalies() -> dict:
    return _read_json("anomalies.json")


# ---------------------------------------------------------------------------
# Regime context (Priority 3d — display-layer warnings)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=TTL, show_spinner=False)
def load_regime_context() -> dict:
    """Load the regime_context.json baked at dashboard-cache build time.

    Returns a dict with keys:
        - market_vol: {current_regime, spy_vol_20d_latest, tercile_lo, tercile_hi, latest_date}
        - dvol_quintile_by_ticker: {ticker: 1..5}  (5 = largest dollar volume)
        - defensive_baskets: list[str]

    Empty dict if file missing (graceful — no warnings rendered).
    """
    return _read_json("regime_context.json")


# Phase 18 — per-stock reliability_flags() removed. CCQS is a technical
# scoring system, not a predictive model; per-stock "reliability" framing
# (mega-cap warnings, defensive-sector warnings, EXHAUSTION caveats,
# leadership-tier inversion warnings) was misleading and has been
# retired. Broad-market context is now surfaced via a single optional
# caution banner in app/streamlit_app.py, triggered only by SPY
# drawdown depth.


def _today_and_prev_dates(df: pd.DataFrame) -> tuple | None:
    if df.empty or "date" not in df.index.names:
        return None
    dates = df.index.get_level_values("date").unique().sort_values()
    if len(dates) < 2:
        return None
    return dates[-1], dates[-2]


@st.cache_data(ttl=TTL, show_spinner=False)
def get_emerging_leaders_today(n: int = 10) -> pd.DataFrame:
    """Phase 18 — top N stocks by largest positive 1-day Δ CCQS today.

    Replaces the prior tier-transition definition with a magnitude-ranked
    list so the section always shows a standardized N rows regardless of
    how many stocks crossed a tier boundary on any given day.
    Returns DataFrame [leadership_tier, ccqs] for compatibility with the
    existing renderer.
    """
    lead = _read_parquet("leadership.parquet")
    ccqs = _read_parquet("ccqs.parquet")
    if lead.empty or ccqs.empty:
        return pd.DataFrame()

    pair = _today_and_prev_dates(ccqs)
    if pair is None:
        return pd.DataFrame()
    today, prev = pair

    ccqs_today = ccqs.xs(today, level="date")["ccqs"]
    ccqs_prev = ccqs.xs(prev, level="date")["ccqs"]
    change = (ccqs_today - ccqs_prev).rename("ccqs_change")

    tier_today = lead.xs(today, level="date")["leadership_tier"] if not lead.empty else pd.Series(dtype=object)

    out = pd.DataFrame({
        "leadership_tier": tier_today.reindex(change.index),
        "ccqs": ccqs_today.reindex(change.index),
        "ccqs_change": change,
    })
    out = out.dropna(subset=["ccqs", "ccqs_change"])
    out = out.sort_values("ccqs_change", ascending=False).head(n)
    return out


@st.cache_data(ttl=TTL, show_spinner=False)
def get_newly_broken_today(n: int = 10) -> pd.DataFrame:
    """Phase 18 — top N stocks by largest negative 1-day Δ CCQS today.

    Replaces the prior "moved into DETERIORATING state" filter with a
    magnitude-ranked list so the section always shows a standardized N
    rows. Returns DataFrame [prev_state, ccqs_change] for compatibility
    with the existing renderer.
    """
    state = _read_parquet("state.parquet")
    ccqs = _read_parquet("ccqs.parquet")
    if ccqs.empty:
        return pd.DataFrame()

    pair = _today_and_prev_dates(ccqs)
    if pair is None:
        return pd.DataFrame()
    today, prev = pair

    ccqs_today = ccqs.xs(today, level="date")["ccqs"]
    ccqs_prev = ccqs.xs(prev, level="date")["ccqs"]
    change = (ccqs_today - ccqs_prev).rename("ccqs_change")

    prev_state = (
        state.xs(prev, level="date")["primary_state"]
        if not state.empty else pd.Series(dtype=object)
    )

    out = pd.DataFrame({
        "prev_state": prev_state.reindex(change.index),
        "ccqs_change": change,
    })
    out = out.dropna(subset=["ccqs_change"])
    out = out.sort_values("ccqs_change", ascending=True).head(n)
    return out


@st.cache_data(ttl=TTL, show_spinner=False)
def get_grade_jumps_today(n: int = 10) -> pd.DataFrame:
    """Phase 18 — top N stocks by largest |Δ CCQS| where grade letter changed.

    If fewer than N stocks had a grade-letter transition today, pad with
    the next largest |Δ CCQS| stocks (grade_move = "—") so the section
    always renders N rows.
    """
    ccqs = _read_parquet("ccqs.parquet")
    if ccqs.empty:
        return pd.DataFrame()
    pair = _today_and_prev_dates(ccqs)
    if pair is None:
        return pd.DataFrame()
    today, prev = pair

    today_g = ccqs.xs(today, level="date")["grade"]
    prev_g = ccqs.xs(prev, level="date")["grade"]
    today_c = ccqs.xs(today, level="date")["ccqs"]
    prev_c = ccqs.xs(prev, level="date")["ccqs"]
    change = (today_c - prev_c).rename("ccqs_change")

    joined = pd.concat({"prev": prev_g, "today": today_g}, axis=1).dropna()
    changed_mask = joined["prev"].astype(str) != joined["today"].astype(str)

    grade_move = pd.Series("—", index=joined.index, dtype=object)
    grade_move.loc[changed_mask] = (
        joined.loc[changed_mask, "prev"].astype(str)
        + " → "
        + joined.loc[changed_mask, "today"].astype(str)
    )

    out = pd.DataFrame({"grade_move": grade_move, "ccqs_change": change.reindex(joined.index)})
    out = out.dropna(subset=["ccqs_change"])
    # Prefer grade-changers; then fall back to largest absolute movers.
    out["_rank_key"] = (~changed_mask.reindex(out.index).fillna(False)).astype(int)
    out["_abs_change"] = out["ccqs_change"].abs()
    out = out.sort_values(["_rank_key", "_abs_change"], ascending=[True, False]).head(n)
    out = out.drop(columns=["_rank_key", "_abs_change"])
    return out


# ---------------------------------------------------------------------------
# Stock detail
# ---------------------------------------------------------------------------

COMPONENT_DISPLAY_NAMES = {
    "s_rs":                  "Relative Strength",
    "s_rs_leadership":       "Relative Strength Leadership",
    "s_residual_momentum":   "Residual Momentum",
    "s_rsl":                 "Relative Strength Line",
    "s_trend_slope":         "Trend Slope",
    "s_structure":           "Structure",
    "s_mtf":                 "Multi-Timeframe Alignment",
    "s_extension":           "Extension",
    "s_momentum":            "Momentum",
    "s_volume":              "Volume Pattern",
    # Phase 28 — s_demand removed (weight 0.0 in every state since Phase 7).
}


@st.cache_data(ttl=TTL, show_spinner=False)
def load_components_for_ticker(ticker: str) -> pd.DataFrame:
    """Returns [component, z_score, weight, contribution] for the ticker today."""
    components = _read_parquet("components.parquet")
    state = _read_parquet("state.parquet")
    if components.empty or state.empty:
        return pd.DataFrame(columns=["component", "z_score", "weight", "contribution"])

    latest = components.index.get_level_values("date").max()
    try:
        comp_row = components.xs((ticker, latest))
    except KeyError:
        return pd.DataFrame(columns=["component", "z_score", "weight", "contribution"])

    try:
        primary_state = state.xs((ticker, latest))["primary_state"]
    except KeyError:
        primary_state = "INDETERMINATE"

    try:
        from compute.ccqs import STATE_WEIGHTS
        weights = STATE_WEIGHTS.get(str(primary_state), STATE_WEIGHTS.get("INDETERMINATE", {}))
    except Exception:
        weights = {}

    rows = []
    for cmp_name, z in comp_row.items():
        w = float(weights.get(cmp_name, 0.0))
        # Phase 28 — hide components with zero weight in this ticker's primary
        # state. They contribute literally nothing to the CCQS for this name;
        # showing them is pure noise. A component zeroed in one state can
        # still be active in another (e.g., s_extension is 0 in TRENDING but
        # 1-2% in PULLBACK/CONSOLIDATING/EXHAUSTION/INDETERMINATE), so this
        # filter is per-row, not global.
        if w == 0.0:
            continue
        contrib = float(z) * w if pd.notna(z) else 0.0
        display = COMPONENT_DISPLAY_NAMES.get(
            cmp_name,
            cmp_name.removeprefix("s_").replace("_", " ").title(),
        )
        rows.append({
            "component":    display,
            "z_score":      float(z) if pd.notna(z) else np.nan,
            "weight":       w,
            "contribution": contrib,
        })
    df = pd.DataFrame(rows)
    return df.sort_values("contribution", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)


PERIOD_DAYS = {
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "3Y": 1095,
    "5Y": 1825,
    "INCEPTION": None,
}


@st.cache_data(ttl=TTL, show_spinner=False)
def load_grade_thresholds_history(period: str = "1Y") -> pd.DataFrame:
    """Per-date cross-sectional CCQS quantile thresholds for grade bands.

    Returns DataFrame indexed by date with columns:
        q30 — D/C boundary  (top 70% threshold)
        q55 — C/B boundary
        q80 — B/A boundary
        q92 — A/S boundary  (top 8% threshold)

    These are the exact thresholds used by compute/ccqs.py to assign
    per-date letter grades, recomputed here from the live ccqs cache.
    Sliced by the same `period` rules as load_ticker_history so the
    bands cover the same horizontal range as the displayed line.
    """
    if period not in PERIOD_DAYS:
        raise ValueError(f"Invalid period: {period!r}")

    ccqs = _read_parquet("ccqs.parquet")
    if ccqs.empty:
        return pd.DataFrame(columns=["q30", "q55", "q80", "q92"])

    if period != "INCEPTION":
        today = pd.Timestamp.today().normalize()
        cutoff = today - pd.Timedelta(days=PERIOD_DAYS[period])
        mask = ccqs.index.get_level_values("date") >= cutoff
        sub = ccqs[mask]
    else:
        sub = ccqs

    if sub.empty:
        return pd.DataFrame(columns=["q30", "q55", "q80", "q92"])

    series = sub["ccqs"].astype(float).dropna()
    if series.empty:
        return pd.DataFrame(columns=["q30", "q55", "q80", "q92"])

    g = series.groupby(level="date", sort=True)
    out = pd.DataFrame({
        "q30": g.quantile(0.30),
        "q55": g.quantile(0.55),
        "q80": g.quantile(0.80),
        "q92": g.quantile(0.92),
    })
    return out


@st.cache_data(ttl=TTL, show_spinner=False)
def load_ticker_history(ticker: str, period: str = "1Y") -> pd.DataFrame:
    """Per-ticker CCQS history sliced by named period.

    Returns DataFrame with columns:
        date, ccqs, grade, primary_state, leadership_tier, setup_label

    period: one of 1W / 1M / 3M / 6M / 1Y / 3Y / 5Y / INCEPTION.
    INCEPTION returns the full available history (typically 2020-01-01 onward
    after 252-day feature warm-up).
    """
    if period not in PERIOD_DAYS:
        raise ValueError(
            f"Invalid period: {period!r}. Must be one of {list(PERIOD_DAYS.keys())}"
        )

    ccqs = _read_parquet("ccqs.parquet")
    if ccqs.empty:
        return pd.DataFrame()

    ticker_ccqs = ccqs[ccqs.index.get_level_values("ticker") == ticker]
    if ticker_ccqs.empty:
        return pd.DataFrame()

    if period != "INCEPTION":
        today = pd.Timestamp.today().normalize()
        days = PERIOD_DAYS[period]
        cutoff = today - pd.Timedelta(days=days)
        ticker_ccqs = ticker_ccqs[ticker_ccqs.index.get_level_values("date") >= cutoff]

    states = _read_parquet("state.parquet")
    leadership = _read_parquet("leadership.parquet")
    setups = _read_parquet("setups.parquet")

    result = ticker_ccqs[["ccqs", "grade"]].copy()

    if not states.empty:
        ticker_states = states[states.index.get_level_values("ticker") == ticker]
        if not ticker_states.empty and "primary_state" in ticker_states.columns:
            result = result.join(ticker_states[["primary_state"]], how="left")

    if not leadership.empty:
        ticker_leadership = leadership[leadership.index.get_level_values("ticker") == ticker]
        if not ticker_leadership.empty and "leadership_tier" in ticker_leadership.columns:
            result = result.join(ticker_leadership[["leadership_tier"]], how="left")

    if not setups.empty:
        ticker_setups = setups[setups.index.get_level_values("ticker") == ticker]
        if not ticker_setups.empty:
            # setups.parquet stores label in `setup` (not `setup_label`)
            if "setup_label" in ticker_setups.columns:
                result = result.join(ticker_setups[["setup_label"]], how="left")
            elif "setup" in ticker_setups.columns:
                result = result.join(
                    ticker_setups[["setup"]].rename(columns={"setup": "setup_label"}),
                    how="left",
                )

    result = result.dropna(subset=["ccqs"])
    result = result.reset_index()
    if "ticker" in result.columns:
        result = result.drop(columns=["ticker"])
    result = result.sort_values("date").reset_index(drop=True)
    return result


@st.cache_data(ttl=TTL, show_spinner=False)
def load_benchmark_ohlcv(ticker: str = "SPY", days: int | None = None) -> pd.DataFrame:
    """Load benchmark OHLCV (SPY/QQQ) from the carved-out benchmarks parquet.

    Returns DataFrame indexed by date with OHLCV columns. Benchmarks are
    excluded from the scoring panel but persisted separately for chart
    overlays. Returns empty frame if benchmarks.parquet missing or ticker
    not present.
    """
    b = _read_parquet("benchmarks.parquet")
    if b.empty:
        return pd.DataFrame()
    if "ticker" not in b.columns:
        return pd.DataFrame()
    sub = b[b["ticker"] == ticker].copy()
    if sub.empty:
        return pd.DataFrame()
    sub["date"] = pd.to_datetime(sub["date"])
    sub = sub.set_index("date").sort_index()
    if days is not None:
        sub = sub.tail(days)
    return sub


@st.cache_data(ttl=TTL, show_spinner=False)
def load_key_metrics_for_ticker(ticker: str) -> pd.DataFrame:
    """Returns df [metric, value(str)] — 8 rows of pre-formatted key metrics."""
    features = _read_parquet("features.parquet")
    if features.empty:
        return pd.DataFrame(columns=["metric", "value"])

    latest = features.index.get_level_values("date").max()
    try:
        row = features.xs((ticker, latest))
    except KeyError:
        return pd.DataFrame(columns=["metric", "value"])

    def get(key, default=np.nan):
        v = row.get(key, default)
        return v if v is not None else default

    def fmt_pct(v):
        return f"{float(v):+.1f}%" if pd.notna(v) else "—"

    def fmt_num(v, digits=2):
        return f"{float(v):,.{digits}f}" if pd.notna(v) else "—"

    def fmt_int(v):
        return f"{int(v):,}" if pd.notna(v) else "—"

    metrics = [
        ("% from 50-day Moving Average",        fmt_pct(get("pct_ma_50"))),
        ("% from 200-day Moving Average",       fmt_pct(get("pct_ma_200"))),
        ("% from 52-week High",                 fmt_pct(get("pct_from_52w_high"))),
        ("Average Directional Index (14)",      fmt_num(get("adx_14"), 1)),
        ("Relative Strength Index (14)",        fmt_num(get("rsi_14"), 1)),
        ("Realized Volatility (60-day)",        fmt_num(get("realized_vol_60"), 1)),
        ("Within-Basket Z-Score (21-day)",      fmt_num(get("within_basket_z_21d"), 2)),
        ("Distribution Days (25-day)",          fmt_int(get("distribution_days_25"))),
    ]
    return pd.DataFrame(metrics, columns=["metric", "value"])


# ---------------------------------------------------------------------------
# System health
# ---------------------------------------------------------------------------

@st.cache_data(ttl=TTL, show_spinner=False)
def load_oos_metrics() -> pd.DataFrame:
    """Composite CCQS OOS metrics, one row per horizon."""
    j = _read_json("oos_ic_summary.json")
    rows = j.get("rows", []) or []
    if not rows:
        return pd.DataFrame(columns=["horizon", "oos_ic", "t_stat", "hit_rate"])
    df = pd.DataFrame(rows)
    # Composite CCQS only
    comp = df[df["score_type"] == "composite"].copy()
    if comp.empty:
        # fallback: any "ccqs" score_name
        comp = df[df["score_name"].astype(str).str.lower().str.contains("ccqs")].copy()
    out = pd.DataFrame({
        "horizon":  comp["horizon"].astype(int).astype(str) + "d",
        "oos_ic":   comp["oos_ic_mean"].astype(float),
        "t_stat":   comp["oos_ic_t_stat"].astype(float),
        "hit_rate": comp["oos_hit_rate"].astype(float),
    })
    out = out.sort_values("horizon", key=lambda s: s.str.replace("d", "").astype(int)).reset_index(drop=True)
    return out


@st.cache_data(ttl=TTL, show_spinner=False)
def load_sanity_status() -> dict:
    j = _read_json("sanity_checks.json")
    total = int(j.get("n_checks", 0))
    failed = int(j.get("n_failed", 0))
    return {"passed": total - failed, "total": total}
