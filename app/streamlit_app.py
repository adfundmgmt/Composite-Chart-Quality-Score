"""CCQS — single-page analytical dashboard.

Five sections, sidebar filters, footer. No decoration; data carries every signal.

Updated 2026-05-25 — Grade band shading added to CCQS Trajectory chart.
Updated 2026-05-29 — Phase 30: Magnificent Seven basket; AAPL moved out of Hyperscalers.
Updated 2026-05-26 — Phase 8a residual momentum added (10th component).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from app.utils.charts import ccqs_trajectory_chart
from app.utils.design_system import CUSTOM_CSS
from app.utils.data_loader import (
    get_emerging_leaders_today,
    get_grade_jumps_today,
    get_newly_broken_today,
    load_components_for_ticker,
    load_dashboard_data,
    load_grade_thresholds_history,
    load_key_metrics_for_ticker,
    load_oos_metrics,
    load_regime_context,
    load_themes_data,
    load_ticker_history,
)
from app.utils.data_loader_sandbox import (
    load_sandbox_comparison_stocks,
    load_sandbox_dashboard_data,
    load_sandbox_diagnostics,
    load_sandbox_only_top_stocks,
    load_sandbox_themes_data,
    load_sandbox_top_by_basket,
    load_sandbox_validation_status,
)
from app.utils.tables import (
    component_table,
    emerging_leaders_table,
    grade_jumps_table,
    key_metrics_table,
    newly_broken_table,
    oos_ic_table,
    peers_table,
    themes_table,
    top_stocks_table,
)
from compute.display_labels import (  # Phase 26 display-layer translation
    STATE_DISPLAY_LABELS,
    STATE_INTERNAL_FROM_DISPLAY,
    TIER_DISPLAY_LABELS,
    TIER_INTERNAL_FROM_DISPLAY,
    display_state,
    display_tier,
)

# ---------------------------------------------------------------------------
# Page config — once per session
# ---------------------------------------------------------------------------
# Phase 31 — guarded so this script can be embedded as a page inside a
# parent Streamlit app (e.g. adfundmgmt.streamlit.app/CCQS) where the
# parent has already called set_page_config(). Streamlit raises
# StreamlitSetPageConfigMustBeFirstCommandError when called twice; we
# silently skip the second call in that case.
try:
    st.set_page_config(
        page_title="CCQS",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    # Either set_page_config was already called by a parent app, or we are
    # running before any other Streamlit command — either way, swallow and
    # continue. Standalone deploys hit the success branch.
    pass

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
df, snapshot_date = load_dashboard_data()
if df.empty:
    st.error("No CCQS data found. Run the pipeline to populate data/cache/.")
    st.stop()

# Regime context for Priority 3d display-layer warnings (no methodology change).
regime_ctx = load_regime_context()


# ---------------------------------------------------------------------------
# Sidebar filters (Leadership Tier + State only)
# ---------------------------------------------------------------------------
# Internal ordering preserved (classifier output uses these labels and
# STATE_WEIGHTS keys on them). Display strings are translated through
# compute.display_labels.{display_tier,display_state} (Phase 26).
TIER_ORDER = [
    "ELITE_LEADER", "STRONG_LEADER", "EMERGING_LEADER", "ESTABLISHED_LEADER",
    "STRONG_PERFORMER", "NEUTRAL", "WEAK_PERFORMER", "DETERIORATING", "WEAK_LAGGARD",
    "UNCLASSIFIED",  # Phase 11.C.1 — explicit catch-all for rows not matching any of the 9 main tiers
]
STATE_ORDER = ["TRENDING", "PULLBACK", "CONSOLIDATING", "EXHAUSTION", "DETERIORATING", "INDETERMINATE"]

tiers_present_internal = [t for t in TIER_ORDER if t in df["leadership_tier"].astype(str).unique()]
states_present_internal = [s for s in STATE_ORDER if s in df["primary_state"].astype(str).unique()]

# Phase 26 — present display strings in the multiselect, but filter the
# dataframe on internal labels. The reverse map (display → internal)
# disambiguates the user's selections back to the classifier vocabulary.
tiers_present_display = [TIER_DISPLAY_LABELS[t] for t in tiers_present_internal]
states_present_display = [STATE_DISPLAY_LABELS[s] for s in states_present_internal]

with st.sidebar:
    st.markdown("## Filters")
    selected_tiers_display = st.multiselect(
        "Leadership Tier",
        options=tiers_present_display,
        default=[],
        help="Restrict universe by leadership tier.",
    )
    selected_states_display = st.multiselect(
        "State",
        options=states_present_display,
        default=[],
        help="Restrict universe by primary state.",
    )

# Map back to internal labels for filtering against the parquet columns.
selected_tiers = [TIER_INTERNAL_FROM_DISPLAY[t] for t in selected_tiers_display]
selected_states = [STATE_INTERNAL_FROM_DISPLAY[s] for s in selected_states_display]

filtered = df.copy()
if selected_tiers:
    filtered = filtered[filtered["leadership_tier"].astype(str).isin(selected_tiers)]
if selected_states:
    filtered = filtered[filtered["primary_state"].astype(str).isin(selected_states)]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# Composite Chart Quality Score")
st.markdown(
    f"<div class='meta'>{snapshot_date} · {len(df):,} names scored · "
    f"{len(filtered):,} after filters</div>",
    unsafe_allow_html=True,
)

# Phase 18 — Market-context caution.
# Discrete banner: silent when the broad market is within its trending
# regime (SPY shallow drawdown and above its 200-day moving average), surfaced
# only when conditions warrant a measured caution. Professional, non-alarmist.
_ds = regime_ctx.get("ccqs_design_space", {}) if regime_ctx else {}
if _ds:
    _state = _ds.get("regime_state", "")
    _dd_pct = _ds.get("spy_dd_from_high", 0) * 100
    if _state == "YELLOW":
        st.info(
            f"**Caution — broad market below its 200-day moving average.** "
            f"SPY is {abs(_dd_pct):.1f}% from its 252-day high but trades "
            f"below its long-term trend. Treat readings as informational "
            f"and apply additional risk management to new positions.",
            icon="⚠️",
        )
    elif _state == "RED":
        st.warning(
            f"**Caution — broad market in a meaningful drawdown.** "
            f"SPY is {abs(_dd_pct):.1f}% below its 252-day high. "
            f"Cross-sectional rankings remain meaningful, but historical "
            f"behaviour suggests rankings are best used as a screening "
            f"aid rather than a directional signal in this environment.",
            icon="⚠️",
        )


# ---------------------------------------------------------------------------
# Tabs: Production / Sandbox
# ---------------------------------------------------------------------------
# Sandbox tab is hidden from production dashboard but the code, loader, and
# data/cache/sandbox/ artefacts are preserved as a regression harness.
# Flip to True to re-enable the tab without re-running the sandbox pipeline.
SHOW_SANDBOX = False

if SHOW_SANDBOX:
    tab_production, tab_sandbox = st.tabs(["Production", "Sandbox (SP500 Expansion)"])
else:
    tab_production = st.container()


with tab_production:
    # -----------------------------------------------------------------------
    # Section 1 — Top Stocks
    # -----------------------------------------------------------------------
    st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
    st.markdown("## Top Stocks")

    c1, c2 = st.columns([1, 5])
    with c1:
        n_top = st.selectbox("Rows", options=[25, 50, 100, 200], index=1, label_visibility="collapsed")

    top_df = filtered.sort_values("ccqs", ascending=False)
    st.plotly_chart(
        top_stocks_table(top_df, n=int(n_top)),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # -----------------------------------------------------------------------
    # Section 2 — Themes
    # -----------------------------------------------------------------------
    st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
    st.markdown("## Themes")
    themes_df = load_themes_data()
    st.plotly_chart(
        themes_table(themes_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # -----------------------------------------------------------------------
    # Section 3 — What Changed Today
    # -----------------------------------------------------------------------
    st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
    st.markdown("## What Changed Today")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("### Strongest Risers")
        st.plotly_chart(
            emerging_leaders_table(get_emerging_leaders_today(n=10)),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with col_b:
        st.markdown("### Largest Decliners")
        st.plotly_chart(
            newly_broken_table(get_newly_broken_today(n=10)),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with col_c:
        st.markdown("### Grade Changes")
        st.plotly_chart(
            grade_jumps_table(get_grade_jumps_today(n=10)),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # -----------------------------------------------------------------------
    # Section 4 — Stock Detail
    # -----------------------------------------------------------------------
    st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
    st.markdown("## Stock Detail")

    tickers_sorted = sorted(filtered.index.astype(str).tolist())
    if not tickers_sorted:
        tickers_sorted = sorted(df.index.astype(str).tolist())

    default_idx = tickers_sorted.index("NVDA") if "NVDA" in tickers_sorted else 0
    sel = st.selectbox("Ticker", options=tickers_sorted, index=default_idx)

    if sel in df.index:
        row = df.loc[sel]

        # Phase 18 — Option 2 stock detail header: labeled key-value chips
        # with a hierarchy. Ticker + score are large; categorical context
        # sits below as labeled chips so the eye reads "what is it scoring"
        # first, "where does it sit" second. Reliability chips removed —
        # CCQS is a technical system, not a predictive model; the user does
        # not need per-stock confidence framing.
        def _chip(label: str, value: str, color: str = "#374151",
                  bg: str = "#f3f4f6", border: str = "#e5e7eb") -> str:
            return (
                f"<span style='display:inline-block;padding:4px 10px;"
                f"margin:0 8px 6px 0;border:1px solid {border};background:{bg};"
                f"color:{color};border-radius:6px;font-size:0.85rem;"
                f"line-height:1.3;'>"
                f"<span style='color:#6b7280;margin-right:6px;font-size:0.78rem;"
                f"text-transform:uppercase;letter-spacing:0.04em;'>{label}</span>"
                f"<strong>{value}</strong></span>"
            )

        st.markdown(
            f"<div style='font-size:1.6rem;font-weight:600;color:#111827;"
            f"margin:0.25em 0 0.1em 0;'>{sel}</div>",
            unsafe_allow_html=True,
        )
        # Phase 26 — display-string translation at render boundary.
        # Internal label values remain unchanged in row['leadership_tier']
        # and row['primary_state']; only the chip text is translated.
        st.markdown(
            "<div style='margin-bottom:0.4em;'>"
            + _chip("Score", f"{row['ccqs']:.1f} ({row['grade']})")
            + _chip("Leadership Tier", display_tier(row['leadership_tier']))
            + _chip("State", display_state(row['primary_state']))
            + _chip("Theme", str(row['basket']))
            + "</div>",
            unsafe_allow_html=True,
        )

        # Phase 24 — partial-CCQS disclaimer. When `is_partial` is True the
        # score was computed by renormalizing state weights across the
        # components the ticker has accumulated; typical for recent IPOs
        # and spin-offs still inside the 504-day long-window-feature warmup.
        if bool(row.get("is_partial", False)):
            wp = float(row.get("weight_present", 1.0)) * 100.0
            nv = int(row.get("n_valid_components", 10))
            st.markdown(
                f"<div style='margin-bottom:0.8em;padding:8px 12px;"
                f"border-left:3px solid #d97706;background:#fef3c7;"
                f"border-radius:4px;font-size:0.85rem;color:#78350f;'>"
                f"<strong>Partial CCQS</strong> — computed from "
                f"{nv} of 10 components ({wp:.0f}% of state weight present). "
                f"This name has insufficient history for long-window features "
                f"(typical for IPOs / spin-offs in the ~2-year warmup); "
                f"score will converge to full-data as history accumulates."
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br/>", unsafe_allow_html=True)
        left, right = st.columns([3, 2])
        with left:
            st.markdown("### Component Contributions")
            st.plotly_chart(
                component_table(load_components_for_ticker(sel)),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with right:
            st.markdown("### Key Metrics")
            st.plotly_chart(
                key_metrics_table(load_key_metrics_for_ticker(sel)),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.markdown("### CCQS Trajectory")
        period_options = ["1W", "1M", "3M", "6M", "1Y", "3Y", "5Y", "INCEPTION"]
        period_sel = st.selectbox(
            "Period",
            options=period_options,
            index=period_options.index("6M"),
            label_visibility="collapsed",
            key=f"period_{sel}",
        )
        st.plotly_chart(
            ccqs_trajectory_chart(
                load_ticker_history(sel, period=period_sel),
                grade_thresholds=load_grade_thresholds_history(period=period_sel),
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown("### Basket Peers")
        basket = row.get("basket")
        if isinstance(basket, str) and basket != "—":
            # Phase 30.2 — use all tagged members of the basket (primary +
            # tag), not just tickers whose PRIMARY = basket. Otherwise a
            # solo-primary basket like Magnificent Seven (only AAPL primary)
            # would render its own selected ticker as the only peer. By
            # pulling all tagged members we show the full cohort the basket
            # represents.
            from data.universe import tickers_tagged
            members = set(tickers_tagged(basket))
            peers = df[df.index.isin(members)].sort_values("ccqs", ascending=False).head(10).copy()
            # Phase 30.4 — every peer row is, by definition, a member of
            # this basket; override the per-ticker "basket" column (which
            # stores each ticker's PRIMARY) so the Theme column reflects the
            # basket being viewed. Without this, AAPL's Mag7 peer list
            # showed NVDA tagged "AI Compute", TSLA tagged "Electric
            # Vehicles", MSFT/META/AMZN/GOOGL tagged "Hyperscalers" —
            # visually scrambled even though all 7 are genuine Mag7 peers.
            peers["basket"] = basket
        else:
            peers = df.head(0)
        st.plotly_chart(
            peers_table(peers, current_ticker=sel),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # -----------------------------------------------------------------------
    # Section 5 — System Health (expander)
    # -----------------------------------------------------------------------
    st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
    with st.expander("System Health & Methodology", expanded=False):
        st.markdown("### Out-of-Sample IC · Composite CCQS")
        st.plotly_chart(
            oos_ic_table(load_oos_metrics()),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown("### Methodology")
        st.markdown(
            """
**CCQS** is a per-ticker composite of 10 standardized components: relative
strength vs SPY, RS leadership, RS line behaviour, trend slope, chart
structure, multi-timeframe alignment, extension, residual momentum,
oscillator momentum, and volume pattern.

Each component is z-scored cross-sectionally per date, combined with
state-conditional weights, and Bayesian-averaged across the six states.
The composite is mapped to 0–100 via the standard-normal CDF, winsorized
at the 1st / 99th percentiles, and graded by per-date quantile cuts
(top 8% → S, next 12% → A, etc.).

**Component contributions** are z × weight under the ticker's primary
state. Components with zero weight in that state are hidden — they
contribute nothing to that name's CCQS.

**Out-of-sample IC** is the Spearman rank correlation between today's CCQS
and forward returns, evaluated on data the model never saw. CCQS shows the
strongest signal at the 60d and 126d horizons. A t-statistic above 2.0
indicates the signal is distinguishable from noise.

See `SPEC.md` for the full methodology, weight tables, and walk-forward
validation.
            """
        )


# ---------------------------------------------------------------------------
# Sandbox tab — parallel pipeline on SP500-expanded universe
# Hidden behind SHOW_SANDBOX flag. Imports/loader/cache remain intact so the
# regression harness keeps working from CLI; only the UI surface is gated.
# ---------------------------------------------------------------------------
if SHOW_SANDBOX:
    with tab_sandbox:
        sb_df, sb_snapshot = load_sandbox_dashboard_data()
        sb_diag = load_sandbox_diagnostics()
        sb_validation = load_sandbox_validation_status()

        if sb_df.empty:
            st.warning(
                "No sandbox data found. Run the sandbox pipeline to populate "
                "data/cache/sandbox/:  \n"
                "1. `python -m compute.sandbox.fetch_sp500`  \n"
                "2. `python -m compute.sandbox.pipeline_sandbox`  \n"
                "3. `python -m compute.sandbox.validate_sandbox`"
            )
        else:
            # ---- Header --------------------------------------------------------
            pm = sb_diag.get("pipeline_meta", {})
            ms = sb_diag.get("missing_equities_summary", {})
            qs = sb_diag.get("quality_status", {})
            n_total = pm.get("n_tickers_total", 0)
            n_prod = pm.get("n_tickers_production", 0)
            n_sb_only = pm.get("n_tickers_sandbox_only", 0)
            st.markdown(
                f"<div class='meta'>{sb_snapshot} · {n_total:,} names scored "
                f"({n_prod} production + {n_sb_only} SP500-only)</div>",
                unsafe_allow_html=True,
            )

            # ---- Sub-section A: Pipeline / Universe Summary --------------------
            st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
            st.markdown("## Sandbox Build Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Universe Expansion**")
                st.markdown(
                    f"- SP500 total: **{ms.get('sp500_total', 0)}**  \n"
                    f"- REITs excluded: **{ms.get('reits_excluded', 0)}**  \n"
                    f"- SP500 non-REIT: **{ms.get('sp500_after_reit_filter', 0)}**  \n"
                    f"- In production already: **{ms.get('in_both', 0)}**  \n"
                    f"- Missing equities: **{ms.get('missing_equities_count', 0)}**"
                )
            with col2:
                st.markdown("**Sandbox-only Quality**")
                st.markdown(
                    f"- Quality PASS: **{qs.get('sandbox_only_pass', 0)}**  \n"
                    f"- Quality WARNING: **{qs.get('sandbox_only_warning', 0)}**  \n"
                    f"- Quality FAIL: **{qs.get('sandbox_only_fail', 0)}**"
                )
            with col3:
                st.markdown("**Validation**")
                if sb_validation:
                    checks = sb_validation.get("checks", {})
                    overall = "PASS" if sb_validation.get("all_pass") else "FAIL"
                    st.markdown(f"- Overall: **{overall}**")
                    for name, r in checks.items():
                        status = "PASS" if r.get("pass") else "FAIL"
                        st.markdown(f"  - `{name}`: {status}")
                else:
                    st.markdown("- _validation report not present_")

            # ---- Sub-section B: Top 50 Sandbox-Only Stocks ---------------------
            st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
            st.markdown("## Top Sandbox-Only Stocks")
            st.markdown(
                "<div class='meta'>Stocks present only because of the SP500 expansion "
                "— not in the production ~892-name universe.</div>",
                unsafe_allow_html=True,
            )
            sb_only_top = load_sandbox_only_top_stocks(n=50)
            if sb_only_top.empty:
                st.info("No sandbox-only tickers in the latest snapshot.")
            else:
                st.plotly_chart(
                    top_stocks_table(sb_only_top, n=50),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            # ---- Sub-section C: Production vs Sandbox (methodology stability) --
            st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
            st.markdown("## Methodology Stability — Production vs Sandbox")
            st.markdown(
                "<div class='meta'>Top 20 production names by CCQS, scored under both "
                "the production and sandbox universes. Δ should be small (universe "
                "expansion shifts cross-sectional z's only slightly).</div>",
                unsafe_allow_html=True,
            )
            cmp_df = load_sandbox_comparison_stocks(anchors=None)
            if cmp_df.empty:
                st.info("No comparison data available.")
            else:
                mean_abs = float(cmp_df["abs_delta"].mean())
                max_abs = float(cmp_df["abs_delta"].max())
                st.markdown(
                    f"**Mean |Δ| = {mean_abs:.2f}   ·   Max |Δ| = {max_abs:.2f}**"
                )
                st.dataframe(
                    cmp_df.assign(
                        ccqs_prod=cmp_df["ccqs_prod"].round(2),
                        ccqs_sandbox=cmp_df["ccqs_sandbox"].round(2),
                        delta=cmp_df["delta"].round(2),
                        abs_delta=cmp_df["abs_delta"].round(2),
                    ),
                    use_container_width=True,
                )

            # ---- Sub-section D: Sandbox Themes ---------------------------------
            st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
            st.markdown("## Themes (Production + SP500 GICS Baskets)")
            sb_themes = load_sandbox_themes_data()
            if sb_themes.empty:
                st.info("No theme aggregates available.")
            else:
                st.plotly_chart(
                    themes_table(sb_themes),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            # ---- Sub-section E: Sector-specific visibility ---------------------
            st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
            st.markdown("## Sector-Specific Visibility (SP500 GICS Baskets)")
            st.markdown(
                "<div class='meta'>Top 10 names per SP500 GICS basket — sectors where "
                "production coverage was thin (utilities, materials, staples) gain "
                "the most.</div>",
                unsafe_allow_html=True,
            )
            sb_basket_focus = [
                "SP500_UTILITIES",
                "SP500_MATERIALS",
                "SP500_CONSUMER_STAPLES",
            ]
            sec_cols = st.columns(len(sb_basket_focus))
            for col, b in zip(sec_cols, sb_basket_focus):
                with col:
                    st.markdown(f"**{b}**")
                    top_b = load_sandbox_top_by_basket(b, n=10)
                    if top_b.empty:
                        st.markdown("_no data_")
                    else:
                        st.plotly_chart(
                            top_stocks_table(top_b, n=10),
                            use_container_width=True,
                            config={"displayModeBar": False},
                        )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    "<div class='footer'>© 2026 AD Fund Management LP</div>",
    unsafe_allow_html=True,
)
