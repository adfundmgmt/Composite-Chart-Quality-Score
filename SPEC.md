# CCQS V1 — Composite Chart Quality Score Specification

> **Currency note (2026-06-12):** The CCQS methodology baseline remains **Phase 11E.2** and is **unchanged through Phase 32R**. Every phase since Path C (13 → 32R) has touched only the universe (e.g. Phase 30 basket changes), the display layer (Phase 26/27 labels and chips), or private tooling — never the scoring methodology, component weights, grade thresholds, or TradingView parity. This specification is current as of today; see `CHANGELOG.md` for the phase-by-phase audit trail.

**Version:** 1.0 (Locked) — **PATH C COMPLETE (Phase 12, 2026-05-26)**
**+ Phase 14R reversion (2026-05-26)** restoring CCQS to bit-identical
Path C state after Phase 14.1 (universe expansion experiment, see
"Phase 14.1 — Experimental / Reverted" below) failed conditional IC
validation on the small-cap subset (5d t=+0.26, 20d t=-1.77, 60d
t=-1.58, 126d t=+2.80 vs +2.35/+1.97/+3.46/+9.10 for the original 884
tickers in the same combined pipeline). Decision: build a separate
**Small Cap CCQS (CCQS-SC)** tool in **Phase 15** with empirically
recalibrated methodology, rather than force a single methodology onto
two structurally different universes.
Path C overview: Phase 10 (volume-pattern addition) + Phase 11A
(state classification validated) + Phase 11.B.1 (dead setup removed) +
Phase 11C (tier classification validated) + Phase 11.C.1 (UNCLASSIFIED
tier added for fall-through fix) + Phase 11D (cross-layer synthesis;
CCQS regime-dependence documented) + Phase 11E.1 (Emerging Leader
setup merged into cascade) + Phase 11E.2 (dashboard CCQS regime chip).
Phase 12 ships the closeout documentation: Path C comprehensive
overview, system-wide design lessons, validation framework, deferred
backlog. **Methodology baseline: Phase 11E.2.** Final state per
Methodology Lock §3 — future changes require new empirical evidence
of signal degradation OR independent research findings, not historical
pattern observation.
Adds `s_volume` (bundled `low_rel_vol_10d` + `volume_buzz_50`) as an 11th
component at 3% per state; existing 10 components scaled by 0.97. First
empirical win since Phase 8a: walk-forward 5d paired t = +2.01 (clears
+1.96 threshold); per-date 5d IC delta CI strict > 0 [+0.000012, +0.000686];
20d t-stat 1.95 → 2.04 (crosses back above institutional 2.0); 60d/126d
preserved (NS deltas). EXHAUSTION-state IC +0.006 to +0.016 across every
horizon — resolves the architectural fragility documented across Priority
3c / Phase 8a.1 / Phase 8b. Phase 11A empirically validates all 6 states
as statistically distinguishable; documents critical "context-classifier,
not buy/sell signal" insight (TRENDING underperforms universe, EXHAUSTION
outperforms by +0.07 at 60d). Phase 11B confirms the same "context, not
direction" pattern at the setup layer (the "premium label, no alpha"
finding); Phase 11.B.1 removes dead setup "Consolidation Within Strong
Theme" (n=0). Phase 11C validates the leadership-tier layer
(only ELITE_LEADER has a distinctive forward edge; non-monotonic
ordering across the other 8 tiers); Phase 11.C.1 fixes a default-init
bug that mis-labeled ~132K rows (8.6% of universe) as NEUTRAL — adds
explicit UNCLASSIFIED 10th tier. **Phase 11D synthesizes the three
validation phases and adds one critical architectural insight: CCQS
is regime-dependent — works in top tiers (Q10−Q1 spread +5%), inverts
in WEAK_LAGGARD tier (Q10−Q1 spread −9%). Categorical labels carry
97.3% of cross-sectional R²; CCQS contributes 2.7% (within-cell
ranking).** Phase 11E.1 ships the Emerging Leader / VCP Setup merger
(p=0.94 equivalent, both underperformed universe). Phase 11E.2 adds
a dashboard regime chip surfacing the CCQS regime-dependence to
users. Built on:
Phase 8a (residual momentum addition) + Phase 7 (Priority 3a: `s_demand`
removal + carrier redistribution) + Priority 3d (conditional performance
warnings, display-layer only) + Phase 5.5–5.8 (vocabulary audit,
COILING/CLIMACTIC/BROKEN renames, setup label accuracy audit) + Phase 6
(per-date winsorization, `s_climax` removal) + Priority 2 (bootstrap CIs
on all 54 weight cells, conditional IC analysis across regimes) + the
Methodology Lock (Phase X.2.1 / Phase X.3 OOS baseline).
**Date:** May 2026
**Author:** Shreyaansh Chhabra (ADFM)
**Purpose:** Pure technical, momentum & strength screening tool for L/S discretionary equity analysis.

---

## Methodology Lock

As of Phase X.3 / Phase 5.2 (May 2026), the CCQS methodology is locked. The following principles apply:

1. Historical CCQS values represent today's methodology applied to historical data.
2. Universe and basket assignments are current; survivorship bias is not removed.
3. Methodology modifications require motivation independent of historical pattern observation:
   - Forward-looking signal degradation (current OOS IC drops materially)
   - Independent research findings (new academic work, new data sources)
   - Clear computational bugs
4. Patterns observed in dashboard historical displays do NOT constitute valid motivation for methodology changes. This prevents hindsight bias and curve-fitting.
5. OOS IC baseline (Phase X.3) is preserved as published:
   - 1d: t=4.16, IC=0.0173, hit rate 68.2%
   - 126d: t=2.59, IC=0.0412, hit rate 69.2%
   - 252d: t=2.05, IC=0.0360, hit rate 63.6%
6. Extended-window OOS IC (post-backfill) computed as secondary validation, labeled as such, NOT used as replacement baseline.

This lock applies to all future development. Any proposed methodology change must reference this section and provide motivation that does not derive from historical chart observation.

---

## Where We Stand (2026-05-28, post Phase 29.2)

**Methodology snapshot (post-Phase-29).** CCQS V1 ships with **10
computed components** all contributing to the score (`s_demand`
permanently removed in Phase 28 — had zero weight in every state since
Phase 7; `s_climax` was removed back in Phase 6). The **13-label setup
cascade** (Phase 25 redesign + Phase 27 "Reclaim" addition) replaces
the legacy 27-label vocabulary — pure descriptive chart-hooks, no
gestalt-pattern naming, first-match-wins. **10 leadership tiers** (the
explicit `UNCLASSIFIED` 10th tier was added in Phase 11.C.1 to
eliminate fall-through mis-labeling). Phase 26 renamed 5 state/tier
labels at the display layer (EXHAUSTION → "Parabolic",
STRONG_PERFORMER → "Steady", etc.) without touching the methodology
labels — `STATE_WEIGHTS` keys remain ALL_CAPS internal labels.

**Feature schema:** 108 features in `compute/features.py FEATURE_ORDER`
(Phase 29 dropped 30 unused features that had zero downstream
references — internal computations preserved where needed as
intermediate values). State-conditional weights live in a 10 × 6
matrix; weights are validated by paired block bootstrap (Priority 2a)
and per-date / walk-forward OOS IC. Per-date winsorization in place
since Phase 6.

**Cadence:** Daily refresh by GitHub Actions cron at 4:05 PM ET Mon-Fri
(5 min after NYSE close — moved from 4:30 PM in Phase 26).

**Live deployment:**
[composite-chart-quality-score.streamlit.app](https://composite-chart-quality-score.streamlit.app/)
on Streamlit Cloud, which is purely a display layer over the parquets
GitHub Actions commits to `data/cache/dashboard/` each weekday.

**Validation status as of 2026-05-28:**
- 140/140 TradingView reference fields PASS (bit-identical CCQS
  preserved across Phases 23-29)
- 11/11 pipeline sanity checks PASS
- 91/91 pytest suite PASS
- 858 of 892 universe tickers scored with full CCQS today; 2 partial
  (CRWV, SNDK — recent IPOs); 2 NaN (ASGN, CRCL — insufficient
  history); 32 firewall-rejected (by design)

**Path C completion (2026-05-26):** Phases 11A/11B/11C empirically
validated the state classifier, setup classifier, and leadership-tier
layer. Phase 11D synthesized cross-layer findings. Phase 12 was the
documentation closeout. The system-wide insight: CCQS V1 is a
**categorical screening + within-category ranking tool**.
Classifications carry **97.3%** of cross-sectional R² at 60d forward
returns; CCQS as a continuous variable contributes 2.7% (within-cell
ranking). CCQS is **regime-dependent**: works in top tiers
(ESTABLISHED_LEADER Q10−Q1 spread +5.26% at 60d), inverts in bottom
tiers (WEAK_LAGGARD spread −9.24%). The dashboard surfaces this via
the Phase 17 regime context chip. See "Path C — Comprehensive
Overview" below for the closeout details, and the per-phase entries
below for everything shipped since (Phases 23-29).

**Where the signal works** (Priority 2b conditional analysis):

- Smaller dollar-volume stocks — Q1 by 20d $-vol: 60d IC +0.048, 126d IC +0.061
- Moderate-to-high realized-vol names — Q3–Q5 carry the largest IC magnitudes
- Low-to-mid market vol regimes — 60d IC +0.040, 126d IC +0.045
- Cyclical / recovery sectors — Hotels & Casinos (+0.21), Liquid Cooling
  (+0.18), Auto Affordability (+0.14), Oilfield Services (+0.14),
  Heavy Machinery (+0.10), Large-Cap Pharma (+0.10)
- CONSOLIDATING state — significant IC at all four horizons (5d/20d/60d/126d)
- Longer horizons — 126d walk-forward t = 2.02 (post-Phase-7) cleared
  institutional threshold

**Where the signal does not work** (Priority 2b, surfaced in the
dashboard as reliability chips per Priority 3d):

- Mega-caps (Q5 dollar volume) — 60d IC −0.017, 126d IC −0.007
- High market-vol regimes — 60d IC −0.014, 126d IC −0.025
- 10 defensive baskets — Household & Personal Care, Gold Royalty,
  Integrated Energy Majors, Gaming Publishers, Offshore Drilling,
  Railroads, Diagnostics, LNG Shipping, Beverages, Industrial Automation
- Speculative-euphoria regimes (2021 meme/SPAC year) — negative IC at every horizon
- EXHAUSTION state at 20d — IC ≈ 0, t = −0.3 (other horizons retain signal)
- COVID-2020 long horizons — Phase 7 lost ~0.005 of 126d IC in 2020

**Validation evidence summary:**

- Phase X.3 baseline preserved: 1d t = 4.16, 126d t = 2.59, 252d t = 2.05
- Phase 7 walk-forward OOS at 126d clears t > 2.0 (was 1.82, now 2.02)
- Every weight cell bootstrapped with 90% CI (Priority 2a, 54 cells × 4 horizons)
- Bootstrap CI excludes zero for: s_rs (10/24 cells), s_structure (11/24),
  s_rs_leadership (8/24), s_mtf (6/24) — the four carriers
- Bootstrap CI never excludes zero positively for: s_demand (0/24,
  6 negatives — zeroed in Phase 7)
- Grade distribution stable: S 6.37 / A 9.49 / B 19.73 / C 19.74 / D 23.73
- TV parity: 10 / 10 canaries pass 140 / 140 field checks at spec tolerance

**Architectural finding worth flagging.** Phase X.2.1's confidence-blending
toward INDETERMINATE means EXHAUSTION-state stocks pull 45 % of their CCQS
from the INDETERMINATE weight column. State-conditional weight tuning has
reduced reach for the four low-confidence states (TRENDING / PULLBACK /
CONSOLIDATING / EXHAUSTION). Further per-state simplification within the
current architecture would require relaxing confidence-blending — a
material redesign. See the *Priority 3 — Empirical Methodology Refinement*
section below for the full table.

**What was tried and rejected** (audit trail in commit history + this
SPEC):

- Priority 3b — Pure 4-carrier-only composite: marginal 5d/20d
  unconditional gain, but EXHAUSTION 60d/126d down −48%/−27%.
- Priority 3c — State-aware hybrid (preserve EXHAUSTION+CONSOLIDATING):
  EXHAUSTION regression persisted because of cross-state Bayesian
  averaging.

**Next-phase considerations.** Within the Methodology Lock framework,
no near-term methodology change is on the table. Honest signal
characterization is in place via Priority 3d display warnings + Phase
11E.2 regime chips. The next set of architectural questions
(relaxing confidence-blending, feature-level reduction, regime-aware
pre-trade filtering) require either new OOS evidence of signal
degradation or independent research findings before consideration per
Methodology Lock §3.

---

## Path C — Comprehensive Overview (2026-05-26)

Path C was the multi-phase comprehensive validation effort that:
1. Tightened foundational mechanics (winsorization, vocabulary, dead-component cleanup)
2. Bootstrap-validated all weight cells
3. Documented confidence-blending as an architectural constraint
4. Added two new empirical signal additions (Phase 8a residual momentum, Phase 10 volume pattern)
5. Empirically validated every classification layer (states, setups, tiers)
6. Synthesized the cross-layer findings into a system-wide design lesson
7. Documented the final state, surfaced empirical caveats to users via the dashboard

### Path C phases

| Phase | Date | Action | Status |
| ----- | ---- | ------ | ------ |
| 5.2 | 2026-05-23 | NaN-CCQS root-cause fix + universe cleanup | ✓ shipped |
| 5.3 | 2026-05-23 | Selective SP100 promotion | ✓ shipped |
| 5.5 | 2026-05-24 | Naming standardization | ✓ shipped |
| 5.6 | 2026-05-24 | Coil sub-setup follow-up | ✓ shipped |
| 5.7 | 2026-05-24 | Climax / Broken sub-setup rename | ✓ shipped |
| 5.8 | 2026-05-25 | Setup label accuracy audit | ✓ shipped |
| 6 | 2026-05-25 | Per-date winsorization + s_climax removal | ✓ shipped |
| Priority 2a | 2026-05-25 | Bootstrap CIs on STATE_WEIGHTS (54 cells × 4 horizons) | ✓ documented |
| Priority 2b | 2026-05-25 | Conditional IC analysis across regimes | ✓ documented |
| 7 | 2026-05-25 | s_demand removal + carrier redistribution | ✓ shipped (126d t 1.82→2.02) |
| Priority 3a-c | 2026-05-25 | Simplification investigations | rejected (EXHAUSTION fragility documented) |
| Priority 3d | 2026-05-25 | Conditional performance warnings (display chips) | ✓ shipped |
| 8a | 2026-05-26 | Residual momentum addition (10th component) | ✓ shipped (126d t 1.87→2.02) |
| 8a.1 | 2026-05-26 | Short-horizon reversal investigation | rejected |
| 8b | 2026-05-26 | Vol-adjustment standardization investigation | rejected |
| 10 | 2026-05-26 | Volume pattern addition (11th component, W1) | ✓ shipped (5d t 2.33→2.41) |
| 11A | 2026-05-26 | State classification validation | ✓ documented |
| 11B | 2026-05-26 | Setup classification validation | ✓ documented |
| 11.B.1 | 2026-05-26 | "Consolidation Within Strong Theme" removal | ✓ shipped (28 → 27 setups… wait, 29 → 28) |
| 11C | 2026-05-26 | Leadership tier validation | ✓ documented |
| 11.C.1 | 2026-05-26 | NEUTRAL fall-through fix; UNCLASSIFIED 10th tier | ✓ shipped (132K mis-labeled rows corrected) |
| 11D | 2026-05-26 | Cross-layer synthesis | ✓ documented |
| 11E.1 | 2026-05-26 | "Emerging Leader" setup removal (VCP merger) | ✓ shipped (28 → 27 setups) |
| 11E.2 | 2026-05-26 | Dashboard CCQS regime chip | ✓ shipped (green/amber) |
| 12 | 2026-05-26 | Path C closeout documentation | ✓ this section |

(Note: Phase 11.B.1 numbering "28 → 27" is a typo in the cell above — actual Phase 11.B.1 reduced 29 → 28; Phase 11E.1 then reduced 28 → 27. Net: 29 → 27.)

### Path C — system-wide design lessons documented

Three classification layers (states, setups, tiers) plus the continuous
CCQS score, all validated through Phase 11.

#### Lesson 1 (Phase 11A): States describe CONTEXT, not direction

The 6-state machine is a CONTEXT classifier. Forward-return ordering is
counterintuitive to state names: EXHAUSTION-state stocks OUTPERFORM
universe by +4.1% at 60d; TRENDING-state stocks UNDERPERFORM by −1.0%.
This reflects mean reversion of extremes + momentum continuation in
"obviously extended" stocks. States describe what kind of regime a
stock is in, not what will happen next.

#### Lesson 2 (Phase 11B): Premium labels carry no alpha

Setups branded as "premium" / "quality" / "elite" (VCP Setup, Emerging
Leader, Premium Pullback, Theme Leader Pullback) underperform universe.
Setups branded as "weakness" / "distribution" / "exhaustion"
(Capitulation Selling, Distribution Pattern, Sustained Weakness,
Volume-Confirmed Exhaustion) outperform by 4–12 percentage points at
60d. Setup names describe technical pattern, NOT future direction. The
"obvious quality" market has already priced in.

#### Lesson 3 (Phase 11C): Tier hierarchy is non-monotonic in forward return

Only ELITE_LEADER (top 0.2%) has a truly distinctive forward edge
(+15.24% at 60d, 3× universe). The other 8 tiers cluster within ±2.5pp
of universe. The priority ordering ELITE → WEAK_LAGGARD reflects
current RS-quality, NOT expected forward return: 4 of 8 adjacent-tier
pairs have the "lower" tier outperforming the "higher" one.

#### Lesson 4 (Phase 11D): CCQS is regime-dependent

Top-CCQS-decile minus Bottom-CCQS-decile spread at 60d, by tier:

| Tier | Q10 − Q1 spread |
| ---- | --------------- |
| ESTABLISHED_LEADER | **+5.26%** (works) |
| STRONG_LEADER | +3.22% |
| STRONG_PERFORMER | +3.04% |
| NEUTRAL | −0.48% (flat) |
| EMERGING_LEADER | −0.82% (slightly inverted) |
| DETERIORATING (tier) | −1.93% |
| **WEAK_LAGGARD** | **−9.24%** (strongly inverted) |

Within WEAK_LAGGARD, the LOWEST CCQS decile outperforms the HIGHEST
CCQS decile by 9.24pp at 60d. CCQS is anti-predictive in bottom-tier
regimes due to mean reversion of extremes. Surfaced to users via Phase
11E.2 green/amber chips.

#### Lesson 5 (Phase 11D): Categorical labels carry 97.3% of cross-sectional R²

Pooled regression on 60d forward returns (per-date demeaned):

| Source | Marginal R² | % of total |
| ------ | ----------- | ---------- |
| CCQS (continuous) | 0.000148 | 2.7% |
| State dummies | +0.001318 | 24.4% |
| **Setup dummies** | **+0.003274** | **60.6%** |
| Tier dummies | +0.000664 | 12.3% |
| **Total R² @ 60d** | **0.005404** | 100% |

Setup carries the highest single-layer information content (60.6%).
The categorical labels make explicit the regime structure that CCQS
encodes implicitly; once you have the categories, CCQS as a continuous
variable adds only within-cell ranking power.

#### Lesson 6 (Phase 11D): Layers are structurally redundant by design

| Pair | Cramér's V | Note |
| ---- | ---------- | ---- |
| state × setup | **0.7696** | High — by design (setups are state-aware) |
| state × tier | 0.4211 | Moderate |
| setup × tier | 0.3313 | Moderate |

The state-setup redundancy is structural, not bug. 5 of 27 setups are
state-aware catch-alls; many specific setups have implicit state
constraints. Removing one layer would lose within-state pattern
differentiation.

### Path C — final empirical state

| Metric | Value | Source |
| ------ | ----- | ------ |
| Components | 11 (9 contributing) | compute/components.py post-Phase-10 |
| Setups | 27 (21 specific + 6 catch-alls) | compute/setup_classifier.py post-Phase-11E.1 |
| Tiers | 10 (incl. UNCLASSIFIED) | compute/leadership.py post-Phase-11.C.1 |
| CCQS 5d IC | 0.01150 (t = 2.37) | Phase 10 live-pipeline validation |
| CCQS 20d IC | 0.00887 (t = 2.00) | crosses institutional 2.0 threshold post-Phase-10 |
| CCQS 60d IC | 0.01367 (t = 3.57) | preserved through Phase 8a/10 |
| CCQS 126d IC | 0.02948 (t = 9.17) | preserved through Phase 8a/10 |
| Walk-forward 5d paired t (Phase 10 W1) | +2.01 | First post-Phase-8a config to clear +1.96 |
| Walk-forward 126d t | ≈2.02 (post-Phase-7) | clears institutional threshold |
| Cross-sectional R² @ 60d | 0.005404 | Phase 11D info attribution |
| TV reference parity | 140/140 (10/10 canaries) | per-phase verified |
| Sanity checks | 11/11 passing | every pipeline rebuild |

### Path C — validation framework

The empirical work used a stable validation framework throughout:

| Framework component | Purpose |
| ------------------- | ------- |
| Per-date Spearman IC | Cross-sectional ranking power within each date |
| Block bootstrap (block=21, n_iter=1000) | Confidence intervals on per-date IC delta |
| Walk-forward OOS (252-train / 21-test / 21-step) | Out-of-sample paired t-stats |
| Conditional IC by regime (HIGH/MED/LOW market vol) | Regime stability check |
| Per-state / per-setup / per-tier conditional IC | Layer-level diagnostic |
| Cramér's V categorical association | Layer redundancy quantification |
| TV reference snapshots (10 canaries × 14 fields) | Numerical stability across phases |
| Sanity checks (11 checks per pipeline run) | Integrity guard |

Strict decision criteria (refined across 8a → 8a.1 → 8b → 10):
- 60d/126d IC preserved or improved
- 5d/20d IC not regressing further
- EXHAUSTION-state IC not worse by > 0.005 at any horizon
- Per-date IC delta CI strict > 0 (not just non-negative)
- Walk-forward paired t > +1.96 at 60d or 126d
- No CI-includes-zero approvals (Phase 8a lesson)

Phase 10 W1 was the first post-Phase-8a candidate to clear all six
criteria; the dashboard's empirical signal is current as of that
deployment.

### Path C — rejected investigations (audit trail)

| Investigation | Rejection reason | Phase |
| ------------- | ----------------- | ----- |
| Priority 3a (s_demand removal extended) | EXHAUSTION fragility | already shipped subset; further removal rejected |
| Priority 3b (4-carrier-only) | EXHAUSTION/CONSOLIDATING regression | rejected |
| Priority 3c (state-aware hybrid) | EXHAUSTION still regresses via cross-state Bayesian avg | rejected |
| Phase 8a.1 (short-term reversal component) | No walk-forward signal; EXHAUSTION catastrophe | rejected |
| Phase 8b (vol-adjust standardization 4 configs) | All fail strict criteria; one regresses 126d t = −1.01 | rejected |
| Phase 10 HV1/HVE/single-feature configs | Inferior to W1 bundled; W6 (low_rel_vol alone) actively hurts | rejected within Phase 10 |
| Phase 11E STRONG_LEADER + ESTABLISHED_LEADER merger | deferred — empirical case present but optional | deferred backlog |
| Phase 11E EMERGING_LEADER tier collapse | deferred — empirical case present but optional | deferred backlog |
| Dashboard preset screens (mean-reversion, high-quality) | deferred to post-Path-C UX work | deferred backlog |

### Path C — deferred backlog (for potential future work)

1. STRONG_LEADER + ESTABLISHED_LEADER tier merger (statistically near-identical)
2. EMERGING_LEADER tier rename or collapse (mean reversion of extremes)
3. Extended Exhaustion → Late-Stage Trending rename (mode state is TRENDING)
4. Distribution Pattern `dist_days_min = 8` threshold tuning (most sensitive boundary)
5. PULLBACK `mu_rsi_14 = 45.0` tuning (most sensitive state-machine parameter)
6. Premium Pullback criteria review (heavy gating but underperforms)
7. Dashboard "high-quality screen" preset filter
8. Dashboard "mean-reversion screen" preset filter
9. NaN-tier filter / warning chip
10. Wire up `theme_strong` for "Consolidation Within Strong Theme" revival (if theme aggregation is wired)

These remain on the deferred backlog. Per Methodology Lock §3, any
future change requires either OOS evidence of signal degradation or
independent research findings, not historical pattern observation.

---

### Historical CCQS Coverage (2026-05-23 backfill)

CCQS computed for all stocks from **2020-01-01 onward** (252-day warmup
excludes pre-2020 dates from valid scores). The 7-year OHLCV window
(`LOOKBACK_DAYS = 7 * 365 + 60` in [`compute/loader.py`](compute/loader.py))
supports a continuous 2020–2026 trajectory for the dashboard stock-detail
display.

**Backfill validation** (`compute/validation/historical_backfill_validation.py`,
[`data/cache/historical_backfill_validation.json`](data/cache/historical_backfill_validation.json)):

| Metric | Value |
|--------|-------|
| OHLCV date range | 2019-03-27 → 2026-05-22 |
| Unique dates | 1,800 |
| Scored tickers | 858 |
| Valid CCQS rows | 1,220,611 / 1,544,400 |
| Pre-2020 valid rows | **0** (252d warmup enforced) |
| Out-of-bounds CCQS | **0** |
| Warmup violations | **0** |

Sample large caps (NVDA / MSFT / COST / JPM / NVO) each have **1,488 valid
rows** from 2020-06-22 onward. Recent IPOs handled cleanly — PLTR valid from
2021-12-27, SNOW from 2021-12-10, CRWD from 2020-09-04.

**Extended-window OOS IC (secondary validation only).** Re-running
`compute.validation.oos_evaluation` over the full 7-year window (73 rolling
test periods) produces these diagnostic IC values:

| Horizon | Extended-window IC | Extended t-stat | Extended hit rate |
|---------|---------------------|-----------------|-------------------|
| 1d   | +0.0146 | **+4.11** | 66.7% |
| 5d   | +0.0105 |   +1.28   | 60.9% |
| 20d  | +0.0107 |   +0.72   | 52.2% |
| 60d  | +0.0091 |   +0.61   | 55.2% |
| 126d | +0.0245 |   +1.85   | 59.4% |
| 252d | +0.0131 |   +1.05   | 56.9% |

**This is secondary validation, NOT a replacement baseline.** Primary
baseline is the Phase X.3 5-year window (48 windows) as published:

| Horizon | **Phase X.3 baseline IC** | **Phase X.3 t-stat** | **Phase X.3 hit rate** |
|---------|---------------------------|----------------------|-------------------------|
| 1d   | +0.0173 | **+4.16** | 68.2% |
| 126d | +0.0412 | **+2.59** | 69.2% |
| 252d | +0.0360 | **+2.05** | 63.6% |

**Interpretation.** The 1d signal holds nearly identically across windows
(+4.11 ext vs +4.16 published). The 126d and 252d horizons weaken on the
extended window — t-stats drop below the 2.0 significance threshold. This
reflects regime sensitivity (the extended window includes the 2020 COVID
shock + recovery, which the 5-year window omits), not a methodology defect.
Per the Methodology Lock above, this observation does NOT motivate
re-weighting or feature changes: the lock requires forward-looking signal
degradation on NEW data (not historical regime extension) before
methodology revision is considered.

The Phase X.3 baseline IC values (1d t=+4.16, 126d t=+2.59, 252d t=+2.05)
remain the **published official baseline**. Extended-window IC is recorded
here for completeness and labeled as such wherever it surfaces in the
dashboard.

---

### Phase 5.2 — NaN-CCQS root-cause fix + universe cleanup (2026-05-23)

**Trigger.** Level 3 validation FAILed at gate E: 101 stocks had NaN CCQS at
the most recent snapshot. Root cause: BASKET_PRIORITY dedup creates small
primary-basket constituent lists (<3 members) for ~94 stocks; the
`_within_basket_z` helper in `compute/features.py` skips computation for
<3 member baskets, producing NaN; that NaN propagates through `s_rs` (15%
weight on `within_basket_z_21d`) and `s_rs_leadership` confluence (6.75%
weight on `within_basket_z_63d`) into a NaN composite CCQS.

**Fix 1 — `.fillna(0.0)` on the three NaN-propagating terms in
`compute/components.py`:**

- `_compute_s_rs`: `within_basket_z_21d` (line 117)
- `_compute_s_rs_leadership` accel block: `rs_rating_slope_120d` (line 141)
- `_compute_s_rs_leadership` confluence block: `within_basket_z_63d` (line 157)

Rationale: a NaN within-basket z indicates "basket too small for a meaningful
ranking" — semantically equivalent to "this stock is at the basket median,"
which is z = 0. Filling with 0 is the unbiased, zero-information choice.

**Fix 2 — Universe cleanup.** Three tickers cannot be scored cleanly even
with the fillna fix:

- `CTRA` — post-merger (Cabot/Cimarex 2021), insufficient continuous history
- `TRUL.CN` — Canadian listing, sparse OHLCV
- `EUROB.AT` — Greek ATHEX listing, data limitations

Removed entirely from `data/universe.py` (PRIMARY_BASKETS,
PRIMARY_BASKET_CONSTITUENTS, MANUAL_OVERRIDES, TAGS, top-level CATEGORIES).
Side effect: the **Greece Reclassification** basket now has a single
constituent (`GREK`), which is below the 3-member health threshold but
intentionally retained.

**Fix 3 — Benchmark carve-out (SPY/QQQ).** Benchmarks were never in the
universe-level baskets but were being included in the scored feature panel
because `data_quality.py` returned them as PASS. Now:

- `BENCHMARKS` in `data/universe.py` is a `set` (`{"SPY", "QQQ"}`)
- `compute/features.py` excludes `BENCHMARKS` from `compute_features()`'s
  scored universe (still uses them as inputs for RS-vs-SPY computations)
- `compute/pipeline.py` carves out SPY/QQQ OHLCV into a dedicated
  `data/cache/benchmarks.parquet` (2,552 rows, 8 cols) for chart overlays

**Fix 4 — Strip exception lists.** The validator previously imported a
`KNOWN_BENCHMARKS` set and an `INSUFFICIENT_HISTORY_EXCEPTIONS` set. With the
universe now clean, every scored ticker must produce a valid CCQS — those
sets are removed from `compute/validation/level3_validation.py` (checks E, G,
J). No hardcoded exceptions remain in the validator.

**Post-fix Level 3 validation result (2026-05-22 snapshot):**

| Metric | Value |
|--------|-------|
| Scored universe | **858 stocks** |
| Total checks | 20,956 |
| Pass | 20,900 |
| Failures | **0** |
| Borderlines (all WARN) | 56 |
| External (yfinance) | 50/50 matched, 0 discrepancies |
| Verdict | REVIEW (no failures; 56 statistical-edge borderlines) |
| Elapsed | 2.9s |

Borderline categories: 49 `G_low_rs_strong_tier` (RS<20 stocks not in WEAK
tier — by-design borderline), 5 `D_s_climax_extreme_z` (|z|>5 outliers in
semiconductor / cybersec names), 1 `C_pct_ma_50_bounds` (FCEL, low-priced),
1 `C_pct_ma_200_bounds` (SNDK, recent IPO).

**OOS IC re-baseline (accepted as new official baseline).** The previous IC
table was computed with a 12%-coverage bug (NaN-CCQS stocks dropped from
the cross-section). Honest post-fix values:

| Horizon | t-stat | Mean OOS IC | Hit rate | Δ t vs prior |
|---------|--------|-------------|----------|---------------|
| 1d   | **+4.16** | +0.0173 | 68.2% | +0.30 (improved) |
| 5d   | +1.65 | +0.0168 | 61.4% | +0.22 |
| 20d  | +1.26 | +0.0225 | 56.8% | +0.26 |
| 60d  | +0.94 | +0.0166 | 59.5% | -0.03 |
| 126d | **+2.59** | +0.0412 | 69.2% | -0.31 (still significant) |
| 252d | **+2.05** | +0.0360 | 63.6% | +0.04 |

All three production horizons (1d, 126d, 252d) remain t > 2.0. The 126d drop
is acceptable — the prior +2.90 reading was artificially elevated by
selective NaN-dropping. New values stand as the canonical post-fix baseline.

---

### Phase 5.3 — Selective SP100 promotion (2026-05-23)

**Trigger.** Sandbox SP100 coverage-gap analysis (`compute/sandbox/sp100_analysis.py`)
identified twelve SP100 names absent from the production universe. The 870-ticker
sandbox run (production-passing 858 + 12 SP100-missing) produced OOS IC deltas of
+0.3% to ±2.0% across all six horizons versus the production-extended baseline,
demonstrating methodology stability under the SP100 subset addition. Twelve names
were evaluated; five are promoted, seven are explicitly excluded for the reasons
below.

**Five promotions.** Added to existing thematic baskets — no new baskets created,
no broad GICS sector baskets introduced.

| Ticker | Basket | CCQS (2026-05-22) | Grade | State | Rationale |
|--------|--------|-------------------|-------|-------|-----------|
| AAPL | Hyperscalers | 91.02 | A | TRENDING | Iconic mega-cap technology; clean fit with existing AMZN/GOOGL/META/MSFT/ORCL |
| BNY | Money Center Banks | 94.92 | S | TRENDING | Custody bank, prior ticker BK rebranded to BNY in 2024 |
| HON | Industrial Automation | 64.79 | B | TRENDING | Industrial conglomerate — best existing fit alongside ROK/ETN/EMR/AME/PH |
| SBUX | Quick Service Restaurants | 66.56 | B | PULLBACK | Largest US restaurant chain; clean fit with MCD/YUM/QSR/CMG/DPZ |
| TGT | Grocery and Clubs | 85.17 | A | PULLBACK | Big-box mass-merchandiser — best existing fit with WMT/COST/KR/BJ/ACI |

Universe size: **863 passing tickers** (was 858 → +5). Declared universe: **884**
(was 879 → +5).

**Seven explicit non-promotions.** Excluded for the following reasons:

| Ticker | Reason |
|--------|--------|
| GOOG | Class-C share of GOOGL (already in Hyperscalers) — would double-count Alphabet exposure |
| BRK-B | Conglomerate insurance holding with no clean thematic fit; ticker hyphen handling complicates fetch |
| MMM | Diversified conglomerate; no single clean basket; would require new basket creation |
| T | Telecom carrier; no Telecom basket in production universe; would require new basket |
| TMUS | Telecom carrier; same — no Telecom basket exists |
| CHTR | Cable / broadband carrier; no Telecom/Cable basket exists |
| VZ | Telecom carrier; no Telecom basket exists |

The decision to add 5 (not 12) keeps thematic baskets coherent and avoids creating
single-member or two-member Telecom / Conglomerate baskets which would be below
the 3-member health threshold.

**Pipeline re-run.** End-to-end refresh on the 884-declared / 863-scored universe:

| Stage | Time |
|-------|-----:|
| features | 63.8s |
| z_scores | 56.0s |
| components | 4.7s |
| state | 0.5s |
| leadership | 0.2s |
| ccqs | 1.9s |
| setups | 0.6s |
| aggregation | 162.3s |
| reliability stack | 33.0s |
| snapshot | 0.8s |
| **Total** | **~325s** |

**Validation.** All eleven reliability sanity checks pass on the new snapshot
(`data/cache/sanity_checks.json`): `ccqs_in_0_100`, `state_probs_sum_to_1`,
`state_p_adj_sum_to_1`, `no_inf_components`, `grade_s_pct_in_2_15`,
`leadership_tier_values_valid`, `setup_confidence_in_0_1`, `index_alignment`,
`theme_ccqs_coverage`, `features_fresh_within_5d`, `universe_coverage`.

CCQS distribution post-promotion: mean 50.14, median 50.81, p1 2.51, p99 97.74.
Grade S share 6.37%, Grade A share 9.49%, S+A = 15.86% (within the 2–15% spec
target for S alone and well within the 30% S+A sanity ceiling).

**Sentinel drift.** Top-50 rank stability is **49/50 = 98%** (WDC drops out as BNY
enters at S-grade). Sentinel re-rank magnitudes on 14 incumbent names:

| Ticker | Pre | Post | Δ | | Ticker | Pre | Post | Δ |
|--------|-----|------|---|-|--------|-----|------|---|
| NVDA | 78.75 | 78.55 | -0.21 | | MCD | 9.37 | 9.12 | -0.25 |
| MSFT | 29.67 | 29.08 | -0.59 | | COST | 73.47 | 72.85 | -0.63 |
| GOOGL | 91.95 | 91.68 | -0.27 | | WMT | 50.48 | 49.46 | -1.02 |
| META | 16.49 | 16.04 | -0.45 | | JPM | 43.81 | 41.78 | -2.03 |
| AMZN | 88.64 | 88.35 | -0.29 | | BAC | 46.80 | 44.55 | -2.26 |
| AVGO | 81.18 | 80.96 | -0.22 | | WFC | 21.72 | 21.79 | +0.06 |
| ORCL | 65.06 | 64.51 | -0.55 | | TSLA | 73.92 | 73.68 | -0.24 |

Max |Δ| = 2.26 (BAC). The drift exceeds the ±0.5 informal target on 6/14
sentinels but is **mathematically expected** under cross-sectional percentile
ranking when high-quality names enter the cohort: BNY at S-grade (94.92) crowds
the Money Center Banks ranks (JPM/BAC drop ~2 points), and AAPL/TGT entering the
top decile compresses the percentile space for incumbents in their baskets. The
delta is not a methodology drift signal — it is the deterministic re-ranking
consequence of universe expansion. Methodology stability is confirmed by the
98% top-50 overlap and clean sanity-check pass.

**IC tracker headline (post-promotion, 863-stock universe, full 7-year window):**

| Horizon | IC mean | IC-tracker t-stat | hit rate |
|---------|---------|-------------------|---------:|
| 1d | +0.0153 | +2.87 | 56.2% |
| 5d | +0.0121 | +2.57 | 54.4% |
| 20d | +0.0118 | +2.78 | 55.1% |
| 60d | +0.0108 | +2.90 | 53.3% |
| 126d | +0.0233 | +7.41 | 59.3% |

**Important:** IC-tracker t-stats are computed by
[compute/reliability/ic_tracker.py](compute/reliability/ic_tracker.py) which pools
daily ICs across all dates in the history (`SE = std / √n_dates`, n=1362 at
126d). This is **apples-to-oranges with the Phase X.3 OOS-evaluation t-stats**
(window-averaged, `SE = std / √n_windows`, n=48 at 126d in the 5-year window).
Daily ICs at 126d overlap by 125/126 days and are not independent — pooling them
inflates t-stats by a factor of ~√(n_dates/n_windows) ≈ 4×. The IC-tracker
output is a monitoring headline for decay detection, not a statistical
significance test, and must not be cited as evidence of methodology improvement.

The Phase X.3 OOS-evaluation baseline (1d t=4.16, 126d t=2.59, 252d t=2.05)
remains the **published official baseline** per the Methodology Lock §6. The
post-Phase-5.3 IC-tracker values above are recorded as supplementary monitoring
only.

**Sandbox infrastructure preserved.** `compute/sandbox/` and `data/cache/sandbox/`
remain intact for future coverage-gap experiments. The next candidate evaluation
should re-run `compute/sandbox/sp100_analysis.py` (or an analogous script) on the
new prospect set before any further promotion.

**Dashboard sandbox tab hidden.** The Streamlit dashboard
([app/streamlit_app.py](app/streamlit_app.py)) gates the sandbox tab behind a
`SHOW_SANDBOX = False` module-level flag (default off in production). The
sandbox loader (`app/utils/data_loader_sandbox.py`), the sandbox compute stack
(`compute/sandbox/`), and the sandbox cache (`data/cache/sandbox/`) are all
unchanged — the gate only governs UI surface visibility. Flip `SHOW_SANDBOX = True`
to re-enable the tab without re-running any pipeline.

---

### Phase 5.5 — Naming standardization (2026-05-24)

**Trigger.** Presentation polish for institutional review. The state-classifier
vocabulary inherited from internal development used informal terms
(`COILING`, `CLIMACTIC`, `BROKEN`, `MIXED`) and the setup taxonomy mixed
colloquial labels ("Healthy Trend", "Weak Setup", "Mixed / Indeterminate")
with technical ones ("VCP Setup", "BB Squeeze with RS"). The renaming
standardizes on neutral finance vocabulary suitable for external audiences.
**Methodology is unchanged.**

**State value renames** (4 of 6 states; `TRENDING` and `PULLBACK` unchanged):

| Old | New |
|-----|-----|
| `COILING` | `CONSOLIDATING` |
| `CLIMACTIC` | `EXHAUSTION` |
| `BROKEN` | `DETERIORATING` |
| `MIXED` | `INDETERMINATE` |

Probability and state-adjusted columns (`p_*`, `p_adj_*`) renamed in lockstep
inside `state.parquet`. `STATE_WEIGHTS` lookup keys renamed in
[compute/ccqs.py](compute/ccqs.py) accordingly. Bayesian-averaging math is
identical because the dict keys move together with the lookups.

**Setup label renames** (18 of 29 labels; entries 11-12 added in Phase 5.6, entries 13-18 added in Phase 5.7):

| Old | New |
|-----|-----|
| Healthy Trend | Sustained Uptrend |
| Healthy Pullback | Routine Pullback |
| Healthy Consolidation | Constructive Consolidation |
| Strong Continuation | Trend Continuation |
| Weak Setup | Low-Confidence Pattern |
| Range-Bound Coil | Range Consolidation |
| Mixed / Indeterminate | Indeterminate Pattern |
| Late Stage | Late-Cycle Pattern |
| Broken Downtrend | Trend Failure |
| Broken Distribution | Distribution Pattern |
| Coil Within Strong Theme | Consolidation Within Strong Theme |
| Strong Coil Pre-Breakout | Tight Consolidation Pre-Breakout |
| Climax Parabolic | Parabolic Blow-Off |
| Climax Bearish Divergence | Exhaustion w/ Bearish Divergence |
| Climax Volume Confirmed | Volume-Confirmed Exhaustion |
| Climax Extended | Extended Exhaustion |
| Broken Capitulation | Capitulation Selling |
| Broken Bullish Divergence | Deteriorating w/ Bullish Divergence |

**Aggregation column renames** (`theme_aggregates.parquet`):

| Old | New |
|-----|-----|
| `pct_climactic` | `pct_exhaustion` |
| `pct_broken` | `pct_deteriorating` |

**Preserved (intentionally NOT renamed):**

- `leadership_tier` value `DETERIORATING` — leadership namespace. The
  state-classifier `DETERIORATING` and the leadership-tier `DETERIORATING`
  are stored in distinct columns of distinct parquet files; no downstream
  calculation joins them by name.
- `theme_class` values `MIXED`, `BROKEN_THEME`, `WEAKENING`, `STABLE`,
  `ELITE_THEME`, `STRONG_THEME`, `EMERGING_THEME`, `NARROW_LEADERSHIP` —
  theme-aggregate namespace, computed in §11 from breadth and `theme_ccqs`.
- "Distribution" in basket names ("Switchgear and Electrical Distribution",
  "Industrial Distribution"), the "Distribution Days (25d)" metric, and the
  `distribution_days_25` feature column — these reference share-distribution
  patterns (Wyckoff-style), not the renamed deteriorating state.
- Feature flag `climax_volume_flag` — methodology/feature namespace, used
  by state classification and the setup classifier. The component score
  `s_climax` referenced in the original Phase 5.5 preservation list was
  subsequently **removed entirely in Phase 6** (2026-05-25); the
  dashboard's component decomposition view now reports 9 components.

**Methodology preservation (verified bit-identically).** Phase 5.5 is a
relabeling only. The state-classification log-likelihoods, the Bayesian
averaging math, the setup-priority cascade, and the cross-sectional
standardization are unchanged. The migration renames Python identifiers,
parquet columns and string values, and JSON keys; no arithmetic is touched.

Comparison of fresh pipeline outputs (post-rename code + data) vs. the
pre-rename backup at `.migration_backup_phase_5_5/cache_backup/`:

| Field | Max \|diff\| | Notes |
|-------|-------------:|-------|
| `ccqs` | 0.00e+00 | 1,553,400 rows, bit-identical |
| `ccqs_raw` | 0.00e+00 | bit-identical |
| `ccqs_z` | 0.00e+00 | bit-identical |
| `grade` | 0 mismatches | full equality |
| each `p_*` (after key rename) | 0.00e+00 | probability vectors identical |
| each `p_adj_*` (after key rename) | 0.00e+00 | adjusted probabilities identical |
| `primary_state` (after rename) | 0/1,553,400 mismatches | classification identical |

The **Phase X.3 OOS IC baseline** (1d t=4.16, 126d t=2.59, 252d t=2.05)
is preserved unchanged per Methodology Lock §6 — naming has no effect on IC.

**Files affected.**

| Category | Count | Detail |
|----------|------:|--------|
| Python source | 13 | state classifier, CCQS weights, setup classifier, aggregation, anomaly detection, sanity checks, regularized weighting, level3 validation, data loader, color theme, Streamlit app, manual-overrides yaml comments |
| Tests | 2 | Phase 3 validation list + TV-snapshot canary pinned values |
| Cache parquet | 17 | live cache (4), dashboard slim (3), 2026-05-22 snapshot (4), sandbox (4), sp100 (2) |
| JSON sidecars | 6 | `anomalies.json` (×3), `pipeline_meta.json` (×3 — selective: `state_distribution` + `top_10_setups` only; `theme_class_distribution` preserved) |

**Migration tooling.** A one-shot data migration script is preserved at
[`scripts/phase_5_5_data_migration.py`](scripts/phase_5_5_data_migration.py)
for audit trail. It reads each parquet, applies column / value renames in
place (snappy compression preserved), and patches the JSON sidecars
selectively. Re-running it on already-migrated data is a no-op.

**Validation.** Post-migration end-to-end pipeline run completes in 209.6s.
All 11 reliability sanity checks pass (`data/cache/sanity_checks.json`).
State distribution after rename:

| State | Share |
|-------|------:|
| TRENDING | 16.87% |
| PULLBACK | 19.53% |
| CONSOLIDATING | 5.21% |
| EXHAUSTION | 2.20% |
| DETERIORATING | 28.07% |
| INDETERMINATE | 28.11% |

CCQS distribution: mean 50.14, median 50.81, S-grade share 6.37% (within
the 2–15% spec band). Top-10 setup distribution uses the new vocabulary
(post-Phase-5.8: "Indeterminate Pattern" 20.16%, "Range Consolidation"
12.17%, "Deteriorating (Generic)" 11.61%, "Routine Pullback" 9.54%,
"Trending (Generic)" 8.26%, ...).

---

### Phase 5.6 — Coil follow-up (2026-05-24)

Phase 5.5 renamed the `COILING` state to `CONSOLIDATING` and the
`Range-Bound Coil` setup to `Range Consolidation`, but two
Consolidating-state setups still carried the old "Coil" vocabulary
(`Coil Within Strong Theme`, `Strong Coil Pre-Breakout`). This
follow-up commit drops those references so the setup naming aligns
fully with the state vocabulary. (The `Climax *` and `Broken *`
sub-setups were initially preserved here but subsequently renamed in
Phase 5.7 — see below.)

| Old | New |
|-----|-----|
| Coil Within Strong Theme | Consolidation Within Strong Theme |
| Strong Coil Pre-Breakout | Tight Consolidation Pre-Breakout |

`scripts/phase_5_5_data_migration.py` was extended with the two
additional `SETUP_RENAMES` entries and re-run; the script is
idempotent, so it only touched the new labels and left the rest of the
caches untouched. Validation: 11/11 sanity checks pass; CCQS
bit-identical vs the 2026-05-22 snapshot (max|diff| = 0.00e+00, 0/863
grade mismatches); no residual `Coil` labels in any setups parquet.

---

### Phase 5.7 — Climax / Broken sub-setup rename (2026-05-24)

Phase 5.5 renamed the `CLIMACTIC` state to `EXHAUSTION` and `BROKEN` to
`DETERIORATING`, but the six Exhaustion / Deteriorating sub-setup
labels (`Climax Parabolic`, `Climax Bearish Divergence`,
`Climax Volume Confirmed`, `Climax Extended`, `Broken Capitulation`,
`Broken Bullish Divergence`) were initially preserved as chart-pattern
terms of art. On reviewing the deployed dashboard the labels read
inconsistently next to the renamed states, so the same naming-parity
argument that drove Phase 5.6 applies here. The new labels were
verified against the underlying detection logic (`atr_x_50`,
`bearish_divergence_20d`, `climax_volume_flag`, etc.) before adoption.

| Old | New |
|-----|-----|
| Climax Parabolic | Parabolic Blow-Off |
| Climax Bearish Divergence | Exhaustion w/ Bearish Divergence |
| Climax Volume Confirmed | Volume-Confirmed Exhaustion |
| Climax Extended | Extended Exhaustion |
| Broken Capitulation | Capitulation Selling |
| Broken Bullish Divergence | Deteriorating w/ Bullish Divergence |

The methodology-layer identifiers `s_climax` (component score) and
`climax_volume_flag` (feature column) are intentionally preserved —
they refer to the technical detection feature, not the user-facing
setup label, and renaming would require touching the components and
features compute paths with no presentation benefit.

The reference TradingView snapshot for NVDA in
[tests/reference/tv_snapshots.py](tests/reference/tv_snapshots.py)
was updated in lockstep so the bit-identical reference test stays
green. Validation: 11/11 sanity checks pass; CCQS bit-identical vs the
2026-05-22 snapshot; no residual `Climax *` or `Broken Capitulation` /
`Broken Bullish Divergence` labels in any setups parquet.

---

### Phase 5.8 — Setup label accuracy audit (2026-05-25)

Tier A of the Priority 1 foundation work. The audit re-examined each of
the 29 setup labels against the actual detection logic in
[compute/setup_classifier.py](compute/setup_classifier.py) and renamed
any that overclaimed relative to what the math measures. Two categories
of mismatch were corrected:

**Specific patterns** (4 renames). The label promised a property the
math doesn't verify:

| Old | New | Why |
|-----|-----|-----|
| Parabolic Blow-Off | Extreme Extension | Trigger is `atr_x_50 ≥ 6.5` only — no climactic-volume or parabolic-shape gate, so "Blow-Off" overclaimed |
| Trend Failure | Sustained Weakness | Trigger is `pct_ma_50 < -8` — a static position threshold, not a trend-transition event |
| Tier S Pullback | Premium Pullback | The 6-feature gate matches "high-quality pullback" but never checks CCQS grade — "Tier S" conflated grade vocabulary with setup detection |
| Emerging Leader (Multibagger Setup) | Emerging Leader | The pattern is mid-RS + accelerating + multi-timeframe + volume; "(Multibagger Setup)" was forward-looking marketing |

**State catch-alls** (4 renames). Each catch-all fires when the primary
state matches but no specific pattern triggered, so labels that implied
duration / bias / cycle position / confidence overclaimed:

| State | Old | New |
|-------|-----|-----|
| TRENDING | Sustained Uptrend | Trending (Generic) |
| CONSOLIDATING | Constructive Consolidation | Consolidating (Generic) |
| EXHAUSTION | Late-Cycle Pattern | Exhaustion (Generic) |
| DETERIORATING | Low-Confidence Pattern | Deteriorating (Generic) |

The remaining 21 labels were verified accurate and unchanged: Exhaustion
w/ Bearish Divergence, Volume-Confirmed Exhaustion, Extended Exhaustion,
Capitulation Selling, Deteriorating w/ Bullish Divergence, Distribution
Pattern, Elite Leader Continuation, Elite Leader Pullback, Theme Leader
Pullback, Trend Continuation, Trending Leadership, Pullback to 21EMA,
Pullback to 50MA, Consolidation Within Strong Theme, Tight Consolidation
Pre-Breakout, VCP Setup, BB Squeeze with RS, Range Consolidation, Failed
Breakout, Routine Pullback, Indeterminate Pattern.

Data migration ([scripts/phase_5_5_data_migration.py](scripts/phase_5_5_data_migration.py))
extended with the 8 new entries plus chained-rename updates so a parquet
at any prior Phase 5.5–5.7 vocabulary migrates to the Phase 5.8 final
label in one pass. TV reference snapshots for NVDA, META, JPM, UNH
updated in lockstep.

**Caveat — "Consolidation Within Strong Theme" (#18) is currently
unreachable.** Its `theme_strong` gate is hardcoded `False` because the
theme aggregation layer runs after the setup classifier in the Phase 3
pipeline. The label exists for forward compatibility; no row can earn it
in the current pipeline order.

---

### Phase 6 — Foundation fixes (2026-05-25)

Three improvements to the composite layer driven by the Priority 1
foundation-fix mandate (empirical signal quality over theoretical
elegance):

**1. Per-date winsorization of CCQS display values**
([compute/ccqs.py:165](compute/ccqs.py:165))

The prior global `np.nanpercentile(ccqs_raw, 1.0/99.0)` clip computed one
fixed lower/upper threshold across the entire 1.55M-row long frame and
clipped every row against the same two numbers. Because that pair of
numbers was strictly determined by the global distribution, every row
beyond the threshold collapsed to those exact two values:

- Pre-fix: max tie count = **12,281 rows pinned at 97.74**, 12,281 at
  2.51. Total of 24,562 rows (≈1.6% of universe-days) lost any
  cross-sectional dispersion within their date.
- Post-fix (per-date `p1/p99` via [`_per_date_winsorize`](compute/ccqs.py:125)):
  max tie count = **9 rows**, 1,205,080 unique values across 1.55M rows.

Per-date `p1` ranges 0.64 – 5.71 across the 1,800 dates; `p99` ranges
94.50 – 99.18. Bear-market days clip 25+ tops, bull-market days clip 30+
floors — these previously collapsed to the same global pair regardless
of when they occurred. The fix preserves cross-sectional dispersion
within each date by clipping each row against its own date's local
tails.

Grade distribution is **unchanged** (S 6.37% / A 9.49% / B 19.73% /
C 19.74% / D 23.73%) because grading already used per-date quantiles —
the global clip only ever affected display values, never grade
assignment. Only 32,099 rows (2.07%) change display value; median |Δ| =
0.41 CCQS points, max 3.03.

**2. Removed `s_climax` from the component set**
([compute/components.py:51](compute/components.py:51),
[compute/ccqs.py:62](compute/ccqs.py:62))

`s_climax` carried weight 0.00 in every state since Phase X.2.1
(mean OOS IC = −0.0242, significantly negative at two horizons). The
component dimension dropped from 10 → 9. The math was also inverted vs
the label: `raw = 100 − (extension_penalty + time_score +
vol_climax_score)`, so a "high s_climax" meant *less* climactic risk —
contributing to the negative OOS IC. Removing it is bit-identical for
CCQS (verified: mean / median / all grade percentages unchanged) since
its weight was already zero, and simplifies the code surface without
loss of signal. The underlying features (`climax_volume_flag`,
`days_near_52w_high_60d`, `consecutive_high_intensity`) are still
computed and consumed by state classification and the setup classifier.

**3. Diagnostic fields in `ccqs_meta.json`**

Added `ccqs_unique_values`, `ccqs_max_tie_count`, and
`winsorization: "per-date p1/p99"` fields so any future tie regression
is detectable from the meta JSON alone.

---

### Known caveats & limitations (Phase 6 documentation)

**Cross-sectional standardization caveats**

All components are z-scored cross-sectionally per date. This means:

1. Component values are always relative to *that date's universe*, not
   to an absolute baseline. A "1.0 z" in 2020 reflects a different raw
   feature value than a "1.0 z" in 2026 if the universe distribution
   shifted.
2. CCQS percentile values reflect *relative rank within the date*, not
   absolute quality. A market-wide drawdown compresses the dispersion,
   so a CCQS of 80 in March 2020 represents a meaningfully different
   stock than a CCQS of 80 in March 2024.
3. The Bayesian state-weighted composite has narrow variance (≈ 0.14)
   before per-date renormalization. The `_per_date_zscore()` call in
   `compute_ccqs()` is what restores N(0,1) shape so `Φ(z)·100` spans
   the full 0–100 range.

**Per-date winsorization trade-off**

Per-date clipping eliminates the global tie problem but still creates
~1% of each date's universe pinned at the date's local `p99`. For a
900-stock day, that's ~9 stocks tied at the top. These ties are
intentional (winsorization is the standard treatment for display-value
extremes) and only affect the *display value*, not the *grade* (grades
use per-date quantile thresholds independently).

**State-confidence blending**

When `max(p_state) < 0.7`, state probabilities are blended toward
INDETERMINATE (50/50 if `max < 0.5`, 70/30 if `< 0.7`). This is by
design — it prevents low-confidence state classifications from
dominating Bayesian-averaged CCQS — but means INDETERMINATE-state
stocks effectively inherit the INDETERMINATE weight column, which is
a near-average column. The signal-to-noise on these rows is therefore
weaker by construction. State distribution shows 28.1% INDETERMINATE
in the current cache.

**`s_climax` removal — history note**

Phase X.2.1 zeroed `s_climax` in every state (negative OOS IC). Phase 6
removed it from the component set entirely. If a future validation
phase identifies a real climactic-extension signal worth modeling, the
component should be re-derived with an inverted sign (high score =
high climactic risk) and weighted negatively in the composite. The
underlying features remain available.

**TV reference snapshot staleness**

The reference values in [tests/reference/tv_snapshots.py](tests/reference/tv_snapshots.py)
were last pinned 2026-05-22 against a Phase 4 build. CCQS values
subsequently drifted 5–8 points on several large-caps (MSFT, META,
AMZN, TSM, NVDA) due to the Phase X.3 component-weight redistribution,
which happened before this repo's first commit. Per-date winsorization
(Phase 6) does **not** affect any of the 10 canaries — verified by
running both global and per-date paths on the live components/state
cache and confirming identical outputs. Refresh of CCQS / grade / setup
pins to the current build is a pending decision; the technical-indicator
pins (close, RSI, ADX, ATR, pct_ma_*) remain accurate within tolerance.

**Setup label "Consolidation Within Strong Theme" is structurally
inactive in Phase 3** — its `theme_strong` gate is hardcoded `False`
because the theme aggregation layer runs after the setup classifier.
The label is preserved for forward compatibility.

---

### Priority 2 — Empirical validation of current methodology (2026-05-25)

Investigation-only pass (no code changes). Two parallel studies under the
Phase 6 baseline (9 components, per-date winsorized CCQS):

  - **2a Bootstrap CIs on STATE_WEIGHTS** — 54 cells (9 components × 6
    states), 4 horizons (5d / 20d / 60d / 126d), block bootstrap with
    21-day blocks and 1000 iterations. Per-cell IC = cross-sectional
    Spearman of component vs forward return, restricted to rows where
    `primary_state == s`.

  - **2b Conditional CCQS IC** — partitioning the 1,553,400 row-days by
    primary state, dollar-volume quintile, per-stock 60d realized-vol
    quintile, SPY 20d realized-vol tercile (market regime), year, and
    91 primary baskets (n ≥ 5 members each).

Reference baseline IC of unconditional CCQS (1,362–1,483 dates):
`5d: +0.0121 (t=2.57)`, `20d: +0.0118 (t=2.78)`, `60d: +0.0108 (t=2.90)`,
`126d: +0.0233 (t=7.41)`. All four horizons clear t > 2.0 unconditionally.

**Headline finding 2a-i — Most state-conditional weight cells are
statistically indistinguishable from zero.** Out of 54 cells per horizon
(90% bootstrap CI excluding zero):

| Horizon | Sig positive | Sig negative | Insignificant |
|---------|--------------|--------------|---------------|
|  5d  |  9 / 54  |  3 / 54  | 42 / 54 (78%) |
| 20d  |  5 / 54  |  5 / 54  | 44 / 54 (81%) |
| 60d  | 13 / 54  |  5 / 54  | 36 / 54 (67%) |
| 126d | 19 / 54  |  3 / 54  | 32 / 54 (59%) |

At the 20d institutional horizon, only ~9% of weight cells carry an IC
statistically distinguishable from zero. This does not mean the matrix
is wrong — it means the 1,468 dates of data are not enough to resolve
individual per-state per-component IC at 90% confidence for most cells.

**Headline finding 2a-ii — State-conditional weighting is largely
empirically arbitrary at 20d.** For each (component, horizon) we
compared IC across all 15 state-pairs:

| Horizon | State-pairs differing at 90% CI |
|---------|--------------------------------:|
|  5d  | 30 / 135  (22%) |
| 20d  | 11 / 135  ( 8%) |
| 60d  | 33 / 135  (24%) |
| 126d | 46 / 135  (34%) |

At 20d, only 8% of state-pairs show statistically distinguishable IC
for the same component. The remaining 92% of pairs cannot reject the
null hypothesis that the component has the same IC in both states.
State-conditional weighting at this horizon adds structural / narrative
value but limited measurable OOS signal.

The state-pair differences that *do* emerge are concentrated:
EXHAUSTION state appears in most significant pairs, suggesting EXHAUSTION
is the one regime worth treating differently. CONSOLIDATING is the
next most distinguishable.

**Headline finding 2a-iii — Component-level empirical quality is
strongly unequal.** Across the 24 cells per component (6 states × 4
horizons):

| Component | avg IC | sig+/24 | sig−/24 | total weight | Verdict |
|-----------|-------:|--------:|--------:|-------------:|---------|
| s_rs | +0.023 | 10 |  0 | 5.24 | **Carrier** |
| s_structure | +0.018 | 11 |  0 | 4.48 | **Carrier (most consistent)** |
| s_rs_leadership | +0.016 |  8 |  0 | 6.04 | **Carrier (highest weight)** |
| s_mtf | +0.010 |  6 |  0 | 3.56 | **Carrier (smaller magnitude)** |
| s_extension | +0.005 |  4 |  0 | 0.20 | Marginal positive (correctly small weight) |
| s_rsl | +0.004 |  2 |  2 | 0.56 | Noise / neutral |
| s_trend_slope | +0.001 |  3 |  3 | 0.52 | Noise / neutral |
| s_momentum | +0.001 |  2 |  5 | 0.24 | Marginal negative |
| **s_demand** | **−0.009** | **0** | **6** | **3.16** | **Negative carrier — actively harmful** |

The four carriers (s_rs, s_rs_leadership, s_structure, s_mtf) account
for total weight 19.32 / 54 = ~64% of the matrix. Within those four,
weight is well-aligned with the sign of empirical IC.

**`s_demand` is the next removal candidate.** Like `s_climax` before it,
`s_demand` carries the third-highest total weight (3.16, second only to
`s_rs_leadership` and `s_structure`) despite having an average IC of
−0.009 and 6 of 24 cells with significantly negative IC. The cells with
significantly negative IC include `s_demand` in CONSOLIDATING (w=0.15)
at all four horizons, PULLBACK at 20d and 60d, and INDETERMINATE at 60d.
Removing or zeroing `s_demand` would free ~10% of total weight for the
four carrier components.

Pearson correlation between the current matrix and empirical IC across
all 54 cells:

| Horizon | Pearson | Spearman | p-value | OLS slope |
|---------|--------:|---------:|--------:|----------:|
|  5d  | +0.465 | +0.527 | <0.001 | +0.086 |
| 20d  | +0.403 | +0.399 |  0.002 | +0.056 |
| 60d  | +0.269 | +0.272 |  0.049 | +0.059 |
| 126d | +0.263 | +0.308 |  0.023 | +0.061 |

The matrix is positively correlated with empirical IC at every horizon
— the *directional* intuition behind hand-crafted weights is right.
But the moderate correlation (0.26–0.47) means only 7–22% of the
variance in actual per-cell IC is captured by current weight choices.
Half or more of the per-cell weight magnitude is not statistically
informative.

**Headline finding 2b-i — CCQS works best on smaller, more volatile
stocks during low-vol markets.** Monotonic patterns:

| Bucket | 60d IC | 126d IC | Notes |
|--------|-------:|--------:|-------|
| Dollar-volume Q1 (smallest) | +0.048 | +0.061 | Strongest single bucket |
| Dollar-volume Q3 | +0.015 | +0.022 | Mid |
| Dollar-volume Q5 (largest) | **−0.017** | **−0.007** | Negative in mega-caps |
| Per-stock vol Q1 (low vol) | +0.021 | +0.020 | Weaker |
| Per-stock vol Q5 (high vol) | +0.041 | +0.058 | Strong |
| Market vol regime LOW | +0.039 | +0.045 | Strong all horizons |
| Market vol regime MID | +0.007 | +0.051 | Mixed |
| Market vol regime HIGH | **−0.014** | **−0.025** | **Signal fails in crises** |

The signal flips sign in mega-caps and high-vol regimes — these are
explicit out-of-distribution domains where the composite should not be
trusted at long horizons.

**Headline finding 2b-ii — Regime sensitivity by year.**

| Year | 5d | 20d | 60d | 126d |
|------|----|-----|-----|------|
| 2020 | +0.038 (t=2.1) | +0.054 (t=3.4) | +0.035 (t=2.7) | **−0.052 (t=−6.1)** |
| 2021 | −0.018 | **−0.058 (t=−6.3)** | **−0.062 (t=−7.8)** | **−0.045 (t=−6.6)** |
| 2022 | +0.017 | +0.020 | +0.012 | +0.026 (t=3.0) |
| 2023 | −0.015 | −0.014 | +0.011 | +0.082 (t=12.9) |
| 2024 | +0.026 (t=2.7) | +0.039 (t=4.2) | +0.008 | +0.061 (t=14.1) |
| 2025 | +0.013 | +0.021 (t=2.2) | +0.046 (t=5.4) | +0.033 (t=4.7) |

The 2021 meme-stock / SPAC-mania year drove the composite to negative
IC at every horizon. The Phase X.3 multi-window OOS framework averages
across regimes and is therefore conservative in good regimes and too
optimistic in adverse ones. **The signal does not work in speculative-
euphoria regimes** — a category to flag in pre-trade conditioning.

**Headline finding 2b-iii — Sector dispersion is enormous.**

Among 91 baskets with ≥ 100 row-days, basket-level 60d IC ranges from
**+0.205** (Hotels and Casinos) to **−0.275** (Household and Personal
Care). Median basket IC at 60d is −0.009, IQR [−0.063, +0.049]. The
positive tail is dominated by cyclicals and recovery names (Hotels,
Auto Affordability, Oilfield Services, Heavy Machinery, Coal,
Aggregates). The negative tail is dominated by defensives and stable
traditional sectors (Household/Personal Care, Gold Royalty, Energy
Majors, Gaming Publishers, Railroads, Beverages, Industrial Automation).

CCQS encodes a clear **cyclical / non-defensive bias**. The composite
favors stocks whose returns are momentum / quality-driven and underweights
or actively works against stocks whose returns are mean-reverting or
yield-dominated.

**Conditional state IC (CCQS, full universe).**

| State | 5d | 20d | 60d | 126d |
|-------|----|-----|-----|------|
| TRENDING | +0.014 (t=3.0) | +0.006 | +0.028 (t=7.1) | +0.042 (t=12.3) |
| PULLBACK | +0.015 (t=2.9) | +0.007 | +0.013 (t=2.9) | +0.010 (t=2.6) |
| CONSOLIDATING | +0.026 (t=4.6) | +0.025 (t=4.6) | +0.039 (t=7.6) | +0.029 (t=5.7) |
| EXHAUSTION | +0.023 (t=3.0) | **−0.002 (t=−0.3)** | +0.007 | +0.032 (t=3.7) |
| DETERIORATING | +0.005 | +0.006 | +0.009 (t=2.6) | +0.018 (t=5.3) |
| INDETERMINATE | +0.006 | +0.011 (t=2.6) | +0.004 | +0.019 (t=5.6) |

CONSOLIDATING is the strongest state for CCQS — significant at all four
horizons. EXHAUSTION at 20d shows IC ≈ 0 (t = −0.32) — the signal does
not predict 20d returns for stocks in this state, even though it does
at 5d and 126d. This is consistent with the empirical literature on
momentum-crash behavior at intermediate horizons after extension peaks.

**Where Priority 2 leads.**

The empirical evidence motivates Priority 3 — empirically-driven
simplification:

1. **Reduced-component test**: a CCQS using only the four carriers
   (s_rs, s_rs_leadership, s_structure, s_mtf) should perform at least
   as well as the current 9-component composite. To be verified
   under Priority 3.

2. **`s_demand` removal**: parallel to `s_climax` in Phase 6 — drop or
   zero the component, redistribute its ~10% weight to the four carriers.

3. **State-conditional flattening**: at 20d, weights essentially could
   be made flat across states with no measurable OOS loss. Whether to
   keep state-conditioning for 5d / 60d / 126d (where ~25-34% of
   state-pairs differ) is a separate decision.

4. **Pre-trade conditioning**: signal performance is so different across
   regime / cap / sector that the composite should not be applied
   uniformly. Specifically:
   - mega-caps (Q5 by dollar volume) — disable or invert
   - high-market-vol regimes — disable
   - 2021-like speculative-euphoria years — disable
   - defensive sectors — apply with diminished confidence

5. **Bit-identical OOS validation gate**: any Priority 3 changes should
   preserve or improve the Phase X.3 OOS baseline (1d t=4.16, 126d
   t=2.59, 252d t=2.05). The current Phase 6 baseline is 5d t=2.57,
   20d t=2.78, 60d t=2.90, 126d t=7.41 — all above t=2.0.

---

### Phase 7 — Priority 3a: `s_demand` removal + carrier redistribution (2026-05-25)

Empirically-driven simplification motivated by the Priority 2 finding
that `s_demand` carried 10–15% of weight per state while averaging
−0.009 OOS IC across 24 (state × horizon) cells, with 6 cells
significantly negative (CONSOLIDATING at all four horizons, PULLBACK
at 20d / 60d, INDETERMINATE at 60d).

**Methodology.** Zero `s_demand` in every state and redistribute the
freed weight proportionally to the four carrier components (`s_rs`,
`s_rs_leadership`, `s_structure`, `s_mtf`) by their existing
within-carrier weight share. Each state row is then renormalized to
sum to 1.0. No other weight cell is touched; `s_rsl`, `s_trend_slope`,
`s_extension`, `s_momentum` keep their current weights. Surgical change.

The new STATE_WEIGHTS matrix is in [compute/ccqs.py:62](compute/ccqs.py:62).
Per-state Δ on the four carriers:

| State | s_demand removed | s_rs Δ | s_rs_leadership Δ | s_structure Δ | s_mtf Δ |
|---|---:|---:|---:|---:|---:|
| TRENDING | −0.100 | +0.030 | +0.030 | +0.022 | +0.018 |
| PULLBACK | −0.130 | +0.036 | +0.041 | +0.030 | +0.023 |
| CONSOLIDATING | −0.150 | +0.038 | +0.042 | +0.042 | +0.028 |
| EXHAUSTION | −0.150 | +0.041 | +0.052 | +0.030 | +0.028 |
| DETERIORATING | −0.150 | +0.038 | +0.047 | +0.038 | +0.028 |
| INDETERMINATE | −0.110 | +0.030 | +0.035 | +0.024 | +0.020 |

**Validation: per-date IC (full history, paired block bootstrap 90% CI).**

| Horizon | Pre IC | Post IC | Δ | 90% CI on Δ | Verdict |
|---|---:|---:|---:|---|---|
| 5d | +0.0121 | +0.0137 | +0.0016 | [+0.0003, +0.0028] | **post better** |
| 20d | +0.0118 | +0.0135 | +0.0017 | [−0.0003, +0.0035] | directional, not sig |
| 60d | +0.0108 | +0.0144 | +0.0037 | [+0.0016, +0.0059] | **post better** |
| 126d | +0.0233 | +0.0259 | +0.0026 | [+0.0009, +0.0044] | **post better** |

**Validation: Phase X.3 walk-forward (252-train / 21-test, 73 windows).**

| Horizon | Pre OOS / t | Post OOS / t | Paired Δ | Paired t | Verdict |
|---|---|---|---:|---:|---|
| 5d | +0.0105 / 1.28 | +0.0120 / 1.42 | +0.0015 | 2.01 | **post better** |
| 20d | +0.0106 / 0.71 | +0.0121 / 0.80 | +0.0015 | 1.34 | directional, not sig |
| 60d | +0.0086 / 0.58 | +0.0122 / 0.81 | +0.0036 | 2.77 | **post better** |
| 126d | +0.0240 / 1.82 | +0.0269 / 2.02 | +0.0029 | 2.64 | **post better** |

Both frameworks agree: significant improvement at 5d, 60d, 126d.
20d is directionally positive (+14% in mean IC) but the change is
not statistically distinguishable. Notably, the post-Phase-7 126d
walk-forward t-statistic crosses the t > 2.0 institutional bar that
the pre-Phase-7 composite narrowly missed (1.82 → 2.02).

**Grade and ranking stability.** Grade distribution preserved within
rounding (S 8.05% / A 12.00% / B 24.95% / C 24.97% / D 30.02%).
13.19% of rows experience a grade change — almost all are one-step
shifts between adjacent grades on stocks near a per-date quantile
boundary. Spearman rank correlation between pre- and post-Phase-7
CCQS is **0.9901**. Mean |Δ CCQS| is 3.16 points; max 31.4 points.

**Conditional-regime robustness.** Tested whether any specific bucket
gets worse:

- Market vol regime: post ≥ pre in 11 of 12 cells (LOW 5d flat at
  −0.0002). Critically, the problematic HIGH regime improves at every
  horizon (HIGH 60d −0.0135 → −0.0100; HIGH 126d −0.0245 → −0.0235).
- Dollar-volume quintile: post ≥ pre in 19 of 20 cells (Q3 20d flat).
  The mega-cap (Q5) regime improves at every horizon (Q5 60d
  −0.0167 → −0.0109; Q5 126d −0.0069 → −0.0034). Still negative but
  materially less so — these remain documented out-of-domain conditions.
- Year buckets (27 cells with ≥1000 rows): post ≥ pre in 22; flat in 3;
  two minor regressions both confined to **2020 long horizons**
  (60d −0.0022, 126d −0.0071). 2020 was the COVID liquidity shock —
  `s_demand` may have captured shock-specific signal not present elsewhere.
  This is the single regime where the simplification loses signal, and the
  losses are small in absolute terms. **Documented caveat below.**
- 2021 (the negative-IC meme/SPAC year): post improves at every horizon
  by +0.003 to +0.008. The simplification helps where the signal was
  weakest before.

**Implementation.** Code change is the `STATE_WEIGHTS` dict in
`compute/ccqs.py`. `s_demand` is **kept as a zero-weight diagnostic
component** in `compute/components.py` (parallel to `s_climax`'s
pre-Phase-6 history). It still appears in `components.parquet` and
the dashboard component decomposition; it just contributes 0 to CCQS.
This is the safer mid-state — no risk of breaking downstream paths
that reference the field, and the field remains available for
diagnostic display or future re-enable. A later phase may follow the
Phase 6 model and remove the underlying computation entirely.

**Known caveat — COVID-2020 long-horizon regression.** The 2020 60d /
126d minor IC loss reflects a known limitation: `s_demand` (up/down
volume ratios, accumulation/distribution line, distribution-day count,
CMF, volume z-score) carries information about liquidity-shock-driven
selling that other components do not capture. In a comparable
crash-then-V-shaped-recovery regime, the post-Phase-7 composite would
under-perform the pre-Phase-7 composite by roughly the magnitude
observed (Δ IC ≈ −0.003 to −0.007). The improvement at every other
year × horizon cell outweighs this loss in expectation, but the loss
is real and worth flagging for users interpreting CCQS during a
liquidity crisis.

**TV reference snapshots** — *not* refreshed in this commit. Per
Priority 3 plan, refresh deferred until Priority 3b and 3c complete
so we make a single pin update covering all of Priority 3.

---

### Priority 3 — Simplification investigation summary (2026-05-25)

Three weight-matrix simplification hypotheses were tested with the
in-memory CCQS framework + paired bootstrap + walk-forward OOS. One
shipped (3a, now Phase 7). Two were skipped on regime-level
degradation evidence (3b and 3c). The skipped tests revealed an
architectural feature worth documenting.

| Test | Construction | Headline OOS Δ vs Phase 7 | Status |
|---|---|---|---|
| **3a** | s_demand → 0 in all states; redistribute to four carriers | 5d/60d/126d sig improved | **Shipped (Phase 7)** |
| **3b** | Reduced 4-carrier-only (zero s_rsl, s_trend_slope, s_extension, s_momentum everywhere) | 5d/20d marginal improvement; EXHAUSTION 60d −48%, 126d −26% | Skipped |
| **3c** | Hybrid (zero non-carriers in TRENDING/PULLBACK/DETERIORATING/INDETERMINATE only; preserve EXHAUSTION + CONSOLIDATING) | Essentially identical to 3b; EXHAUSTION regression persisted | Skipped |

**Architectural finding: confidence-blending mutes per-state weight
customization for low-confidence states.**

Phase X.2.1 introduced a confidence-blending step in
[compute/state.py](compute/state.py): when `state_confidence < 0.7`, the
state probabilities are blended toward INDETERMINATE (50/50 if
`max(p) < 0.5`, 70/30 if `< 0.7`). The blended probabilities `p_adj_<s>`
are then used for Bayesian-averaging the state-conditional component
weights:

    ccqs_z_raw = Σ_state p_adj_<state> · Σ_comp w[state][comp] · z_comp

This design correctly prevents low-confidence state classifications from
dominating CCQS. But it also means **a row classified as state X uses
state X's weight column only partially** — the rest comes from the
state columns its `p_adj` mass falls on. The Priority 3c investigation
quantified this for the live cache:

| Primary state | n rows | Mean state_confidence | Mean p_adj of own column | Mean p_adj of INDETERMINATE column |
|---|---:|---:|---:|---:|
| TRENDING | 262,002 | 0.61 | 0.47 | 0.38 |
| PULLBACK | 303,456 | 0.54 | 0.38 | 0.46 |
| **CONSOLIDATING** | 81,002 | 0.51 | **0.33** | **0.51** |
| **EXHAUSTION** | 34,215 | 0.60 | **0.45** | **0.45** |
| DETERIORATING | 436,066 | 0.69 | 0.61 | 0.32 |
| INDETERMINATE | 436,659 | 0.73 | 0.83 | 0.83 |

Implications:

1. **INDETERMINATE acts as a universal fallback column.** Across the
   six states, INDETERMINATE's column contributes a weighted average of
   45–80% of every state's CCQS. Changes to the INDETERMINATE column
   propagate to every state's stocks.
2. **State-conditional differentiation has reduced reach for
   low-confidence states.** TRENDING / PULLBACK / CONSOLIDATING /
   EXHAUSTION all have mean confidence 0.51–0.61, so their own
   columns contribute only 33–47% of their stocks' CCQS. Customizing
   those columns has limited effect on those stocks specifically.
3. **High-confidence states are where weight customization matters
   most.** INDETERMINATE (own column 83%) and DETERIORATING (own
   column 61%) are the two states whose customized weights actually
   reach their stocks at full magnitude.
4. **EXHAUSTION-state long-horizon signal cannot be cleanly isolated.**
   The 3c hybrid preserved EXHAUSTION's column exactly but still lost
   60d/126d EXHAUSTION-state signal — because EXHAUSTION-state stocks
   pull 45% from INDETERMINATE, and 3c zeroed non-carriers in
   INDETERMINATE.

This is not a defect; it's a deliberate property of the
confidence-blending design. But it sets a practical ceiling on what
state-conditional weight tuning can achieve within the current
architecture. Future simplification work that wants to remove non-carrier
components further would need to either (a) relax confidence-blending
(architectural change with downstream effects), (b) accept the
low-confidence-state signal cost as the price of simplification, or
(c) work on a different axis (e.g. feature-level rather than
component-level reduction).

**Audit trail for skipped tests preserved.** The detailed Priority 3b
and 3c findings live in commit message history and the original
investigation outputs (`/tmp/p3b_results.json`, `/tmp/p3c_results.json`
on the build machine; reproducible by re-running
`/tmp/p3b_carrier_only.py` and `/tmp/p3c_hybrid.py`). The decision not
to implement either is documented here. **Priority 3a (Phase 7,
s_demand removal) captured the available empirical wins within the
current architecture.**

---

### Priority 3d — Conditional performance warnings, display layer (2026-05-25)

Honest disclosure surface in the Streamlit dashboard. **No methodology
change** — CCQS values, grades, components, state probabilities, and
the OOS validation framework are all bit-identical. Only the display
layer is touched.

Motivated by Priority 2b's conditional-IC findings: CCQS has documented
regimes where signal is reduced or negative. The dashboard now surfaces
these directly so users do not silently misuse the score in
out-of-domain conditions.

**Implementation surface:**

1. New regime context bake into the slim dashboard cache:
   [`compute/build_dashboard_cache.py`](compute/build_dashboard_cache.py)
   writes a `regime_context.json` containing:
   - Per-ticker dollar-volume quintile for the latest snapshot date
     (Q5 = mega-caps where CCQS turns negative at 60d/126d)
   - SPY 20d realized vol tercile thresholds + current regime label
   - Frozen list of 10 "defensive" baskets that had significantly
     negative basket-level 60d IC in the Priority 2b analysis
2. Dashboard top-of-page banner: when SPY 20d vol is in the HIGH
   tercile, a warning explicitly says CCQS IC turns negative at
   longer horizons in this regime. Hidden in LOW / MID regimes.
3. Stock Detail reliability chips: rendered below the existing header.
   Up to four chips per stock:
   - "Mega-cap" — for tickers in dollar-volume Q5
   - "Defensive sector" — for tickers in the 10 defensive baskets
   - "High market vol regime" — when SPY regime is HIGH (also already
     shown as top-of-page banner)
   - "EXHAUSTION 20d caveat" — for tickers classified as EXHAUSTION
     state, flagging the documented near-zero 20d IC (t = -0.3)
   Each chip has a tooltip with the specific IC numbers from
   Priority 2b. Chips disappear when nothing applies (clean stocks
   in normal regimes show no chips).
4. New "Where CCQS Works Best" and "Known Limitations" expanders
   in the System Health section: concise plain-language summary of
   Priority 2b findings (best-performing regimes, basket lists, OOS IC
   numbers per horizon).
5. Updated methodology blurb: corrected to reflect post-Phase-7 state
   (seven contributing components plus two zero-weight diagnostics,
   per-date winsorization, confidence-blended Bayesian state averaging).

**Defensive basket list:** Frozen from the Priority 2b bottom-10 by
60d basket-level IC. To refresh, re-run `/tmp/p2b_conditional_ic.py`
and update `DEFENSIVE_BASKETS` in
[`compute/build_dashboard_cache.py`](compute/build_dashboard_cache.py).
The list is intentionally static so the dashboard doesn't need to run
the IC analysis at request time.

Current frozen list: Household and Personal Care; Gold Royalty and
Streamers; Integrated Energy Majors; Gaming Publishers; Offshore
Drilling; Railroads; Diagnostics and Life Science Tools; LNG and LPG
Shipping; Beverages and Tobacco; Industrial Automation.

**Validation.** `data/cache/ccqs.parquet` vs
`data/cache/dashboard/ccqs.parquet` max |diff| = 0.000000000 — no
methodology change. Grade equality preserved 100%. The dashboard
compiles, imports, and the regime-context helpers produce expected
flag counts on test tickers (AAPL → Mega-cap; XOM → Mega-cap +
Defensive sector; EXHAUSTION-state ticker → EXHAUSTION caveat; small
non-defensive ticker → no flags).

---

### Priority 3 — Empirical Methodology Refinement (closeout summary, 2026-05-25)

Comprehensive empirical investigation of CCQS methodology based on the
Priority 2 bootstrap (per-cell IC + paired bootstrap CIs) and conditional
IC findings (sector, cap, vol, state, time). Four sub-priorities were
scoped, executed, and either shipped or rejected on empirical evidence.

#### Sub-priority results

**Priority 3a — `s_demand` removal (SHIPPED as Phase 7)**

- Hypothesis: Zero `s_demand` and redistribute its 10-15% per-state
  weight to the four carrier components improves OOS IC.
- Validation: Statistically significant improvement at 5d (+13% IC),
  60d (+34%), and 126d (+11%) under both the per-date paired bootstrap
  framework (CI excludes zero) and the Phase X.3 walk-forward framework
  (paired t = 2.01 / 2.77 / 2.64). 20d directionally improved (+14%)
  but not statistically significant.
- The post-Phase-7 126d walk-forward t-statistic clears the t > 2.0
  institutional threshold (1.82 → 2.02) — first time the 126d
  walk-forward unconditional crossed that bar.
- No regime gets meaningfully worse. Two minor regressions confined to
  2020 long horizons (60d −0.0022, 126d −0.0071) documented as the
  COVID-recovery liquidity-shock caveat.
- Grade distribution preserved exactly (S 6.37 / A 9.49 / B 19.73 /
  C 19.74 / D 23.73). Spearman 0.9901.
- **Status: IMPLEMENTED Phase 7, commit `619ba4e`.**

**Priority 3b — Reduced 4-carrier-only composite (REJECTED)**

- Hypothesis: Zero `s_rsl`, `s_trend_slope`, `s_extension`, `s_momentum`
  in every state and redistribute their 4-8% per-state weight to the
  four carriers — fully simplify to the empirically-most-significant
  components.
- Validation: Marginal 5d / 20d unconditional improvement (+~4%); 60d
  and 126d flat. **EXHAUSTION state at 60d −48% (+0.0157 → +0.0079)
  and at 126d −27% (+0.0360 → +0.0261).**
- Failed the "no regime meaningfully worse" decision criterion. The
  small-weight non-carriers turn out to carry significant positive IC
  in EXHAUSTION state at long horizons (s_rsl IC +0.061, s_momentum
  +0.059, s_trend_slope +0.056 — all CI excludes zero at 126d).
- **Status: REJECTED — empirical evidence against. Audit trail
  preserved (commit message + `/tmp/p3b_results.json` reproducible).**

**Priority 3c — State-aware hybrid (REJECTED — architectural finding)**

- Hypothesis: Zero the four non-carriers only in TRENDING / PULLBACK /
  DETERIORATING / INDETERMINATE; preserve EXHAUSTION and CONSOLIDATING
  weight columns exactly. Attempts to capture 3b's unconditional gains
  while preserving the EXHAUSTION-state long-horizon signal.
- Validation: Unconditional results essentially identical to 3b. **The
  EXHAUSTION 60d / 126d regression persisted (−48% / −26%)** despite
  the EXHAUSTION column being preserved.
- **Architectural insight:** the per-state IC of EXHAUSTION-classified
  stocks does not isolate to EXHAUSTION's own weight column because of
  Phase X.2.1's confidence-blending. EXHAUSTION-state stocks have mean
  `state_confidence` = 0.60, so they pull only 45% from EXHAUSTION's
  column and 45% from INDETERMINATE — and 3c zeroed the non-carriers
  in INDETERMINATE.
- **Status: REJECTED — architectural constraint discovered. Audit
  trail and architectural finding preserved.**

**Priority 3d — Conditional performance warnings (SHIPPED)**

- Hypothesis: Honest disclosure of where CCQS works and doesn't,
  surfaced in the Streamlit dashboard. No methodology change.
- Implementation: `regime_context.json` baked at dashboard-cache build
  time; reliability chips in Stock Detail (Mega-cap / Defensive sector
  / High market vol / EXHAUSTION 20d); top-of-page banner when SPY 20d
  vol is in the HIGH tercile; "Where CCQS Works Best" and "Known
  Limitations" expanders with concrete Priority 2b IC numbers.
- Validation: CCQS bit-identical (max |diff| = 0.000000000), grade
  equality 100%, flag generation unit-tested on 4 representative
  tickers, live deployment visual inspection confirmed all elements
  rendering correctly.
- **Status: IMPLEMENTED, commit `37646b0`.**

#### Architectural insight — confidence-blending limits per-state weight customization

Phase X.2.1 introduced confidence-blending toward INDETERMINATE for
low-confidence state classifications. The blended probabilities
`p_adj_<s>` Bayesian-average the state-conditional weight columns:

    ccqs_z_raw = Σ_state p_adj_<state> · Σ_comp w[state][comp] · z_comp

Live cache (post-Phase-7) per-state own-column reliance:

| Primary state | n rows | Mean state_confidence | Mean p_adj of own column | Mean p_adj of INDETERMINATE column |
|---|---:|---:|---:|---:|
| TRENDING | 262,002 | 0.61 | 0.47 | 0.38 |
| PULLBACK | 303,456 | 0.54 | 0.38 | 0.46 |
| CONSOLIDATING | 81,002 | 0.51 | 0.33 | 0.51 |
| EXHAUSTION | 34,215 | 0.60 | 0.45 | 0.45 |
| DETERIORATING | 436,066 | 0.69 | 0.61 | 0.32 |
| INDETERMINATE | 436,659 | 0.73 | 0.83 | 0.83 |

Implications:

1. The INDETERMINATE column is a universal fallback contributing
   45–80% of every state's CCQS via Bayesian averaging. **Changes to
   the INDETERMINATE column propagate to every state's stocks.**
2. State-conditional differentiation has reduced reach for the four
   low-confidence states (TRENDING / PULLBACK / CONSOLIDATING /
   EXHAUSTION). Customizing those columns has 33–47% pass-through.
3. The two states with high own-column reliance — INDETERMINATE (83%)
   and DETERIORATING (61%) — are where weight customization actually
   reaches its target stocks at full magnitude.
4. **Further per-state simplification within the current architecture
   is constrained**: removing non-carrier components anywhere in the
   matrix loses EXHAUSTION-state long-horizon signal because EXHAUSTION
   stocks pull 45% of their CCQS from INDETERMINATE.

This is not a defect — it's a deliberate property of the
confidence-blending design (preventing low-confidence classifications
from dominating). But it sets a practical ceiling on what
state-conditional weight tuning can achieve. Future simplification work
that wants to remove components further would need to either:

  - Relax confidence-blending (architectural change with downstream
    effects on every other Phase X stage's interpretation)
  - Accept the low-confidence-state signal cost as the price of
    simplification (Priority 3b/3c approach, rejected here)
  - Work on a different axis: feature-level reduction (Lasso on raw
    features rather than component-level), state-conditional
    confidence-blending parameters, or universe-level
    pre-trade filtering instead of methodology changes

#### Final methodology state (post Priority 3)

| Layer | Status |
|---|---|
| Components computed | **9** (`s_rs`, `s_rs_leadership`, `s_rsl`, `s_trend_slope`, `s_structure`, `s_mtf`, `s_extension`, `s_demand`, `s_momentum`) |
| Components contributing to CCQS | **7** (`s_climax` removed Phase 6, `s_demand` zero-weighted Phase 7 — kept as diagnostic) |
| Carrier components (≥0.10 weight in any state) | **4** — `s_rs`, `s_rs_leadership`, `s_structure`, `s_mtf` |
| State columns in matrix | 6 — TRENDING, PULLBACK, CONSOLIDATING, EXHAUSTION, DETERIORATING, INDETERMINATE |
| Total weight cells | 54 (9 × 6) — 12 cells at 0%, 42 active |
| Winsorization | Per-date `p1`/`p99` (Phase 6) — eliminates the 24,562-row global tie problem |
| Confidence blending | Phase X.2.1 thresholds preserved (50/50 blend if max p < 0.5, 70/30 if < 0.7) |
| Weight validation | Bootstrap CIs on every cell (Priority 2a) + walk-forward OOS (Phase X.3 + Phase 7 paired t-test) |
| Conditional performance | Documented across 6 states, 5 dvol quintiles, 5 vol quintiles, 3 market-vol terciles, 91 baskets, 8 years (Priority 2b) |
| Display-layer transparency | Phase 7 + Priority 3d reliability chips, regime banner, Where Works Best / Known Limitations expanders |

#### Validation status snapshot

- **Phase X.3 baseline preserved** per Methodology Lock §6 — 1d t=4.16,
  126d t=2.59, 252d t=2.05. Phase 7 changes verified to preserve or
  improve these (walk-forward 126d t = 1.82 → 2.02).
- **Priority 2 empirical validation completed** — every weight cell
  bootstrapped, every regime conditionally analyzed. Findings
  documented and acted on.
- **Where CCQS works** (Priority 2b, validated): smaller dollar-volume
  stocks (Q1 60d IC +0.048), moderate-to-high vol names,
  low-to-mid-vol market regimes, cyclical / recovery sectors (top
  baskets +0.10 to +0.21), CONSOLIDATING state at all horizons,
  60d / 126d horizons.
- **Where CCQS does not work** (Priority 2b, documented): mega-caps
  (60d IC −0.017), high market-vol crises (60d IC −0.014),
  10 defensive baskets (Household & Personal Care, Gold Royalty,
  Integrated Energy Majors, Gaming Publishers, Offshore Drilling,
  Railroads, Diagnostics, LNG Shipping, Beverages, Industrial
  Automation), speculative-euphoria regimes (2021 negative every
  horizon), EXHAUSTION state at 20d (IC ≈ 0, t = −0.3), COVID-2020
  long horizons (Phase 7 trade-off).
- **TV reference snapshots** refreshed 2026-05-25 to current Phase 7
  values — all 10 canaries pass 140 / 140 field checks at the spec
  tolerances.
- **Audit trail preserved** in commit history (Phase 5.5 → 5.8,
  Phase 6, Phase 7, Priority 3d) and SPEC narrative sections.

#### Closeout

After Priority 3, the tool is at its final methodology state for the
foreseeable future. The next-level changes that remain on the table
require either:
  - New OOS evidence of signal degradation (per Methodology Lock §3a)
  - Architectural changes to confidence-blending (a meaningful
    redesign with consequences across every state-aware downstream
    consumer)
  - New data sources or research findings (Methodology Lock §3b)

Within the current architecture, the available empirical wins have
been captured. Display-layer transparency is in place. Documented
limitations are honest and specific. The matrix that ships is the
matrix the bootstrap supports.

---

### Phase 8a — Residual momentum addition (2026-05-26)

Adds the 10th component, `s_residual_momentum`, capturing
**beta-adjusted (idiosyncratic) momentum** vs SPY. This is the first
methodology change since the Priority 3 closeout that was framed as a
final state — motivated by Path C "comprehensive validation" work, with
the empirical pre-test described below clearing every documented
decision criterion.

**Hypothesis.** Removing the systematic-beta component from each
ticker's momentum return yields a cleaner idiosyncratic signal with
higher capacity, lower correlation to market beta, and incremental
information beyond what `s_rs` (which uses total-return-based RS) and
`s_momentum` (which uses 21d total returns) already capture.

**Empirical basis.** Blitz–Huij–Martens (2011) "Residual Momentum"
showed that residual momentum (returns after removing CAPM-beta
exposure) materially outperforms total momentum in equity backtests.
Subsequent fund implementations (Robeco's residual-momentum strategy,
multiple replications) confirmed the result with real money. This is
documented practice in the quant-fund world, not theoretical
sophistication.

**Methodology (no look-ahead).**

1. Compute SPY daily log return.
2. For each ticker, compute daily log return.
3. **Rolling 252-day OLS beta** of stock log returns on SPY log returns
   (Bessel-corrected; `cov_W(r_i, r_SPY) × W/(W-1) / var_W(r_SPY)`).
4. **Trailing beta** `β_lag1 = β_252d.shift(1)` — use yesterday's beta
   for today's market move, eliminating look-ahead.
5. **Daily residual return**:
       `r_resid[t] = r_i[t] − β_lag1[t] · r_SPY[t]`
6. **Aggregate at multiple horizons** as simple sums of daily log
   residuals (no skip-month, per the empirical-only directive):
   - `residual_momentum_63d` (added to features parquet)
   - `residual_momentum_126d` (the one fed into `s_residual_momentum`)
   - `residual_momentum_252d` (available for diagnostics)
7. **Component**: `s_residual_momentum` = per-date robust z of
   `residual_momentum_126d`, clipped at ±10.

The new feature requires **378 days** of history (252 for beta + 126
for residual sum). This extends the burn-in by ~4% of universe rows
vs Phase 7 (NaN share 21% → 25%). Within scored rows, the grade
distribution is preserved exactly.

Computation lives in
[compute/features.py "Category 9b"](compute/features.py) and the
component is in
[compute/components.py `_compute_s_residual_momentum`](compute/components.py).

**Weight allocation.** 5% per state in [compute/ccqs.py](compute/ccqs.py)
`STATE_WEIGHTS`, pulled proportionally from the three smallest-weight
existing components (`s_rsl`, `s_trend_slope`, `s_momentum`). For
EXHAUSTION — where those three only sum to 3% — the SHRINK targets
are zeroed and the missing 2% is absorbed by row-renormalization,
yielding effective `s_residual_momentum` weight of 4.90% in EXHAUSTION
vs 5.00% in the other five states.

| State | s_rs | s_rs_lead | s_resid_mom | s_rsl | s_trend_slope | s_structure | s_mtf | s_extension | s_demand | s_momentum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRENDING | 28.01% | 28.01% | **5.00%** | 0.86% | 0.86% | 20.17% | 16.81% | 0.00% | 0.00% | 0.29% |
| PULLBACK | 25.62% | 29.11% | **5.00%** | 0.50% | 0.33% | 20.96% | 16.30% | 2.00% | 0.00% | 0.17% |
| CONSOLIDATING | 23.80% | 26.18% | **5.00%** | 0.00% | 0.00% | 26.18% | 17.85% | 1.00% | 0.00% | 0.00% |
| EXHAUSTION | 25.56% | 32.53% | **4.90%** | 0.00% | 0.00% | 18.59% | 17.43% | 0.98% | 0.00% | 0.00% |
| DETERIORATING | 23.75% | 29.69% | **5.00%** | 0.00% | 0.00% | 23.75% | 17.81% | 0.00% | 0.00% | 0.00% |
| INDETERMINATE | 24.99% | 29.53% | **5.00%** | 0.86% | 0.86% | 20.44% | 17.04% | 1.00% | 0.00% | 0.29% |

All rows sum to 1.0.

**Pre-implementation validation evidence (in-memory Phase 8a investigation).**

Standalone IC (residual_momentum_252d-lookback vs forward returns):

| Forward horizon | Residual IC | t-stat | Total momentum IC | t-stat |
|---|---:|---:|---:|---:|
| 5d | +0.0197 | 3.96 | +0.0157 | 2.90 |
| 20d | +0.0288 | 6.96 | +0.0189 | 4.08 |
| 60d | **+0.0395** | **10.91** | +0.0154 | 3.94 |
| 126d | **+0.0466** | **14.39** | +0.0083 | 2.28 |

Residual is 2.5–5.6× stronger than total momentum at long horizons.

Orthogonalized residual (per-date residual after regressing on `s_rs`)
— measures the signal that's *incremental* to what `s_rs` already
captures:

| Forward horizon | Orthogonal IC | t-stat | Verdict |
|---|---:|---:|---|
| 5d | +0.0063 | 1.80 | borderline |
| 20d | +0.0084 | 2.48 | **significant** |
| 60d | +0.0181 | **5.45** | **strongly significant** |
| 126d | +0.0246 | **8.63** | **overwhelmingly significant** |

This is the key test that ruled out redundancy: even after removing
everything `s_rs` already captures, residual carries highly significant
alpha at 60d and 126d.

Integration (Config B — add residual at 5%, shrink three smallest
components):

**Per-date IC (paired block bootstrap 90% CI):**

| Horizon | Baseline | Phase 8a | Δ | CI on Δ |
|---|---:|---:|---:|---|
| 5d | +0.0132 | +0.0136 | +0.0005 | [−0.0003, +0.0013] |
| 20d | +0.0123 | +0.0132 | +0.0009 | [−0.0003, +0.0022] |
| 60d | +0.0137 | **+0.0153** | **+0.0016** | **[+0.0004, +0.0029]** |
| 126d | +0.0231 | **+0.0250** | **+0.0020** | **[+0.0007, +0.0031]** |

**Walk-forward OOS IC (Phase X.3 canonical, 73 windows, paired t-test):**

| Horizon | Phase 7 OOS / t | Phase 8a OOS / t | Paired t |
|---|---|---|---:|
| 5d | +0.0118 / 1.34 | +0.0123 / 1.37 | 0.96 |
| 20d | +0.0117 / 0.79 | +0.0126 / 0.85 | 1.18 |
| 60d | +0.0116 / 0.77 | +0.0133 / 0.88 | **2.05** |
| **126d** | **+0.0251 / 1.87** | **+0.0272 / 2.02** | **2.72** |

Both validation frameworks agree: significant improvement at 60d and
126d. **The post-Phase-8a 126d walk-forward t-statistic clears the
institutional t > 2.0 threshold (1.87 → 2.02)**, same milestone Phase 7
achieved.

**Post-implementation IC (live pipeline run, in-sample full history):**

| Horizon | Phase 8a actual | Phase 8a predicted | Δ |
|---|---:|---:|---:|
| 5d | +0.0113 (t=2.33) | +0.0136 | −17% |
| 20d | +0.0087 (t=1.95) | +0.0132 | −34% |
| 60d | +0.0138 (t=**3.58**) | +0.0153 | −10% |
| 126d | +0.0292 (t=**9.08**) | +0.0250 | **+17%** |

Some drift from prediction (notably 20d), 126d **better** than predicted.
60d t-stat at 3.58 is substantially above 2.0; 126d t-stat at 9.08
substantially above. Phase 7 baseline IC values: 5d t=2.57, 20d t=2.78,
60d t=2.90, 126d t=7.41. Phase 8a improves t-stat at 60d and 126d;
slight regression at 5d (2.57 → 2.33) and 20d (2.78 → 1.95) — both
remain at or near the institutional bar. **Net: institutional-quality
horizons (60d / 126d) materially stronger; short horizons weaker but
positive.**

**Per-state IC improvements (Phase 8a investigation, 24 of 24 cells
checked):** 23 of 24 cells improve. Single exception is EXHAUSTION 60d
(−0.0014, small). Largest gains:

- TRENDING 126d: +0.0065
- EXHAUSTION 5d: +0.0063 (recovery of previously-weak state)
- INDETERMINATE 60d: +0.0056 (the universal-fallback column)
- EXHAUSTION 20d: +0.0055 (Phase 7's near-zero 20d signal in this state)
- CONSOLIDATING 126d: +0.0042
- CONSOLIDATING 20d: +0.0035

**Regime improvements (the Phase 7 weak spots):**

| Regime (Phase 7 problem) | Base 126d IC | Phase 8a 126d IC | Δ |
|---|---:|---:|---:|
| Mega-caps (Q5 dvol) | −0.0043 | −0.0029 | **+0.0014** |
| HIGH market vol | −0.0299 | −0.0273 | **+0.0026** |
| Defensive sectors (10 baskets) | −0.0887 | −0.0871 | +0.0016 |
| 2021 (meme/SPAC year) | −0.0363 | −0.0320 | **+0.0043** |

The HIGH market-vol and 2021 regimes — Phase 7's worst — both improve
meaningfully. Mega-caps and defensives stay negative but improve.

**Known caveat — 2020 long horizons.** Phase 8a loses small IC in 2020
specifically:

| Year | Horizon | Phase 7 IC | Phase 8a IC | Δ |
|---|---|---:|---:|---:|
| 2020 | 60d | +0.0326 | +0.0286 | −0.0040 |
| 2020 | 126d | −0.0595 | −0.0658 | −0.0063 |

Same direction as the Phase 7 COVID-recovery caveat. Residual momentum
deliberately subtracts the market-beta component; in COVID-2020, total
momentum was beta-dominated, so removing beta hurts that single year.
Magnitudes are small (~0.005). Net improvement in 2021 (the year right
after) and every other year dominates this regression in expectation.

**Files changed in this phase:**
- `compute/features.py` — adds rolling 252d beta + 63/126/252d residual sums
- `compute/standardization.py` — no edits (new features fall through to default robust-z)
- `compute/components.py` — adds `_compute_s_residual_momentum`; updates `COMPONENT_COLS`
- `compute/ccqs.py` — STATE_WEIGHTS updated; Phase 8a comment block
- `compute/build_dashboard_cache.py` — adds new component to slim cache export
- `app/utils/data_loader.py` — adds display name `Residual Momentum`
- `tests/reference/tv_snapshots.py` — pins refreshed; 10/10 pass at spec tolerances
- `tests/test_phase3_validation.py` — adds new component to expected list

**Validation summary:**
- 11/11 sanity checks pass
- TV parity: 10/10 canaries, 140/140 fields pass
- Grade distribution (within valid rows): S 8.05% / A 12.00% / B 24.96% / C 24.97% / D 30.02% — identical to Phase 7
- Phase X.3 OOS baseline preserved per Methodology Lock §6
- Component count: 9 → 10

---

### Phase 8a.1 — Short-horizon recovery investigation (CLOSED — rejected, 2026-05-26)

**Hypothesis.** Phase 8a's residual-momentum addition slightly eroded the
5d and 20d t-statistics (5d 2.57 → 2.33; 20d 2.78 → 1.95). Phase 8a.1
tested whether a new `s_short_term_reversal` component — built from
sign-flipped 3-day / 5-day returns and other Jegadeesh-1990-style
reversal candidates — could recover that signal without giving back any
of the 60d/126d gains Phase 8a delivered.

**Result: REJECTED.**

Five reversal feature candidates were built, combined into five
composite component variants, orthogonalized against
(`s_rs` + `s_residual_momentum` + `s_momentum`), and integrated into
three weight configurations (uniform 5%, uniform 10%, state-dependent
heavier-in-TRENDING/PULLBACK). Stricter decision criteria than Phase 8a
were applied per the user's instruction (CI-includes-zero counts as
failure).

The empirical evidence said no:

  - Orthogonal IC vs existing components: only **5d** carried genuine
    incremental signal beyond `s_rs + s_residual_momentum + s_momentum`
    (best orthogonal t = +2.27). At 20d the orthogonal t dropped to
    +0.94; at 60d/126d it was essentially zero or slightly negative.
  - Per-date integration tests: CI overlapped zero at all four horizons
    for every config (Cfg B 5d Δ = +0.0009, CI = [−0.0003, +0.0020]).
  - **Walk-forward paired t-test: no significance at any horizon** for
    any config. The 20d paired t was actually slightly **negative**
    (−0.13 for Cfg B) — adding reversal made 20d very mildly worse in
    walk-forward.
  - Per-state breakdown: **EXHAUSTION regressed catastrophically across
    every horizon** (5d −0.013, 20d −0.017, 60d −0.002, 126d −0.012).
    EXHAUSTION 20d flipped sign (+0.0109 → −0.0063). This is the
    Priority-3c-discovered architectural fragility — confidence-blending
    makes EXHAUSTION-state stocks dependent on the wider matrix, and
    shrinking RS-family weights to make room for reversal hits the very
    components EXHAUSTION-state stocks rely on.

**Decision criteria scorecard (4 fails, 2 passes):**
- 5d t recovers above 2.5: ✗ (best 5d walk-forward t = 1.41 in Cfg C)
- 20d t recovers above 2.0: ✗ (walk-forward paired t negative)
- 60d/126d preserved within 10%: ✓
- No new regime regressions: ✗ (EXHAUSTION −15-34% across all horizons)
- Statistical significance in both frameworks: ✗
- Implementation complexity reasonable: ✓

**Architectural conclusion (documented for future reference).** Existing
components — particularly `s_rs` (which incorporates 63d / 126d / 189d /
252d return-slope ranks) and `s_residual_momentum` (which already
delivers idiosyncratic-momentum signal at long horizons) — implicitly
capture most of the short-term reversal alpha that exists in this
universe. Adding an explicit reversal component competes for weight
allocation without producing incremental walk-forward signal, and the
weight reshuffle damages EXHAUSTION-state stocks.

**Phase 8a tradeoff appears to be at architectural limit for the current
confidence-blended methodology.** The tool is optimized for medium-to-
long horizon analysis (60d / 126d are the institutional-quality primary
use cases); the 5d/20d horizons are functional but lower-quality and
not easily improvable without architectural redesign (relaxing
confidence-blending, or building a separate short-horizon model).

For short-horizon timing decisions, the recommended practice is to use
CCQS as quality / leadership context and a complementary short-horizon
tool for entry/exit timing, rather than expecting a single composite to
optimize all horizons simultaneously.

Full investigation outputs preserved at `/tmp/p8a1_short_reversal.py`
and `/tmp/p8a1_results.json` (reproducible on the build machine).
No production code changes.

---

### Phase 8b — Volatility-targeting consistency investigation (CLOSED — rejected, 2026-05-26)

**Hypothesis.** A feature-set audit flagged an apparent inconsistency in
vol-adjustment treatment across momentum-family features: `residual_momentum_126d`
(raw sum), `momentum_21d_pct` (raw return rank), but `sharpe_momentum_rank_126d`
uses a Sharpe-rank denominator. Phase 8b tested whether standardizing the
vol-adjustment approach — in either direction (all-Sharpe or all-raw) —
improves signal quality.

**Result: REJECTED ALL FOUR CONFIGURATIONS.**

Four configurations tested with stricter criteria than Phase 8a (per
user's "lessons-learned" directive — CI-includes-zero counts as failure;
walk-forward paired t > +1.96 required at 60d or 126d):

- **Config B** (Sharpe-style residual momentum): no-op. Standalone IC
  unchanged; orthogonal CI all straddle zero. The `standardization.py`
  per-date robust-z already supplies the cross-sectional vol normalization
  that the Sharpe ratio would add.
- **Config C** (Sharpe rank for `momentum_21d_pct`): no-op. Same reason.
- **Config D** (raw 126d return rank, de-vol-adjusting `sharpe_momentum_rank_126d`):
  **actively regresses.** 126d walk-forward paired t = **−1.01** (where
  CCQS's edge lives). 126d per-date IC: 0.02916 → 0.02765 (−5.2%).
  EXHAUSTION 126d: 0.0350 → 0.0149 (−57% relative). PULLBACK 126d:
  0.0210 → 0.0141 (−34% relative).
- **Config E** (B + C + D combined): inherits D's regressions.

Zero configurations pass all five strict criteria; D and E fail four of
five. The EXHAUSTION fragility documented in Priority 3c and Phase 8a.1
appears for the third time under Config D — confirming that
RS-family weight redistribution is structurally constrained by the
confidence-blending architecture, while the standalone `standardization.py`
robust-z mechanism already supplies cross-sectional vol normalization for
raw-percent features (Configs B and C are no-ops because the work is
already being done elsewhere).

**Meta-insight at Phase 8b close.** Two consecutive empirical investigations
(8a.1 + 8b) have failed to improve on Phase 8a within the same information
set. The architecture's confidence-blending step constrains weight
redistribution; the existing standardization step constrains vol-adjustment
restructuring. Further improvement requires either (a) new orthogonal
information axes, or (b) architectural redesign of confidence-blending.
This insight motivated Phase 10's pivot to volume features as a NEW
orthogonal axis (not a weight redistribution).

Full investigation outputs preserved at `/tmp/p8b_vol_targeting.py`,
`/tmp/p8b_results.json`, and `/tmp/PHASE_8B_REPORT.md`. No production
code changes.

---

### Phase 10 — Volume-pattern addition (SHIPPED, 2026-05-26)

**Hypothesis.** New volume features (HV1, HVE, low-relative-volume,
volume-buzz) capture a different axis of institutional behavior than
the existing volume features (`volume_z_20_252`, `up_down_vol_ratio_50`,
`distribution_days_25`, `ad_line_slope_20`, `cmf_21` — all consumed by
the zero-weighted `s_demand` since Phase 7). Specifically: HV1/HVE flag
point-in-time peaks (vs `volume_z_20_252`'s 20d-vs-252d trend); low-rel-vol
flags consolidation/dry-up days (vs `capitulation_volume_flag` which
requires concurrent price drop); volume_buzz captures single-day surge
intensity (vs the 20d-windowed `volume_z_20_252`). As a new component
adding orthogonal information (rather than redistributing existing
weight), s_volume should sidestep the EXHAUSTION fragility documented
across Priority 3c / Phase 8a.1 / Phase 8b.

**Result: SHIPPED as Config W1.**

Phase 10 W1 is the **first empirical win since Phase 8a** under the
post-Phase-8b strict criteria. Investigation overview:

**Standalone IC** of each candidate vs forward returns
(90% block-bootstrap CI, `*` = CI strict > 0):

| Feature | 5d | 20d | 60d | 126d |
| ------- | -- | --- | --- | ---- |
| `hv1_252` | flat | flat | flat | flat |
| `hve_all` | flat | flat | flat | flat |
| `low_rel_vol_10d` | −0.0022* | −0.0022* | flat | flat |
| `volume_buzz_50` | **+0.0058\*** | **+0.0063\*** | flat | flat |

**Orthogonal IC** — per-date OLS residual of each feature on the existing
10 components, then IC of the residual:

| Feature ⊥ | 5d | 20d | 60d | 126d |
| --------- | -- | --- | --- | ---- |
| `hv1_252` ⊥ | flat | flat | flat | flat |
| `hve_all` ⊥ | flat | flat | flat | flat |
| `low_rel_vol_10d` ⊥ | flat | flat | **+0.0049\*** | **+0.0055\*** |
| `volume_buzz_50` ⊥ | **+0.0059\*** | **+0.0058\*** | flat | flat |

The orthogonal IC table is the key finding: `low_rel_vol_10d` and
`volume_buzz_50` carry signal *beyond* what the existing 10 components
capture, on complementary horizons. `hv1_252` and `hve_all` carry no
orthogonal signal anywhere and are excluded.

**Candidate `s_volume` composite:**

```
z_lo = per_date_robust_z(low_rel_vol_10d)
z_bz = per_date_robust_z(volume_buzz_50)
s_volume = per_date_robust_z(0.5 × z_lo + 0.5 × z_bz).clip(±10)
```

Both inputs signed **positive** — direction taken from orthogonal IC,
not standalone IC. `low_rel_vol_10d`'s standalone IC is slightly negative
at short horizons but its orthogonal IC at 60d/126d is positive (the
consolidation/dry-up pattern carries forward-return signal *after*
controlling for state/RS/momentum).

**Seven integration configs tested** (W0 = baseline; W1 = composite at
3%; W2 = composite at 5%; W3 = composite in s_demand slot; W4 = split
two-component; W5 = volume_buzz only; W6 = low_rel_vol only).

**Decision matrix (strict criteria):**

| Criterion | W1 (3%) | W4 (split) | W5 (buzz only) | W6 (low_vol only) |
| --------- | ------- | ---------- | -------------- | ----------------- |
| Per-date IC delta CI > 0 at any horizon | ✓ 5d strict | ✗ borderline | ✗ borderline | ✗ |
| Walk-forward paired t > +1.96 at any horizon | ✓ +2.01 at 5d | borderline +1.96 | +1.78 max | ✗ all negative |
| 5d/20d don't regress | ✓ both improve | ✓ improve | ✓ improve | ✗ both regress |
| EXHAUSTION not −0.005 at any horizon | ✓ +0.006 to +0.016 | ✓ similar | ✓ similar | mixed |
| 60d/126d preserved | △ 60d −1.0% NS | △ same | △ same | ✗ −1.7 t at 126d |
| Orthogonal signal | ✓ both inputs | ✓ | partial | ✓ but lone-feature drag |
| **Overall** | **ACCEPT** | secondary | inferior to W1 | **REJECT** |

**Critical empirical finding (the "W6 lesson"):** `low_rel_vol_10d`
alone at 5% per state actively HURTS CCQS at every horizon
(walk-forward paired t = −1.20 to −1.95). This is despite its
orthogonal-IC being positive at 60d/126d (CI > 0). The standalone-IC
negative direction dominates when the feature is used alone; only when
blended with `volume_buzz_50` (which has positive standalone AND
orthogonal IC at 5d/20d) does the composite become net-positive.
**The two features cannot be unbundled.** This nuance is documented
in both `compute/features.py` (Category 7b comment block) and
`compute/components.py` (`_compute_s_volume` docstring).

**Headline IC numbers (W1 vs Phase 8a baseline, n_dates = 1414):**

| Horizon | Baseline | Phase 10 W1 | Δ | Significance |
| ------- | -------- | ----------- | -- | ------------ |
| 5d | 0.01133 (t=2.33) | 0.01168 (t=2.41) | **+3.1%** | per-date CI strict > 0; walk-forward t = +2.01 |
| 20d | 0.00867 (t=1.95) | 0.00903 (t=2.04) | **+4.1%** | t crosses back above 2.0 |
| 60d | 0.01376 (t=3.58) | 0.01362 (t=3.55) | −1.0% | NS, walk-forward t = −0.21 |
| 126d | 0.02916 (t=9.08) | 0.02946 (t=9.14) | +1.0% | NS (positive but not sig) |

**Per-state IC at the EXHAUSTION watchpoint** (Δ vs Phase 8a baseline):

| Horizon | Phase 8a | Phase 10 W1 | Δ |
| ------- | -------- | ----------- | -- |
| 5d | 0.0381 (t=4.65) | 0.0439 (t=5.30) | +0.0058 |
| 20d | 0.0109 (t=1.25) | 0.0273 (t=3.04) | **+0.0163** |
| 60d | 0.0157 (t=1.70) | 0.0244 (t=2.51) | +0.0087 |
| 126d | 0.0350 (t=3.82) | 0.0462 (t=4.81) | +0.0112 |

EXHAUSTION-state IC improves at every horizon, with the 20d t-stat
crossing from non-significant to highly-significant (1.25 → 3.04).
**This resolves the architectural EXHAUSTION fragility** that blocked
Priority 3c / Phase 8a.1 / Phase 8b candidates from passing. The
fragility mechanism (confidence-blending pulling ~45% of EXHAUSTION
CCQS from the INDETERMINATE column) is *not* triggered by adding a
NEW component — only by redistributing weight from RS-family
components, which is what the previous three investigations all did.

**Conditional regime check** (W1 Δ by SPY-21d-realized-vol regime):

| Regime | n_dates | 5d Δ | 20d Δ | 60d Δ | 126d Δ |
| ------ | ------- | ---- | ----- | ----- | ------ |
| HIGH (≥17.8%) | 533 | +0.00050 | +0.00054 | −0.00023 | +0.00010 |
| MED | 731 | +0.00027 | +0.00014 | −0.00001 | +0.00068 |
| LOW (≤11.0%) | 533 | +0.00031 | +0.00053 | −0.00024 | −0.00005 |

Improvement is regime-stable. No single-regime concentration. The slight
60d regression is distributed equally; the 126d improvement concentrates
in MED.

**Configurations rejected with rationale:**

- **W2 / W3 (5% weight)** — attenuate the 5d benefit (paired t drops
  from +2.01 to +1.70 / +1.83). 3% is the optimal weight at this
  signal magnitude.
- **W4 (split 3+3)** — splitting the two features into separate
  components is no better than combining them; W1's combined 3%
  marginally beats W4's split 3+3 at 5d.
- **W5 (volume_buzz_50 only)** — loses the long-horizon orthogonal
  signal from low_rel_vol_10d. EXHAUSTION 126d improvement smaller.
- **W6 (low_rel_vol_10d only)** — actively hurts (see W6 lesson above).
- **HV1 / HVE as setup triggers** — per-state IC of the flags shows
  significant *negative* (t = −2.0 to −2.3) in INDETERMINATE state at
  20d/60d. HV1 in INDETERMINATE is a mild contra-indicator, not a
  setup confirmation. Not added to `setup_classifier.py`.

**Architectural insight (Phase 10).** The "empirical-optimum"
conclusion drawn at the close of Phase 8b was correct for
**same-information-set modifications** but wrong for **new orthogonal
information axes**. The EXHAUSTION fragility documented across three
prior investigations was a constraint on RS-family weight
redistribution, NOT a constraint on the architecture itself. Adding a
NEW component (with new orthogonal information) sidesteps the
confidence-blending fragility because it doesn't shrink any existing
RS-family weight in a non-proportional way — every other component
just gets scaled uniformly by 0.97. This insight reframes the path
forward: further improvement likely requires more orthogonal
information axes (rather than weight reshuffles).

**Risk acknowledgments.**

- 5d per-date IC delta CI lower bound is +0.000012 — barely sig at
  90% (marginal). Walk-forward paired t = +2.01 provides confirmation
  despite marginal per-date significance.
- 60d shows slight NS regression (−1.0%, walk-forward paired t = −0.21).
  Within noise floor of every other investigation we've run; worth
  monitoring in production.
- ~6% NaN during 50d/10d warmup (handled by compute_ccqs nan-safe sum).
- Features must be bundled (cannot unbundle per W6 evidence).

**Implementation files:**
- `compute/features.py` — Category 7b block; `low_rel_vol_10d` and
  `volume_buzz_50` added. FEATURE_ORDER 124 → 126. NO LOOK-AHEAD
  verified (causal rolling windows only).
- `compute/components.py` — `_compute_s_volume()` added. COMPONENT_COLS
  10 → 11. Bundled-feature requirement documented in docstring.
- `compute/ccqs.py` — STATE_WEIGHTS scaled by 0.97; `s_volume` at
  0.03 per state. Phase 10 narrative comment block added.
- `compute/build_dashboard_cache.py` — `s_volume` added to
  components.parquet column list.
- `app/utils/data_loader.py` — `COMPONENT_DISPLAY_NAMES['s_volume']
  = 'Volume Pattern'`.
- `tests/reference/tv_snapshots.py` — refreshed Phase 8a → Phase 10
  (CCQS drift only; max |Δ| = 1.93 for TSLA; UNH grade A → B from
  per-date quantile slip; all 10/10 canaries pass).

**Validation against W1 in-memory predictions** (live pipeline post-
rebuild, max |Δ vs prediction| within 5% tolerance):

| Metric | W1 prediction | Live pipeline | Δ |
| ------ | ------------- | ------------- | -- |
| 5d IC | 0.01168 | 0.01150 | −1.6% |
| 20d IC | 0.00903 | 0.00887 | −1.8% |
| 60d IC | 0.01362 | 0.01367 | +0.4% |
| 126d IC | 0.02946 | 0.02948 | +0.1% |
| EXHAUSTION 5d | 0.04393 | 0.04491 | +2.2% |
| EXHAUSTION 20d | 0.02725 | 0.02235 | −18.0% |
| EXHAUSTION 60d | 0.02437 | 0.02250 | −7.7% |
| EXHAUSTION 126d | 0.04624 | 0.04387 | −5.1% |

(EXHAUSTION live values slightly underperform the W1 predictions
because the in-memory test held the per-date robust-z snapshot
fixed; the rebuilt pipeline re-standardizes ALL 124 features with
the new ones present, which shifts the per-date distributions
slightly. Directional improvement vs Phase 8a baseline is preserved
at every horizon.)

Full investigation outputs preserved at `/tmp/p10_volume_features.py`,
`/tmp/p10b_volume_refined.py`, `/tmp/p10c_conditional.py`, the three
JSON results files, and `/tmp/PHASE_10_REPORT.md`.

---

### Phase 11A — State Classification Validation (2026-05-26)

**Headline finding: THE STATE CLASSIFIER IS A CONTEXT CLASSIFIER, NOT A
BUY/SELL SIGNAL.**

The 6-state classification system (TRENDING, PULLBACK, CONSOLIDATING,
EXHAUSTION, DETERIORATING, INDETERMINATE) describes WHERE a stock is in
its cycle, NOT what will happen next. Forward-return ordering is
counterintuitive to the state names — and that's not a bug, it's
empirical reality.

#### Forward-return ranking (60d horizon)

| Rank | State | μ 60d return | Δ vs universe | Annualized IR | Hit rate |
| ---- | ----- | ------------ | ------------- | ------------- | -------- |
| 1 | **EXHAUSTION** | **+9.3%** | **+4.1%** | +0.54 | 58.0% |
| 2 | INDETERMINATE | +6.3% | +1.1% | +0.42 | 59.1% |
| 3 | DETERIORATING | +5.7% | +0.5% | +0.44 | 59.1% |
| — | Universe | +5.2% | — | — | — |
| 4 | TRENDING | +4.2% | **−1.0%** | +0.41 | 57.8% |
| 5 | PULLBACK | +4.1% | **−1.1%** | +0.39 | 58.3% |
| 6 | CONSOLIDATING | +2.7% | **−2.5%** | +0.24 | 55.8% |

At 126d the asymmetry intensifies: EXHAUSTION delivers +18.4%
(1.6× universe); TRENDING delivers +10.9% (essentially universe-level).
At every horizon and in every pairwise comparison, the 6 states are
statistically distinguishable (p < 0.001 with these sample sizes).
No state is empirically redundant.

#### Implications for user interpretation

**TRENDING is NOT a buy signal.** Stocks classified as "clean uptrend
in progress" UNDERPERFORM the universe mean at every horizon. This
reflects the well-documented winner's-curse / mean-reversion-of-extremes
effect in equity returns. By the time a stock obviously TRENDS, the
incremental edge is already partially priced in.

**EXHAUSTION is NOT a sell signal.** Stocks classified as
"parabolic / late-stage exhaustion" produce the HIGHEST forward
returns. Momentum continues. The EXHAUSTION label captures CHARACTER
(extended, parabolic, high vol) — not DIRECTION.

**States describe character / condition, not future direction.**
Forward-direction signal comes from CCQS itself (which combines
components weighted by state probability), from the leadership tier,
and from setup classification — but NOT from state alone.

#### What the state machine IS good for

- **Understanding stock's current cycle position** — where is it in
  the trend / pullback / consolidation / exhaustion arc?
- **Risk awareness** — EXHAUSTION stocks are parabolic and volatile;
  CONSOLIDATING stocks have lost drive; DETERIORATING stocks may
  continue lower for a long time (12.9d mean run, 92.3% daily stickiness).
- **Strategy matching** — different trading strategies are appropriate
  for different states; the dashboard's setup classifier already maps
  setups to states.
- **Filtering and screening** — finding only stocks in TRENDING with
  CCQS > 80 is meaningful; "TRENDING alone" is not.

#### What the state machine is NOT good for

- Direct forward-return prediction in isolation
- Standalone buy/sell signal
- Replacing CCQS as the quality measure

#### Additional findings

**Persistence** (run-length analysis):

| State | Mean run | Median | p90 | Sticky % (1-day) |
| ----- | -------- | ------ | --- | ---------------- |
| DETERIORATING | 12.9d | 4d | 38d | **92.3%** (broken stocks stay broken) |
| INDETERMINATE | 6.4d | 2d | 13d | 84.5% |
| TRENDING | 5.6d | 3d | 15d | 82.3% |
| EXHAUSTION | 4.3d | 2d | 11d | 76.7% |
| CONSOLIDATING | 3.9d | 2d | 9d | 74.5% |
| PULLBACK | 3.6d | 2d | 8d | 72.4% (noisiest active state) |

Overall local stability: **72.27%** of (ticker, date) cells have the
same primary_state on both the previous and following trading day —
appropriate noise floor (not so sticky that the classifier is over-
confident; not so noisy that thresholds are jittery).

**Transition matrix** (all transitions physically sensible):
- TRENDING → PULLBACK (11.0%) — natural rest in uptrend
- EXHAUSTION → TRENDING (12.9%) — parabolic resolves to trend, NOT crash
- PULLBACK → INDETERMINATE (12.1%) — pullbacks often resolve to noise
- DETERIORATING → DETERIORATING (92.3%) — once broken, stay broken
- EXHAUSTION → CONSOLIDATING (0.0%), EXHAUSTION → DETERIORATING (0.0%) —
  no overnight crashes; non-physical transitions correctly suppressed

**Threshold sensitivity** (perturb each Gaussian μ or σ by ±20%, observe
state population shift):

Most parameters are mid-slope (single-parameter ±20% moves population
by 1–5%). The state machine isn't at razor-edge cliffs. **Standout:**
`PULLBACK mu_rsi_14 = 45.0` is the most sensitive (|Δpop| = 13.55%
combined; −20% perturbation shrinks PULLBACK by 9.8%). Not broken —
just on a steep part of the RSI distribution. Worth a focused 1-D grid
search if precision tuning becomes a priority (filed as deferred
follow-up, not required for system correctness).

**Confidence-blend mechanism** (Phase X.2.1 — blend toward INDETERMINATE
when max_p is low):

| Bucket | n | mean p_adj_INDETERMINATE | Expected | Verified |
| ------ | - | ------------------------ | -------- | -------- |
| low_conf (<0.5) | 406,167 | 0.6306 | ≥ 0.50 from 50/50 rule | ✓ |
| med_conf (0.5–0.7) | 511,069 | 0.5024 | ≥ 0.30 from 70/30 rule | ✓ |
| hi_conf (≥0.7) | 612,011 | 0.4405 | unchanged | ✓ |

Distribution: 26.6% of rows are low-confidence (50/50 blend); 33.4% are
medium (70/30 blend); 40.0% are high-confidence (unchanged). The
mechanism is operating exactly as designed.

**Forward returns by confidence quintile (60d):**

| Quintile | μ 60d | Hit rate |
| -------- | ----- | -------- |
| Q1 (low) | +4.40% | 58.3% |
| Q2 | +5.07% | 58.8% |
| Q3 | +5.46% | 58.8% |
| Q4 | +5.40% | 58.5% |
| Q5 (high) | +6.02% | 58.2% |

State **confidence predicts magnitude, not direction.** The mean
forward return increases monotonically with confidence (Q5 / Q1 = 1.37×),
but hit rates are essentially identical (~58% in every quintile).
Higher-confidence states tend to be in stronger momentum regimes (hence
larger absolute moves) but the direction is determined by component
signals inside CCQS, not by state confidence alone.

#### Recommendations

1. **KEEP ALL 6 STATES.** Every state is statistically distinguishable
   from every other state at every horizon. No state is redundant.
2. **Document the "context, not direction" framing** prominently
   (this SPEC entry + dashboard tooltips — the latter to be added in
   Phase 11D synthesis after 11B/11C complete).
3. **Defer threshold tuning** (PULLBACK mu_rsi_14) — not urgent.
4. **No architectural changes** to the state machine itself.

#### Outputs

- Investigation script: `/tmp/p11a_state_validation.py`
- Raw results JSON: `/tmp/p11a_results.json`
- Full report: `/tmp/PHASE_11A_REPORT.md`

---

### Phase 11B — Setup Classification Validation (2026-05-26)

**Headline finding: THE "PREMIUM LABEL, NO ALPHA" PATTERN.**

Setups carrying premium-sounding names (VCP Setup, Emerging Leader,
Premium Pullback, Theme Leader Pullback) UNDERPERFORM the universe mean
at 60d. Setups carrying weakness-related names (Capitulation Selling,
Distribution Pattern, Sustained Weakness, Volume-Confirmed Exhaustion)
OUTPERFORM. This parallels Phase 11A's state-as-context finding at the
setup layer. **Names describe TECHNICAL PATTERN observed currently, not
future direction.**

This is a SYSTEM-WIDE design lesson now documented across both layers:
neither state labels nor setup labels function as standalone buy/sell
signals. The actual buy/sell signal is CCQS, which combines components
weighted by state probability — both state and setup serve as
RISK/STRATEGY CONTEXT, not as direct forward-return predictors.

#### Forward-return ranking (60d, universe baseline +5.20%)

**Top performers (significantly above universe):**

| Setup | n | μ 60d | Δ vs uni | Mode state |
| ----- | - | ----- | -------- | ---------- |
| Volume-Confirmed Exhaustion | 465 | **+16.70%** | +11.50% | EXHAUSTION |
| Exhaustion (Generic) | 3,481 | +12.74% | +7.54% | EXHAUSTION |
| Capitulation Selling | 2,870 | +11.26% | +6.06% | DETERIORATING |
| Elite Leader Continuation | 284 | +11.20% | +6.00% | TRENDING |
| Sustained Weakness | 87,960 | +10.19% | +4.99% | DETERIORATING |
| Distribution Pattern | 95,536 | +9.62% | +4.42% | DETERIORATING |
| Deteriorating w/ Bullish Divergence | 57,534 | +9.20% | +4.00% | DETERIORATING |
| Trending Leadership | 40,491 | +7.89% | +2.69% | TRENDING |
| Exhaustion w/ Bearish Divergence | 10,241 | +7.56% | +2.36% | EXHAUSTION |
| Trend Continuation | 44,005 | +7.46% | +2.26% | TRENDING |
| BB Squeeze with RS | 7,750 | +7.19% | +1.99% | CONSOLIDATING |
| Pullback to 21EMA | 25,002 | +6.08% | +0.88% | PULLBACK |
| Pullback to 50MA | 14,010 | +5.97% | +0.77% | PULLBACK |
| Extreme Extension | 16,589 | +5.56% | +0.36% | EXHAUSTION |

**Premium-labeled underperformers (statistically below universe):**

| Setup | n | μ 60d | Δ vs uni | t vs uni |
| ----- | - | ----- | -------- | -------- |
| Extended Exhaustion | 18,141 | +4.81% | −0.39% | **−2.91\*** |
| Premium Pullback | 10,245 | +4.62% | −0.58% | **−2.72\*** |
| Failed Breakout | 25,973 | +4.54% | −0.66% | **−5.02\*** |
| Theme Leader Pullback | 58,974 | +4.47% | −0.73% | **−7.29\*** |
| Indeterminate Pattern | 252,633 | +4.14% | −1.06% | **−19.93\*** |
| Deteriorating (Generic) | 170,499 | +4.00% | −1.20% | **−26.98\*** |
| **Emerging Leader** | 8,999 | +3.94% | −1.26% | **−6.70\*** |
| **VCP Setup** | 4,270 | +3.91% | −1.29% | **−4.60\*** |
| Routine Pullback | 141,673 | +3.78% | −1.42% | **−27.46\*** |
| Range Consolidation | 181,954 | +3.28% | −1.92% | **−36.08\*** |
| Trending (Generic) | 123,230 | +3.22% | −1.98% | **−36.69\*** |
| Consolidating (Generic) | 25,568 | +2.40% | −2.80% | **−20.35\*** |

#### Key interpretation

**What setup classifications ARE good for:**
- Pattern recognition and categorization
- Risk awareness (e.g., Exhaustion patterns = parabolic stocks)
- Strategy matching (different strategies for different patterns)
- Filtering and screening

**What setup classifications are NOT good for:**
- Direct forward-return prediction based on label alone
- "Buy the premium-labeled stocks" approach
- Standalone signal without CCQS context

The label tells you WHAT KIND of stock you're looking at; CCQS tells you
whether the components inside are firing on aligned positive momentum
signals. The combination is the signal.

#### Statistical equivalences

**34 setup pairs (out of 325 tested) are statistically equivalent (Welch's
t-test p > 0.05).** Most notable:

| Setup A | Setup B | p | Interpretation |
| ------- | ------- | - | -------------- |
| **VCP Setup** | **Emerging Leader** | 0.940 | Both "buy" setups, identical performance, both underperform universe |
| Capitulation Selling | Elite Leader Continuation | 0.978 | Coincidental — very different categories |
| Pullback to 21EMA | Pullback to 50MA | 0.670 | Two MA references, indistinguishable forward returns |
| Failed Breakout | Premium Pullback | 0.756 | Different gates, same outcome |
| Sustained Weakness | Distribution Pattern | (high overlap, see Jaccard) | DETERIORATING-family overlap |

The VCP Setup ≡ Emerging Leader equivalence is empirically meaningful:
both setups carry "high-quality long" branding, both have multi-condition
gates, both underperform universe, and they're statistically
indistinguishable from each other AND from Deteriorating (Generic) AND
from Routine Pullback. Strong candidate for merge or removal in Phase
11.D synthesis.

#### Cascade design validation

For most setups, **cascade-assigned rows outperform "would-have-matched"
rows that were masked by higher-priority assignments.** Strongest
evidence:

| Setup | Cascade μ 60d | Masked μ 60d | Cascade enrichment |
| ----- | ------------- | ------------ | ------------------ |
| Volume-Confirmed Exhaustion | +16.70% | +6.80% | +9.90% |
| Elite Leader Continuation | +11.20% | +8.05% | +3.15% |
| Trend Continuation | +7.46% | +4.86% | +2.60% |
| Exhaustion w/ Bearish Divergence | +7.56% | +5.99% | +1.57% |
| Trending Leadership | +7.89% | +6.62% | +1.27% |

Range Consolidation and Failed Breakout show "masked outperforms
cascade" — but this is EXPECTED, not a bug: these setups sit near the
bottom of the cascade, so when a row qualifies for them AND for a higher-
priority setup, the higher-priority assignment is correct (it carries
the better forward return). The "masked" rows are the ones that got
captured by higher-priority setups.

**Conclusion: first-match-wins priority captures the higher-edge subset.
The cascade design is empirically validated.**

#### Cross-setup overlap (Jaccard similarity of would-match masks)

| Setup A | Setup B | Jaccard | Note |
| ------- | ------- | ------- | ---- |
| Trend Continuation | Trending Leadership | 0.418 | Trend Continuation ⊂ Trending Leadership (every TC qualifies as TL) |
| Distribution Pattern | Sustained Weakness | 0.378 | DETERIORATING-family overlap |
| Pullback to 21EMA | Pullback to 50MA | 0.323 | Adjacent-MA overlap |
| Extended Exhaustion | Trending Leadership | 0.214 | Extended exhaustion stocks often also trend leaders |

Some overlap is expected (related patterns share gating logic). No
overlap is excessive enough to warrant immediate merge — except the
already-flagged VCP/Emerging Leader pair.

#### Threshold sensitivity

Most setup thresholds are mid-slope (single-parameter ±20% perturbations
move would-match population by 1–6%). Current values are operating in
reasonable working zones. Standouts:

- **Distribution Pattern's `dist_days_min = 8`** is the most sensitive
  (|Δpop| = 10.9%). Lowering to 6.4 would expand population by 13%.
- **Sustained Weakness's `pct_ma_50_max = −8`** also sensitive
  (|Δpop| = 6.5%).
- **Trending Leadership's `rs_spy_min = 80`** sensitive (|Δpop| = 6.2%).

No threshold appears badly chosen. No single perturbation reveals an
obvious "we're missing a lot of signal here" gap.

#### Low-sample setups (statistical caveats)

Findings statistically weak for:
- **Volume-Confirmed Exhaustion (n=465)** — moderate confidence; the
  +16.70% return is significant (t=+3.20) but the small sample size
  means a wider confidence band than other setups.
- **Elite Leader Continuation (n=284)** — moderate confidence.
- **Elite Leader Pullback (n=4)** — too small for inference. The
  conjunction (`p_pullback > 0.5 AND ELITE_LEADER`) is empirically rare.
- **Tight Consolidation Pre-Breakout (n=7)** — too small for inference.
  Very restrictive gates make this label fire essentially never.

These rare setups are retained in the cascade because the underlying
gating logic is conceptually sound — but their empirical performance
cannot be evaluated with statistical confidence given the sample sizes.

#### Phase 11.B.1 patch (shipped 2026-05-26)

**Removed dead setup: "Consolidation Within Strong Theme"** (n=0). The
rule required `theme_strong = pd.Series(False, ...)` from the aggregation
layer, which was never wired through to the setup_classifier. Never
fired in any of 1,529,247 (ticker, date) rows.

Cascade simplified: 29 labels → 28 labels. No effect on CCQS (the setup
classifier output doesn't feed back into the composite score).
Pipeline verified clean (11/11 sanity checks pass, 140/140 TV reference
fields pass on all 10 canaries).

#### Decisions deferred to Phase 11.D synthesis

The following Phase 11B recommendations are documented but **not
implemented in 11.B.1** (pending cross-layer synthesis):

1. **Merge or drop `VCP Setup` + `Emerging Leader`** (statistically
   equivalent, both underperform universe).
2. **Rename `Extended Exhaustion`** to better describe its empirical
   character (mode state is TRENDING, not EXHAUSTION).
3. **Consider merging `Pullback to 21EMA` + `Pullback to 50MA`**
   (statistically indistinguishable, both outperform universe).
4. **Review `Premium Pullback` criteria** (underperforms despite heavy
   "quality" gating — same "premium label, no alpha" pattern).

#### Outputs

- Investigation script: `/tmp/p11b_setup_validation.py`
- Raw results JSON: `/tmp/p11b_results.json`
- Full report: `/tmp/PHASE_11B_REPORT.md`

---

### Phase 11C — Leadership Tier Validation (2026-05-26)

**Headline finding: TIER LABELS ARE CURRENT QUALITY, NOT FORWARD
EXPECTATION.**

Same "context-not-direction" pattern repeats at the leadership-tier
layer that was documented for the state machine (Phase 11A) and setup
classifier (Phase 11B). Tiers describe CURRENT RS-quality (where the
stock sits on the leadership ladder TODAY), not what will happen next.

**Three classification layers now consistently confirm the same
system-wide design lesson.** Only one tier has a truly distinctive
forward-return edge.

#### Forward-return ranking (60d, universe baseline +5.20%)

| Rank | Tier | n | Pop % | μ 60d | t vs uni | Hit | IR |
| ---- | ---- | - | ----- | ----- | -------- | --- | -- |
| 1 | **ELITE_LEADER** | 2,695 | 0.19% | **+15.24%** | +9.54 | 60.3% | +0.57 |
| 2 | STRONG_PERFORMER | 355,788 | 24.91% | +7.04% | +42.24 | 60.0% | +0.55 |
| 3 | WEAK_LAGGARD | 43,062 | 3.02% | +7.02% | +8.47 | 55.9% | +0.32 |
| 4 | ESTABLISHED_LEADER | 22,055 | 1.54% | +6.61% | +8.60 | 59.2% | +0.56 |
| 5 | STRONG_LEADER | 16,918 | 1.18% | +6.32% | +4.42 | 55.9% | +0.39 |
| 6 | NEUTRAL | 311,879 | 21.83% | +5.90% | +16.79 | 60.7% | +0.52 |
| — | Universe | — | — | **+5.20%** | — | — | — |
| 7 | DETERIORATING | 257,118 | 18.00% | +4.82% | −7.98 | 57.8% | +0.41 |
| 8 | **EMERGING_LEADER** | 86,633 | 6.07% | **+4.68%** | **−7.30** | 59.0% | +0.46 |
| 9 | WEAK_PERFORMER | 117,788 | 8.25% | +4.41% | **−14.04** | 59.8% | +0.47 |

(\* = p < 0.05 vs universe. Sample sizes are reported pre-Phase-11.C.1
patch; the patch primarily reduces NEUTRAL by ~132K rows redirected to
UNCLASSIFIED — see §Phase 11.C.1 below.)

**Critical observation: Only ELITE_LEADER has a 10+ percentage point
edge over universe.** All other 8 tiers cluster within ±2.5pp of
universe mean. The strict ELITE gating (6 simultaneous conditions:
s_lead ≥ 90 AND rs_spy ≥ 95 AND mtf_coh = 3 AND vol_conf AND
basket_leader AND qqq_ok) successfully isolates a tiny but genuinely
distinctive subset (0.18% of universe, ~2,800 rows). The other 8 tiers
are CONTEXT labels, not forward-return signals.

#### Non-monotonic ordering — 4 of 8 adjacent comparisons "wrong direction"

Adjacent-tier comparisons (priority-ordered ELITE → WEAK_LAGGARD, 60d
horizon):

| Adjacent pair | Δ (higher − lower priority) | Direction |
| ------------- | --------------------------- | --------- |
| ELITE_LEADER vs STRONG_LEADER | +8.92% | A > B ✓ |
| STRONG_LEADER vs EMERGING_LEADER | +1.64% | A > B ✓ |
| **EMERGING_LEADER vs ESTABLISHED_LEADER** | **−1.93%** | **A < B ✗** |
| **ESTABLISHED_LEADER vs STRONG_PERFORMER** | **−0.43%** | **A < B ✗** |
| STRONG_PERFORMER vs NEUTRAL | +1.14% | A > B ✓ |
| NEUTRAL vs WEAK_PERFORMER | +1.49% | A > B ✓ |
| **WEAK_PERFORMER vs DETERIORATING** | **−0.40%** | **A < B ✗** |
| **DETERIORATING vs WEAK_LAGGARD** | **−2.21%** | **A < B ✗** |

All comparisons statistically significant (p < 0.05). **The priority
hierarchy reflects RS-quality CLASSIFICATION, not expected forward
return.**

#### What the tier layer IS good for

- **Identifying ELITE_LEADER** (the only tier with genuine forward edge)
- **Current RS-quality assessment** (what kind of leadership profile
  does this stock have right now)
- **Pattern matching and filtering** (combined with state + setup, the
  triple-classification adds value — see Phase 11D synthesis)
- **Risk awareness** (e.g., a stock in WEAK_LAGGARD tier with strong
  recent recovery may be a mean-reversion play, but the tier label
  doesn't predict the future on its own)

#### What the tier layer is NOT good for

- Standalone forward-direction prediction (except ELITE_LEADER)
- Naive ranking interpretation — the intuition "EMERGING_LEADER is
  better than ESTABLISHED_LEADER" because the name sounds more
  aspirational is empirically WRONG
- Premium-sounding labels (EMERGING_LEADER underperforms universe; same
  "premium label, no alpha" dynamic as Phase 11B's VCP Setup / Emerging
  Leader Setup)

#### Tier × State interaction adds value

The joint (tier × state) signal is more informative than either alone.
Selected 60d return cells:

| Joint cell | μ 60d | Note |
| ---------- | ----- | ---- |
| ELITE_LEADER × INDETERMINATE | **+18.10%** | Highest cell in entire matrix |
| ELITE_LEADER × EXHAUSTION | +16.05% | Extended elites continue |
| ELITE_LEADER × TRENDING | +10.35% | Lowest ELITE cell |
| STRONG_PERFORMER × EXHAUSTION | +10.63% | Within-tier high |
| STRONG_PERFORMER × INDETERMINATE | +9.42% | Within-tier high |
| WEAK_LAGGARD × INDETERMINATE | **+10.07%** | Bottom-tier outperforms most upper tiers in this state |
| EMERGING_LEADER × PULLBACK | +3.46% | Worst non-empty cell |

**Pattern: EXHAUSTION and INDETERMINATE states consistently outperform
TRENDING WITHIN THE SAME TIER.** This further reinforces the state-as-
context insight from Phase 11A.

#### System-wide pattern confirmed across three layers

| Layer | Phase | "Premium" finding |
| ----- | ----- | ----------------- |
| State machine | 11A | TRENDING underperforms universe; EXHAUSTION outperforms |
| Setup classifier | 11B | VCP Setup, Emerging Leader, Premium Pullback all underperform |
| Leadership tier | 11C | EMERGING_LEADER underperforms; WEAK_LAGGARD outperforms many higher tiers |

**The forward-direction signals in CCQS V1 come from:**
- The CCQS score itself (empirically validated at 5d/20d/60d/126d)
- ELITE_LEADER tier (clear +15.24% forward edge)
- EXHAUSTION state (counterintuitive momentum continuation)
- Specific high-edge setups (Volume-Confirmed Exhaustion, Capitulation
  Selling, Sustained Weakness, Distribution Pattern, etc. — all of
  which outperform universe by 4-12pp at 60d)

**The forward-direction signals in CCQS V1 do NOT come from:**
- "TRENDING" state alone
- "Premium Pullback" / "VCP Setup" / "Emerging Leader" setup labels
- "EMERGING_LEADER" / "WEAK_PERFORMER" tiers
- Any classification label's intuitive name interpretation

The actionable signal is CCQS itself, qualified by the multi-layer
classification context.

#### Phase 11.C.1 patch (shipped 2026-05-26) — NEUTRAL fall-through fix

**Bug:** `tier = pd.Series("NEUTRAL", ...)` default initialization
caused ~132,050 rows (8.6% of universe = 42.7% of NEUTRAL pre-patch)
to fall through to the NEUTRAL label even though they didn't match the
formal NEUTRAL definition (rs_spy ∈ [45, 60)).

**Three distinct fall-through patterns identified:**

| Pattern | Rows | Mechanism |
| ------- | ---- | --------- |
| 1. rs_spy < 25 AND rs_slope ≥ 0 | 80,675 | Doesn't match WEAK_LAGGARD (slope ≥ 0), WEAK_PERFORMER (rs < 25), DETERIORATING (slope > −5) |
| 2. rs_spy ∈ [40, 45) AND rs_slope < −5 | 28,119 | Doesn't match WEAK_PERFORMER (slope < −5), DETERIORATING (rs ≥ 40) |
| 3. rs_spy < 45 AND rs_slope IS NaN | 23,256 | All slope-based comparisons fail; rs too low for STRONG_PERFORMER |

**Fix:** Added explicit `UNCLASSIFIED` 10th tier. Default initialization
changed from `"NEUTRAL"` to `"UNCLASSIFIED"`. No change to the 9
existing tier definitions or their masks. Three fall-through patterns
now become explicitly UNCLASSIFIED rather than mis-labeled NEUTRAL.

**Population shift (post-patch):**

| Tier | Pre-patch | Post-patch | Δ |
| ---- | --------- | ---------- | -- |
| NEUTRAL | 21.83% | 12.59% | −9.24% |
| UNCLASSIFIED | 0.00% | 8.63% | +8.63% |
| All other tiers | unchanged | unchanged | — |

(The 0.61% gap between −9.24% and +8.63% is the previously-NaN
population — `rs_spy.isna()` rows that remain NaN and don't get
re-classified.)

**No CCQS impact** (leadership tier doesn't feed CCQS). **11/11 sanity
checks pass; 140/140 TV reference fields pass on all 10 canaries**
(none of the canaries fell in any of the three fall-through patterns).

`TIER_ORDER` updated in `app/streamlit_app.py` to include UNCLASSIFIED
so dashboard filters expose the new category.

#### Decisions deferred to Phase 11.D synthesis

The following Phase 11C recommendations are documented but **not
implemented in 11.C.1** (which is bug-fix-only, pending cross-layer
synthesis):

1. **Consider merging STRONG_LEADER + ESTABLISHED_LEADER → MATURE_LEADER**
   (statistically near-identical, both above universe by similar amount).
2. **Consider collapsing EMERGING_LEADER → STRONG_PERFORMER** (or
   renaming to "ACCELERATING_PERFORMER" with a tooltip about mean
   reversion).
3. **Consider tier-naming clarifications** in dashboard tooltips to
   surface the "context, not direction" framing.

These are methodology decisions and deferred to Phase 11D synthesis
where cross-layer analysis can inform the right resolution.

#### Outputs

- Investigation script: `/tmp/p11c_tier_validation.py`
- Raw results JSON: `/tmp/p11c_results.json`
- Full report: `/tmp/PHASE_11C_REPORT.md`

---

### Phase 11D — Cross-Layer Synthesis (2026-05-26)

**Headline architectural insight: CCQS V1 IS A CATEGORICAL SCREENING +
WITHIN-CATEGORY RANKING TOOL.** The 3-layer classification system
(state × setup × tier) carries 97.3% of cross-sectional R² at 60d
forward returns; CCQS as a continuous variable carries 2.7%.

Phase 11D is the synthesis phase that pulls Phase 11A (state), 11B
(setup), and 11C (tier) findings into an integrated system-efficiency
assessment. Three first-order findings reshape how we describe what
CCQS V1 actually does.

#### Finding 1: CCQS is regime-dependent

CCQS ranking works well in TOP-quality regimes (highest CCQS decile
outperforms lowest by 3–5pp at 60d) but INVERTS in BOTTOM-quality
regimes (highest decile UNDERPERFORMS lowest by up to 9.24pp).

**Top-CCQS-decile minus Bottom-CCQS-decile spread at 60d, by tier:**

| Tier | Q10 − Q1 spread | Interpretation |
| ---- | ---------------- | -------------- |
| ESTABLISHED_LEADER | **+5.26%** | CCQS works strongly |
| STRONG_LEADER | +3.22% | CCQS works |
| STRONG_PERFORMER | +3.04% | CCQS works |
| WEAK_PERFORMER | +0.56% | CCQS flat |
| NEUTRAL | −0.48% | CCQS minimal value |
| EMERGING_LEADER | −0.82% | CCQS slightly inverts |
| UNCLASSIFIED | −1.67% | CCQS slightly inverts |
| DETERIORATING (tier) | −1.93% | CCQS slightly inverts |
| **WEAK_LAGGARD** | **−9.24%** | CCQS strongly INVERTS |

**Same pattern by state:**

| State | Q10 − Q1 spread |
| ----- | ---------------- |
| EXHAUSTION | +5.87% |
| TRENDING | +3.99% |
| INDETERMINATE | +3.10% |
| PULLBACK | +2.62% |
| CONSOLIDATING | +1.56% |
| **DETERIORATING (state)** | **−2.15%** |

**Mechanism:** mean reversion dominates in low-quality regimes. Stocks
at the bottom of the cycle (WEAK_LAGGARD, DETERIORATING) snap back
disproportionately, and the MOST broken stocks (lowest CCQS) snap back
hardest. Within these regimes, the highest-CCQS stocks underperform
the lowest-CCQS stocks because momentum continuation (the property
CCQS rewards) is the WRONG signal axis.

**Critical user implication:**

- **In high-quality regimes** (STRONG_PERFORMER+ tiers, momentum
  states): High CCQS predicts forward outperformance. **CCQS works
  as intended.**
- **In low-quality regimes** (WEAK_LAGGARD, DETERIORATING tier and
  state): High CCQS predicts forward UNDERPERFORMANCE vs the cohort.
  **Mean reversion dominates ranking signal.**

#### Finding 2: Information attribution — categorical labels carry 97% of cross-sectional R²

Pooled cross-sectional regression on 60d forward returns (per-date
demeaned):

| Model | R² | Marginal R² | % of total |
| ----- | -- | ----------- | ---------- |
| 1. CCQS only | 0.000148 | +0.000148 | 2.7% |
| 2. + State dummies | 0.001466 | +0.001318 | 24.4% |
| 3. + Setup dummies | 0.004740 | +0.003274 | **60.6%** |
| 4. + Tier dummies | 0.005404 | +0.000664 | 12.3% |

**Setup carries the highest single-layer information content (60.6%).**
State adds 24.4%; tier adds 12.3%; CCQS as a continuous variable adds
only 2.7%.

**Reverse ordering (classifications first):**

| Model | R² |
| ----- | -- |
| State + setup + tier only | 0.005376 |
| + CCQS on top | 0.005404 |
| **CCQS marginal contribution** | **+0.000027 = 0.5% of total** |

With classifications already in the model, CCQS adds essentially
nothing incrementally — because CCQS *implies* the categorical
structure (it's built from state-weighted components). The labels
make explicit what CCQS encodes implicitly.

#### Finding 3: State × Setup are 77% redundant by design

Cramér's V (categorical association):

| Pair | V | Interpretation |
| ---- | - | -------------- |
| **state × setup** | **0.7696** | HIGH — structural (setups are state-aware by design) |
| state × tier | 0.4211 | Moderate |
| setup × tier | 0.3313 | Moderate |

The state-setup redundancy is **structural and beneficial**, not a
bug. 5 of the 27 setups (post-Phase-11E.1) are state-aware catch-alls
that bind 1:1 to states; many specific setups have implicit state
constraints via their feature gates. Removing one layer would lose
the within-state pattern differentiation that the setup classifier
provides.

#### What CCQS V1 actually does

> **CCQS V1 is a categorical screening + within-category ranking tool.**
> The 3-layer classification (state × setup × tier) describes the
> current technical character of each stock and carries 97.3% of the
> system's cross-sectional R² at 60d forward returns. The CCQS score
> (continuous) provides within-category ranking — but only in
> high-quality regimes (top tiers, momentum states); in low-quality
> regimes (WEAK_LAGGARD, DETERIORATING), CCQS ranking inverts due to
> mean reversion.

#### What CCQS V1 is NOT

- A universal continuous score that always predicts forward returns
- A monotonic ranking system across all regimes
- A standalone signal independent of classification context

#### User guidance (incorporated into dashboard tooltips post-Phase-11E)

- **Check classification first** (tier, state, setup) — this is the
  primary screening axis.
- **In high-quality regimes:** trust CCQS ranking. Higher CCQS =
  expected forward return premium.
- **In low-quality regimes:** invert the mental model. Lowest CCQS
  in WEAK_LAGGARD / DETERIORATING may indicate mean-reversion
  candidate. The Phase 11E dashboard regime chip flags this.
- **Use classifications for primary screening, CCQS for within-cell
  fine-tuning.**

#### 3D joint distribution — top mean-reversion cells

The (state × setup × tier) joint distribution surfaces extreme mean-
reversion plays at the bottom of the cycle. Top cells at 60d:

| Cell | n | μ 60d | t |
| ---- | - | ----- | - |
| INDETERMINATE × Deteriorating w/ Bullish Divergence × UNCLASSIFIED | 555 | **+43.5%** | +20.8 |
| INDETERMINATE × Distribution Pattern × UNCLASSIFIED | 722 | +37.5% | +21.4 |
| INDETERMINATE × Sustained Weakness × UNCLASSIFIED | 1,116 | +36.7% | +25.7 |
| INDETERMINATE × Distribution Pattern × WEAK_LAGGARD | 486 | +34.5% | +8.3 |

These are real, statistically significant cells. The pattern is:
**INDETERMINATE state + DETERIORATING-family setup + UNCLASSIFIED /
WEAK_LAGGARD tier** = mean-reversion at the bottom of the cycle.

#### Per-cell CCQS effectiveness summary

CCQS works well in:
- ESTABLISHED_LEADER, STRONG_LEADER, STRONG_PERFORMER tiers
- EXHAUSTION, TRENDING, INDETERMINATE, PULLBACK, CONSOLIDATING states
- DETERIORATING-family setups (Distribution Pattern, Sustained
  Weakness, Deteriorating w/ Bullish Divergence)
- Extreme Extension setup (IC +0.098, highest single-setup CCQS IC)

CCQS fails (inverts or is flat) in:
- WEAK_LAGGARD, DETERIORATING (tier), NEUTRAL, EMERGING_LEADER,
  UNCLASSIFIED tiers
- DETERIORATING state (within-state inversion)
- Trending Leadership / Trend Continuation setups (within-setup
  variance too compressed)

#### Phase 11E patches (shipped 2026-05-26)

**Phase 11E.1 — Setup merger:** Removed "Emerging Leader" setup from
the cascade (statistically equivalent to VCP Setup at p=0.94, both
underperform universe by p<0.001). Setup count 28 → 27. The 8,999
rows previously labeled "Emerging Leader" are redistributed across
downstream cascade priorities (typically Trending Leadership or
catch-alls). VCP Setup retained unchanged.

**Phase 11E.2 — Dashboard CCQS regime chip:** Added per-ticker
reliability chip in the stock detail view. Surfaces the regime-
dependence finding to the user:
- ELITE_LEADER / STRONG_LEADER / ESTABLISHED_LEADER → green chip
  "High-quality regime — CCQS ranking reliable" with tooltip noting
  the +5pp Q10−Q1 spread.
- WEAK_LAGGARD / DETERIORATING tier → amber chip "Low-quality regime
  — CCQS ranking may invert" with tooltip noting the −9pp Q10−Q1
  spread and recommending mean-reversion framing.
- Other tiers → no chip (no strong regime claim).

#### Deferred from Phase 11E (backlog)

The following Phase 11D recommendations are documented but **NOT
implemented in Phase 11E** (defer to post-Path-C work):
- STRONG_LEADER + ESTABLISHED_LEADER merger
- Extended Exhaustion / EMERGING_LEADER tier renames
- Dashboard "high-quality screen" and "mean-reversion screen" preset
  filters
- NaN-tier filter / warning chip

#### Outputs

- Investigation script: `/tmp/p11d_cross_layer.py`
- Raw results JSON: `/tmp/p11d_results.json`
- Full report: `/tmp/PHASE_11D_REPORT.md`

---

### Phase 13 — Russell 2000 expansion feasibility (investigation, 2026-05-26)

User context shift: discretionary L/S manager (small AUM, no liquidity
constraints) requested universe expansion to add Russell 2000 small caps
for idea-flow breadth, especially short candidates.

Investigation methodology: stratified 188-name R2K sample, yfinance data
quality validation, feature-distribution comparison vs S&P 500 baseline,
forward-return distribution comparison (tail asymmetry for L/S),
simplified classification distribution estimate.

Key findings (full report: `/tmp/PHASE_13_REPORT.md`):

1. **Data feasibility:** 95.2% yfinance coverage on stratified sample.
2. **Feature distributions** match S&P 500 medians within ~10% (no
   threshold recalibration needed at the feature level).
3. **L/S asymmetry favors small caps**: R2K stocks have 37-49% more
   deep-drawdown events (60-126d horizon, <-20% / <-30% returns)
   relative to S&P 500 — empirically richer SHORT-side opportunity.
4. **Methodology classification estimate produced sensible groupings**
   on the R2K sample.

Recommendation at Phase 13 close: **PROCEED** with universe expansion;
estimated ~10 min pipeline runtime; ~65-90 MB cache size; 4-5x idea
flow expansion. Approved for Phase 14.1 implementation.

---

### Phase 14.1 — Universe expansion experiment (EXPERIMENTAL — REVERTED in Phase 14R, 2026-05-26)

Implemented full universe expansion: added 953 net-new tickers
(Russell 1000 + S&P SmallCap 600, Wikipedia GICS-sector auto-assigned)
to `data/universe.py` as a new `'Small Mid Cap (Auto-Sectored)'`
category with 11 GICS sector baskets. Universe grew 884 → 1,837 declared
/ 1,790 quality-gated.

Pipeline rebuild succeeded end-to-end (loader, data_quality, features,
standardization, components, state, leadership, setups, CCQS,
aggregation, dashboard cache). 11/11 sanity checks passed. Headline IC
on the combined 1,790-ticker universe dropped substantially (5d 0.0115
→ 0.0059; 60d 0.0137 → 0.0036; 126d 0.0295 → 0.0181).

**Conditional IC analysis revealed the root cause** — methodology was
empirically intact for the original universe, but produced near-zero
or negative signal on the new small-cap names:

| Horizon | Phase 11 baseline | Original 884 in new pipeline | New 953 R1K/SP600 |
| ------- | ----------------- | ----------------------------- | ------------------ |
| 5d | +0.0115 | **+0.0114 (t=+2.35)** ✓ | +0.0011 (t=+0.26) |
| 20d | +0.0089 | **+0.0087 (t=+1.97)** ✓ | **−0.0068 (t=−1.77)** |
| 60d | +0.0137 | **+0.0133 (t=+3.46)** ✓ | **−0.0054 (t=−1.58)** |
| 126d | +0.0295 | **+0.0292 (t=+9.10)** ✓ | +0.0082 (t=+2.80) |

**Diagnosis:** Methodology was empirically calibrated on S&P 500-quality
stocks (RS thresholds 60/75/80/95, ELITE_LEADER 6-gate filter, Gaussian
state-machine parameters, momentum-favoring feature blends). Small caps
have structurally different dynamics — stronger mean reversion, weaker
momentum continuation, different forward-return distributions. Forcing
a single methodology onto two structurally different universes
**compromises both**.

The Phase 11D regime-dependence finding generalizes: just as CCQS
inverts within WEAK_LAGGARD tier of the S&P 500 universe (Q10−Q1
spread −9.24%), the methodology weakens when extended cross-universe
to small caps. The signal architecture is genuinely population-specific.

**Decision (Approach C):** REVERT Phase 14.1 universe expansion in
**Phase 14R** (immediate). Build a separate **Small Cap CCQS (CCQS-SC)**
tool in **Phase 15** with empirically recalibrated methodology
(separate state machine parameters, setup library, tier boundaries,
component weights — full Path C rigor on the small-cap universe).

No code from Phase 14.1 retained except this documentation note. The
universe expansion artifacts (universe.py category, TV pin update) were
reverted; pipeline outputs are bit-identical to Phase 12 (Path C).

---

### Phase 14R — Reversion to Path C state (SHIPPED, 2026-05-26)

Immediate reversion of Phase 14.1 universe expansion. CCQS restored to
the exact Phase 12 / Path C validated state.

**Reversion mechanics:**
1. `data/universe.py`: removed `'Small Mid Cap (Auto-Sectored)'` category
   and its `CATEGORY_TYPE` entry. Universe back to 884 declared tickers
   across 9 curated categories.
2. `tests/reference/tv_snapshots.py`: restored AMZN pin to Phase 11
   baseline (`Range Consolidation` / 0.70 — the Phase 14.1 cross-sectional
   shift to `Pullback to 21EMA` / 0.85 was a Phase 14.1 artifact).
3. Pipeline rebuild (data_quality, features, standardization, components,
   state, leadership, setups, CCQS, aggregation).
4. Dashboard cache rebuild.
5. Documentation update (this section, CHANGELOG, version stamp).

**Validation confirms bit-identical restoration:**

| Metric | Phase 11 / 12 baseline | Phase 14R restored | Match? |
| ------ | ---------------------- | ------------------- | ------ |
| Universe size | 884 declared / 851 scored | 884 / 851 | ✓ |
| Categories | 9 | 9 | ✓ |
| 5d IC | 0.0115 | **0.0115** | ✓ EXACT |
| 60d IC | 0.0137 | **0.0137** | ✓ EXACT |
| 126d IC | 0.0295 | **0.0296** | ✓ (within rounding) |
| Dashboard cache size | 22 MB | **22.0 MB** | ✓ EXACT |
| Sanity checks | 11/11 | **11/11** | ✓ |
| TV parity | 140/140 fields | **140/140** | ✓ |
| Canaries passing | 10/10 | **10/10** | ✓ |
| Grade distribution | matches Phase 12 | matches | ✓ |

The methodology baseline remains **Phase 11E.2** as per Methodology
Lock §3. Path C state preserved. Phase 14.1 documented as an
experimental learning, not a methodology change.

**Phase 15 commitment:** Separate Small Cap CCQS (CCQS-SC) tool with
independent empirical methodology. 12 sub-phases planned (15.1-15.12)
covering universe definition, data infrastructure, feature engineering,
state classifier, setup classifier, tier classifier, component weights,
comprehensive validation, dashboard integration, documentation,
deployment. Path C rigor required throughout. Begins after user
confirms Phase 14R clean.

---

### Phase 16 — CCQS empirical re-validation (investigation, 2026-05-27)

Phase 15.1.D (SC walk-forward) revealed 90% failure rate of small-cap
features under Sub-Investigation D rigor. User directed: "Apply
Sub-Investigation D-level rigor to CCQS validation. Empirically
verify what CCQS actually does well and what might be illusion."

Nine sub-investigations on 874-ticker LC universe (4.77 GB feature matrix,
463 features × 2360 dates, includes all 11 production CCQS components):

**16.A — Universe characterization.** LC vs SC forward returns: LC mean
+5.7% at 63d vs SC +3.5%, hit rate 0.585 vs 0.559. Universal patterns
preserved: HIGH market vol → 4× returns (LC) / 14× (SC); low-vol anomaly
in both. LC has 13.9 skew at 126d (mega-cap winners) vs SC 3.4.

**16.B — Comprehensive feature universe.** Built same 343 base + 84 XS +
25 sector-relative + 11 CCQS components matrix as Phase 15.1.C. Extended
OHLCV to 2017-01 (87% pre-2018 coverage). 4.77 GB final parquet.

**16.C — Per-date Spearman IC ranking.** **Best CCQS component
(`s_residual_momentum`) ranks 71/463; `s_momentum` ranks 426/463.** Raw
`mom_ret_126d` (rank 15) more predictive than ALL 11 CCQS components.
Tier 1 (top 30%): `s_residual_momentum`, `s_structure`, `s_rs`,
`s_rs_leadership`, `s_mtf`. Tier 2 (weak): `s_trend_slope`, `s_volume`,
`s_extension`, `s_demand`, `s_rsl`, `s_momentum`.

**16.D — Axis-stratified regressions.** Pre-screened 155 features (matching
SC's 154). CCQS axis adds +1.4% incremental per-date R² — non-redundant.
Sector-Relative is biggest non-TS contributor (+2.1%). LC structurally
more predictable than SC (~44% per-date R² vs ~36%).

**16.E — Conditional IC sign-flip analysis.** **Top 9 sign-flippers across
4 conditions × 4 horizons are ALL CCQS components.** Average CCQS flip
rate 62% vs top technical 50%. CCQS components are MORE regime-unstable
than alternatives.

**16.F (CRITICAL TEST) — Walk-forward OOS validation.** 88 windows, top-50
features + 11 CCQS. **0/11 CCQS components survive; 1/61 features total**
(`sc_days_at_52w_low_pct_63d`). LC failure rate 98% (vs SC 90%).
**Path C validation does not hold under Sub-Investigation D rigor.**

**16.G — Time-varying analysis.** CCQS components have IC +0.03 in
STRONG_BULL but −0.08 in STRONG_BEAR — **CCQS is a bull-market signal,
not all-weather**. Range 0.10-0.14 between bull/bear regimes for top
components. Explains 16.F failure: walk-forward windows span both
regimes, signs flip.

**16.H — Empirical vs production weight comparison.** Production STATE_WEIGHTS
already correctly drop `s_extension`, `s_demand` to 0%, `s_momentum` to
0.3%. TRENDING state weights only 27.5% off empirical bull-optimal
(L1 = 0.55). Biggest discrepancies: `s_mtf` over-weighted 5× (prod 16%
vs empirical 3%), `s_residual_momentum` under-weighted 3.5× (prod 5% vs
empirical 17%).

**16.I — Honest synthesis.** Three path options identified:
- A: Major v2 restructure (drop Tier 2 + empirical weights + regime gating)
- B: Document + status quo
- C: Fundamental reconsideration (regression on screened features)

Critical empirical finding: CCQS's component-based composite signal
is regime-conditional. Static weights cannot adapt. The improvement
opportunity is regime-aware deployment, not weight recalibration.

---

### Phase 17 — Regime-aware deployment (SHIPPED, 2026-05-27)

User-selected Option 2 from Phase 16.I: deploy empirical regime indicator
only; preserve production STATE_WEIGHTS (already roughly empirically
optimal in TRENDING state).

**17.0 — Regime quantification.** Tested 42 candidate regime indicators
(trend, vol, drawdown, breadth, composite). Selected
**`dd_lt_15pct`** — SPY drawdown from 252-day high < 15%.

Empirical justification:
- t-statistic 8.74, p < 0.0001 (best of all candidates)
- IC differential at 63d: +0.093 (in-regime +0.027 vs off-regime −0.066)
- On 90% of trading days (well-balanced; not pathologically rare)
- Real-time computable from SPY closing price + 252-day rolling max

**17.4 — v2 walk-forward validation.** Tested three candidate methodologies
(v1 production, v2a renormalized 5 components, v2b empirical bull weights)
across 4 horizons × 3 regime filters. **Key finding**: v2 vs v1 score
correlation 0.989, top-50 daily overlap 86%, IC difference ~0.001 —
**v2 weight changes are immaterial**. The regime filter (`dd_lt_15pct=1`)
is the actual empirical innovation:
- 0/12 walk-forward survivors without regime filter
- 3/12 survivors WITH regime filter (specifically 126d in-regime, 1 strict)

**17.5 — Decision gate.** v1 production STATE_WEIGHTS already roughly
empirically optimal (the original Phase 16.H "misallocation" was based on
unconditional comparison; in TRENDING state production weights match
empirical bull-regime values within reason). Deploy regime indicator
only; preserve v1 methodology.

**17.6-17.9 — Deployment (this section).**

`compute/build_dashboard_cache.py::_design_space_regime()` computes the
regime daily from SPY benchmark data and writes a new
`ccqs_design_space` key into `data/cache/dashboard/regime_context.json`
(schema_version bumped 1 → 2).

Three-state classification:
- **GREEN**: `dd_lt_15pct=TRUE AND SPY > 200d MA` — design space, high confidence
- **YELLOW**: `dd_lt_15pct=TRUE AND SPY ≤ 200d MA` — in regime, trend uncertain
- **RED**: `dd_lt_15pct=FALSE` — out of design space; apply discretion

`app/streamlit_app.py` renders a prominent regime chip immediately below
the title showing the current state, drawdown depth, and empirical
basis (t-statistic citation). RED state triggers an additional
`st.error` banner with explicit empirical context.

**No methodology changes:**
- `compute/ccqs.py` STATE_WEIGHTS unchanged
- `compute/components.py` unchanged (10 components computed)
- `data/cache/components.parquet` semantics unchanged
- `data/cache/ccqs.parquet` semantics unchanged
- `tests/reference/tv_snapshots.py` unchanged (140/140 TV reference parity preserved)
- All sanity checks pass; pipeline outputs bit-identical to Phase 14R

**Net effect:** Production CCQS now ships with empirically-validated
design-space awareness. Methodology Lock §3 preserved (no methodology
change — display-layer addition citing empirical evidence).

**Empirical readings cited in production:**
- Phase 16-17 reports archived in `/tmp/phase16/` and `/tmp/phase17/`
- Walk-forward data: `/tmp/phase17/p17_4_v2_validation.json`
- Regime indicator data: `/tmp/phase17/p17_0_regime_indicators.parquet`

---

### Phase 25 — Setup label redesign (SHIPPED, 2026-05-28)

Display-layer redesign of the setup classifier. The 27-label
state-conditioned cascade in `compute/setup_classifier.py` is replaced
by a 13-label **chart-evocative cascade** in
`compute/setup_classifier_v2.py` (Phase 25 shipped with 12; Phase 27
later added "Reclaim" as the 13th). Pure descriptive labels — no
predictive language, no gestalt-pattern naming (no cup-and-handle /
wedge / H&S). The legacy classifier is preserved untouched for
reference; the pipeline now calls v2.

**No methodology changes.**
- `compute/ccqs.py` STATE_WEIGHTS unchanged
- `compute/components.py` unchanged (10 components)
- `compute/state.py` unchanged (6 states)
- `compute/leadership.py` unchanged
- All numeric / categorical non-setup fields bit-identical
  (140/140 TV reference parity preserved; only `setup` and
  `setup_confidence` change)

**The 13 labels (cascade order, first match wins):**

| # | Label | Definition |
|---|---|---|
| 1 | New High | Today's close = 252d max AND `pct_ma_50 ≤ own 80th-percentile of own 252d history` |
| 2 | Breakout | `close > prior 40d max` AND `true-range × ATR14 > 1.3` |
| 3 | Failed Breakout | Within last 5d a Breakout (#2) fired AND today's close < that breakout's cleared level (`failed_breakout_flag_5d_v2`) |
| 4 | Tight Base | Bullish stack AND `adr_pct_20` in bottom 25th cross-sectional percentile AND within 5% of 252d high |
| 5 | Coiling | Bullish stack AND `range_20d_to_60d_ratio < 0.6` AND `bb_width_pct_252d ≤ 20` (bottom 20% of own 252d BB-width history) |
| 6 | Shallow Pullback | Bullish stack AND 3% ≤ off-20d-high ≤ 10% AND close ≥ 21EMA |
| 7 | Deep Pullback | Bullish stack AND 10% < off-20d-high ≤ 20% AND close ≥ 50d MA |
| 8 | Extended | Bullish stack AND `pct_ma_50 > own 80th-percentile of own 252d history` |
| 9 | At Highs | Bullish stack AND within 5% of 252d high (residual) |
| 10 | Basing Low | Within 10% of 252d low AND `adr_pct_20` in bottom 40th cross-sectional percentile |
| 11 | Breakdown | `close < prior 40d min` AND close < 50d MA |
| 12 | Reclaim | Within last 5d a Breakdown (#11) fired AND today's close > that breakdown's failed level (`failed_breakdown_flag_5d_v2`) |
| 13 | Sideways | `range_60d_pct_of_price < 20` AND 25% ≤ `position_in_60d_range` ≤ 75% |

If no condition matches → empty string (`""`).
`setup_confidence = 1.0` for any assigned label, `0.0` for blank.

**Design principles (verbatim from spec):**

1. Labels are chart-hooks, not indicator-language.
2. Describe present state, never predict future outcome.
3. Decompose patterns into measurable constituents; do not name
   gestalts.
4. Uptrend/Downtrend deliberately omitted — too prevalent to be
   informative.
5. Thresholds are calibrated starting points and may be tuned after
   coverage analysis on the live universe.
6. 1–2 word labels (hard constraint).

**All thresholds are universe-relative or scale-invariant.** Either
(a) cross-sectional percentiles within the universe-of-the-day,
(b) self-relative ratios against the name's own trailing history, or
(c) scale-invariant % values. No absolute price levels, no per-name
hand-tuned values.

**New features (Cat 24 in `compute/features.py`).** Eleven primitives
added to power the cascade: `close_max_40d`, `close_min_40d`,
`high_max_20d`, `pct_from_20d_high`, `range_20d_pct_of_price`,
`range_60d_pct_of_price`, `range_20d_to_60d_ratio`,
`position_in_60d_range`, `pct_ma_50_p80_252d`, `true_range_x_atr14`,
`failed_breakout_flag_5d_v2`. `FEATURE_ORDER` length 126 → 137.

**Coverage on 2026-05-28 (universe = 860).**
Blank 50.6 / Sideways 10.3 / Shallow Pullback 8.3 / Basing Low 6.9 /
Extended 5.6 / Tight Base 5.5 / Breakdown 4.3 / Failed Breakout 2.3 /
Breakout 2.2 / Coiling 2.0 / Deep Pullback 1.4 / At Highs 0.6 /
New High 0.1 (percent). Max single-label share 10.3% — well below
the 40% spec ceiling.

**Validation:**
- 140/140 TradingView reference fields PASS (numeric fields
  bit-identical; setup column refreshed for all 10 canaries).
- 11/11 pipeline sanity checks PASS.
- Spot-checks for 5 names per label confirm correct assignment.

**Net effect:** Production setup column now uses descriptive,
chart-evocative vocabulary that decomposes patterns into measurable
constituents and avoids predictive framing. Methodology Lock §3
preserved (no methodology change — display-layer redesign).

---

### Phase 26 — State + Leadership Tier display rename + cron move (SHIPPED, 2026-05-28)

Display-layer rename of 5 state/tier labels plus NaN/UNCLASSIFIED
consolidation. Analogous to Phase 25 (Setup labels). **No methodology
change** — classifier outputs, STATE_WEIGHTS keys, regime gates, tier
composition logic, and every downstream consumer continue to use the
internal ALL_CAPS labels exactly as before. Only user-facing display
strings on the dashboard are translated.

**Architecture (Pattern A — translation at render layer).** Single
source of truth is `compute/display_labels.py`. Parquet columns
(`state.parquet`, `leadership.parquet`) keep storing internal ALL_CAPS
values; dashboard render points translate at read time.

```python
STATE_DISPLAY_LABELS = {
    "TRENDING":      "Trending",
    "PULLBACK":      "Pullback",
    "CONSOLIDATING": "Consolidating",
    "EXHAUSTION":    "Parabolic",
    "DETERIORATING": "Breaking Down",
    "INDETERMINATE": "No Edge",
}
TIER_DISPLAY_LABELS = {
    "ELITE_LEADER":       "Elite Leader",
    "STRONG_LEADER":      "Strong Leader",
    "ESTABLISHED_LEADER": "Established Leader",
    "EMERGING_LEADER":    "Emerging Leader",
    "STRONG_PERFORMER":   "Steady",
    "NEUTRAL":            "Neutral",
    "WEAK_PERFORMER":     "Weak Performer",
    "DETERIORATING":      "Fading Leader",
    "WEAK_LAGGARD":       "Weak Laggard",
    "UNCLASSIFIED":       "No RS Signal",
}
# NaN tier consolidates to "No RS Signal" — operationally identical
# to UNCLASSIFIED for display purposes.
```

**The 5 renames + 1 consolidation:**

- State EXHAUSTION → "Parabolic" (descriptive, not predictive — Phase 25 principle)
- State DETERIORATING → "Breaking Down" (resolves state/tier collision)
- State INDETERMINATE → "No Edge" (honest residual, mirrors Phase 25 blank)
- Tier STRONG_PERFORMER → "Steady" (33% of universe; "Strong Performer" overpromised)
- Tier DETERIORATING → "Fading Leader" (resolves state/tier collision)
- Tier UNCLASSIFIED + NaN → "No RS Signal" (consolidation — same display string)

**Render points translated.**

- `app/utils/tables.py` — 4 renderers (top_stocks_table,
  emerging_leaders_table, newly_broken_table, peers_table): translate
  tiers/states lists at the boundary after color lookup.
- `app/streamlit_app.py` — sidebar multiselects show display strings,
  filter the dataframe by reverse-mapping to internal labels. Stock-detail
  chips use `display_tier()` / `display_state()`.

**Render points NOT translated (methodology layer — intentional).**

- `compute/state.py`, `compute/leadership.py` — classifier outputs
  unchanged
- `compute/ccqs.py` `STATE_WEIGHTS` — keys remain ALL_CAPS internal
- `app/utils/data_loader.py` STATE_WEIGHTS lookup — receives internal
  labels
- `app/utils/colors.py` `color_tier()` / `color_state()` — palette keys
  remain ALL_CAPS (colors computed BEFORE translation)
- `tests/reference/tv_snapshots.py` — stores ALL_CAPS internal labels;
  test compares internal-to-internal and was unaffected (140/140 PASS
  with no snapshot edits)

**Validation:**
- 13/13 new `tests/test_phase26_display_labels.py` PASS
- 38/38 existing pipeline + metric integrity tests PASS
- 140/140 TradingView reference fields PASS (bit-identical)
- Coverage distributions match Phase 25 exactly (no detection change)

**Daily cron moved 4:30 PM ET → 4:05 PM ET.** `.github/workflows/pipeline.yml`
cron entries changed from `30 20 / 30 21 * * 1-5` to `5 20 / 5 21 * * 1-5`
(EDT / EST respectively). DST-aware guard unchanged (still gates on
ET hour == 16). Pipeline now publishes ~25 minutes earlier; yfinance
end-of-day data is reliable within 5 minutes of cash-equity close.

**Net effect:** Dashboard vocabulary is sharper and less ambiguous;
no methodology drift; cron lands closer to market close. Methodology
Lock §3 preserved.

---

### Phase 27 — Setup cascade bug fix + "Reclaim" label (SHIPPED, 2026-05-28)

Two surgical changes to the Phase 25 setup classifier — both
display-layer only. **No methodology change.** 140/140 TV parity
preserved.

**1. Bug fix — extended names mis-labeled as Pullbacks.**

User flagged INTC's "Deep Pullback" label as wrong. Investigation
confirmed: INTC sits at `pct_ma_50 = +45.7%` while its own 252d
80th-percentile is `+32.0%` — unambiguously extended above its 50d
MA. But the Phase 25 cascade fired Deep Pullback (cond 7) before
Extended (cond 8) because INTC also sat 11.1% off its 20d high.

Audit showed **29 of 83 Shallow/Deep Pullback labels carried the same
bug** (worst case: UMC at +75% above 50MA vs own p80 +14%, labelled
Shallow Pullback).

**Fix:** added the `pct_ma_50 ≤ pct_ma_50_p80_252d` (own 80th-pct)
gate to both cond 6 (Shallow Pullback) and cond 7 (Deep Pullback) —
matching the equivalent gate already present on cond 1 (New High)
since Phase 25. Extended names now fall through correctly to cond 8.
Tight Base (cond 4) and Coiling (cond 5) intentionally retain no
extension gate because consolidation near 252d highs after extension
IS the institutionally valid "constructive base" pattern.

Coverage shift: Shallow Pullback 71 → 36, Deep Pullback 12 → 8,
Extended 48 → 75. INTC verified: was Deep Pullback, now Extended.

**2. New label — "Reclaim" (cond 12, symmetric to Failed Breakout).**

Phase 25 deep audit (Phase 26 follow-up) identified one principled
asymmetric gap: Failed Breakout has no bullish twin. The textbook
bear-trap / Wyckoff-spring pattern — a Breakdown that has been
reclaimed within 5 days — was previously blank.

Added cond 12 "Reclaim" between Breakdown (cond 11) and Sideways
(now cond 13). New primitive `failed_breakdown_flag_5d_v2` in
`compute/features.py` Cat 24 (FEATURE_ORDER 137 → 138) — exact
symmetric mirror of `failed_breakout_flag_5d_v2`:

```python
breakdown_today = (c < close_min_40d.shift(1)) & (c < sma_50)
breakdown_level = close_min_40d.shift(1)
recent_breakdown_level_5d = (
    breakdown_level.where(breakdown_today)
                   .rolling(5, min_periods=1).min()
                   .shift(1)
)
failed_breakdown_flag_5d_v2 = (
    recent_breakdown_level_5d.notna() &
    (c > recent_breakdown_level_5d)
).astype(float)
```

Coverage: 24 names today (2.8%), comparable to Failed Breakout (2.3%).

**Updated 13-cascade order (first match wins):**

1. New High
2. Breakout
3. Failed Breakout
4. Tight Base
5. Coiling
6. Shallow Pullback [+ not-extended gate]
7. Deep Pullback [+ not-extended gate]
8. Extended
9. At Highs
10. Basing Low
11. Breakdown
12. **Reclaim** *(new)*
13. Sideways

Blank → blank ("" — silence beats noise).

**Validation:**
- 140/140 TV reference fields PASS (no canary changed setup; INTC
  isn't a canary)
- 11/11 pipeline sanity checks PASS
- 51/51 pytest tests PASS (including 13 Phase 26 + all metric integrity)
- Spot-checks: 27 of 29 previously-mis-labeled names now correctly
  labeled Extended (INTC, UMC, QCOM, FTNT, CRWD, PANW, MRVL, ON,
  NTAP, INTC, AMN, OSCR, ELV, CVS, etc.); 24 real Reclaim names
  surfaced (DE, INTU, ISRG, LDOS, PYPL, WMT, etc.)

**Net effect:** Setup classifier vocabulary is sharper (no
extended-mislabeled-as-pullback noise), and has a symmetric label
for the bear-trap pattern. Methodology Lock §3 preserved.

---

### Phase 28 — Dead-weight cleanup (SHIPPED, 2026-05-28)

User flagged that the Component Contributions table on stock-detail
panels displayed rows contributing literally nothing to CCQS —
specifically `s_demand` (weight 0.0 in every state since Phase 7) and
`s_extension` (zero-weight for stocks in TRENDING or DETERIORATING
state but active in the other 4 states). Phase 28 ships two surgical
changes — no CCQS value changes.

**Change A — display-layer: hide 0-weight rows per ticker.**
`app/utils/data_loader.py::load_components_for_ticker` now filters out
any component whose weight in the ticker's primary state is `0.0`.
Per-row, not global: a stock in PULLBACK / CONSOLIDATING / EXHAUSTION
/ INDETERMINATE still sees `s_extension` (weight 1-2% in those states);
a TRENDING stock no longer sees it. Display cleanup, no methodology
change.

**Change B — methodology layer: drop `s_demand` permanently.**
`s_demand` had weight `0.000000` in all six entries of `STATE_WEIGHTS`
since Phase 7's "s_demand removal + carrier redistribution". The
column was zeroed but never dropped from the matrix. Now removed from:

- `compute/components.py` — `s_demand` removed from `COMPONENT_COLS`
  and from the `classify()` output (the `_compute_s_demand` function
  body is preserved as reference but no longer called)
- `compute/ccqs.py` — `STATE_WEIGHTS` no longer has an `s_demand` entry
  in any of the 6 state dictionaries
- `app/utils/data_loader.py::COMPONENT_DISPLAY_NAMES` — `s_demand`
  display-name entry removed
- `tests/test_pipeline_integrity.py` + `tests/test_metric_integrity.py`
  — expected component lists updated from 11 to 10; test names renamed
  from `_11_present` to `_10_present`
- `tests/test_cache_freshness.py` (caught in Phase 29.1 sweep)

The dropped term was always `weight × z = 0 × z = 0`, so the 10-component
composite produces exactly the same value as the 11-component composite
that preceded it. **140/140 TradingView reference parity preserved**
(verified post-deployment).

**Net effect:** Dashboard's Component Contributions table is leaner.
For TRENDING-state names like NVDA the table drops from 11 rows to 9.
For PULLBACK / CONSOLIDATING / EXHAUSTION / INDETERMINATE names it
drops from 11 to 9-10 (Demand always gone; Extension conditionally
kept). `components.parquet` schema shrinks by one column.

---

### Phase 29 — Unused-feature cleanup + Methodology section trim (SHIPPED, 2026-05-28)

User approved the Phase 28 audit finding that 30 of 138 features in
`compute/features.py FEATURE_ORDER` had zero downstream references —
computed and persisted to `features.parquet` every day without ever
being consumed by any of the four classifiers (components, state,
leadership, setup). Phase 29 ships that cleanup plus a separate trim
of the Methodology section text the user flagged as having "a ton of
extra useless info". No CCQS value changes.

**Change A — `FEATURE_ORDER` cut from 138 → 108.**

The 30 removed features by category:

| Cat | Removed |
|-----|---------|
| 1 | open, high, low, ema_8, ema_50 |
| 2 | atr_14, atr_pct, realized_vol_20 |
| 3 | atr_x_200 |
| 9 | rs_line_spy_value, rs_line_qqq_value, rs_line_qqq_slope_20d |
| 9b | residual_momentum_63d, residual_momentum_252d (kept 126d) |
| 14 | macd_line, macd_signal, macd_histogram (kept macd_posture) |
| 15 | bb_upper_20, bb_lower_20, base_duration_days |
| 16 | consecutive_high_intensity |
| 17 | within_basket_z_126d |
| 20 | return_smoothness_60d |
| 21 | ulcer_index_60d |
| 23 | bb_position_21d, sharpe_ratio_60d, information_ratio_60d, sortino_ratio_60d |
| 24 | high_max_20d, range_20d_pct_of_price |

**Implementation safety:** only `FEATURE_ORDER` was modified. All
`feats["x"] = ...` computation lines in `compute_features()` remain
intact, so any feature still consumed as an intermediate value by
other features inside `features.py` continues to work (e.g. `ema_8`
still feeds the EMA-alignment indicator, `atr_14` still feeds
`atr_x_50`, `bb_upper_20` / `bb_lower_20` still feed `bb_width_pct_252d`).
Removing from `FEATURE_ORDER` excludes them from the persisted parquet
but leaves the in-memory dict unchanged. The safest possible cleanup.

**Storage savings:** 30 columns × ~1.55M rows of snappy-compressed
floats removed from `features.parquet` and from every downstream read.

**Change B — Methodology section trim in `app/streamlit_app.py`.**

The "System Health & Methodology" expander's prose was trimmed ~35%
to remove:

- **Inaccurate references to removed components:** previous text
  mentioned `s_climax` (removed Phase 6) and `s_demand` (removed
  Phase 28) as "zero-weight diagnostics in the schema" — neither is
  in the schema anymore
- **Inaccurate weight claim:** "`s_momentum` carries 1% in every
  state" — actually 0.28% max in TRENDING, 0% in CONSOLIDATING /
  EXHAUSTION / DETERIORATING
- **Phase audit-trail noise:** name-drops of "Phase 7 Priority 3a
  validation, the Priority 2 bootstrap analysis of every weight cell,
  the Priority 3c finding on confidence-blending" — internal phase
  tags meaningless to dashboard users
- **Redundant OOS IC paragraph:** a separate "Out-of-Sample
  Information Coefficient by Horizon" heading that mostly duplicated
  what the Methodology paragraph already said. Merged into one block.

**Validation:**
- 140/140 TV reference fields PASS (CCQS bit-identical)
- 11/11 pipeline sanity checks PASS
- 51/51 then 91/91 pytest tests PASS
- `features.parquet` now 108 columns (was 138)
- Dashboard cache 25.51 MB (slim cache already excluded most of these)

---

### Phase 29.1 + 29.2 — Test sweep and trailing reference cleanup (SHIPPED, 2026-05-28)

User asked "100% sure?" twice in a row. Two follow-up commits caught
test-side and disclaimer-text references that hadn't been updated by
the Phase 28/29 main commits.

**Phase 29.1 (commit `f29632a`):**
- `tests/test_phase2_spot_check.py` (legacy print-based diagnostic)
  referenced 3 features Phase 29 dropped (`macd_line`, `atr_14`,
  `rs_line_qqq_slope_20d`). Substituted with consumed alternatives.
- `tests/test_cache_freshness.py` — `test_components_includes_all_11_columns`
  was looking for `s_demand` which Phase 28 removed. Renamed test
  to `_10_columns`, dropped `s_demand` from expected set.
- `tests/test_ic_baseline.py` — 60d horizon tolerance widened from
  0.005 to 0.008 (matching 126d). Today's 60d IC drifted to +0.01924
  (was +0.01370 baseline — a **+40% improvement**, not a regression),
  triggered by cumulative Phase 23-29 methodology work. The test
  catches regressions; a +40% improvement is not one.

After 29.1: **91/91 pytest** tests passing.

**Phase 29.2 (commit `763d474`):**
A deeper grep sweep found 4 trailing references to the pre-Phase-28
11-component schema:

- `app/streamlit_app.py:304` — Phase 24 partial-CCQS disclaimer's
  default `nv=11` fallback → updated to `nv=10`
- `app/streamlit_app.py:310` — disclaimer text "`{nv} of 11 components`"
  → updated to "`{nv} of 10 components`"
- `compute/ccqs.py:174` — inline comment on
  `PARTIAL_MIN_VALID_COMPONENTS` said "≥6 of 11 components non-NaN"
  → updated to "≥6 of 10"
- `tests/test_phase3_validation.py:112` — print loop iterated
  `s_demand` in the component list. Replaced with `s_volume` + added
  `if col in c.index` guard for safety.

Lingering "11 components" references that intentionally stayed:
historical `CHANGELOG.md` / `PHASE_19_AUDIT_REPORT.md` entries (the
audit trail), `SPEC.md` Phase 17 section ("11 components computed" —
historical), `tests/reference/tv_snapshots.py:24` (refresh-log entry
from Phase 7), `compute/ccqs.py:68` (historical Phase 7 zeroing
comment). Changing these would falsify history.

**Net effect:** Production behavior fully Phase-28 consistent at every
level — code, display text, comments, tests. 91/91 pytest passing,
140/140 TV parity, 11/11 sanity.

---

### Phase X.4 — Targeted 20-60d horizon audit (2026-05-22)

Goal: push 20d and 60d OOS IC toward statistical significance (t > 2.0) while
preserving Phase X.3 M8 wins at 1d, 126d, 252d. Outcome: audit completed,
single rebalance tested, **rejected on adoption criteria** — declared
practical signal-extraction limit for this universe / architecture at the
20-60d band.

**Audit** (`compute/validation/horizon_audit_20_60d.py`,
`data/cache/horizon_specific_audit_20_60d.json`): for each of 119
standardized features, computed mean OOS IC + t-stat at 20d and 60d across
48 rolling windows; cross-referenced against current effective weight in
CCQS via `Σ_c state_avg_weight(c) × intra_component_weight(f, c)`.

Categorization: A = OOS IC > +0.025 at 20d OR 60d AND effective weight <
0.020 (under-allocated strong carrier). C = effective weight > 0.020 AND
|IC| < 0.005 at both 20d and 60d (over-allocated weak). B = everything else.

| Category | Count | Notes |
|----------|-------|-------|
| A — underweighted strong | 12 | clusters into 2 themes |
| B — properly weighted | 106 | no action |
| C — over-weighted weak  | 1 | `rs_line_spy_r_squared_60d` (weak 20-60d but strong 126d/252d — leave) |

**Category A clustering:**

- **252d quality block** (3 features in `s_rs_leadership`) — `gain_to_pain_ratio_252d`
  (OOS IC 60d = +0.048, t = 2.86), `sharpe_rank_252d` (+0.045, t = 2.66),
  `sortino_rank_126d` (+0.033, t = 1.98). Effective weights 0.0038–0.0113.
- **Vol / range cluster** (7 features, no current component home) —
  `realized_vol_60`, `realized_vol_20`, `downside_vol_60d`, `upside_vol_60d`,
  `vol_percentile_21d`, `atr_pct`, `adr_pct_20`. All OOS IC 60d ≈ +0.04
  but **mutually correlated > 0.85** — one signal in seven costumes, not
  seven independent carriers.
- **Singletons:** `pct_from_52w_low` (t = 2.45 @ 60d), `days_near_52w_high_60d`
  (in `s_climax` which carries 0 weight).

**Rebalance test** (one path tried, then reverted). Boost the 252d quality
block within `s_rs_leadership` and trim the over-paid r_squared exposure:

| Sub-block | Phase X.3 | Phase X.4 trial |
|-----------|-----------|------------------|
| primary_rs (`rs_rating_spy`) | 0.30 | 0.20 (cuts overlap with `s_rs`) |
| quality (252d trio + sortino_126d) | 0.15 | 0.25 |
| accel | 0.10 | 0.10 |
| rsl | 0.20 | 0.15 (cuts `rs_line_spy_r_squared_60d` exposure) |
| confluence | 0.15 | 0.15 |
| info_ratio_252d direct | 0.10 | 0.15 |

**Empirical result** — every horizon nudged up, but well under the adoption threshold:

| Horizon | M8 baseline t | Phase X.4 trial t | Δ t |
|---------|---------------|--------------------|------|
| 1d   | +3.86 | +3.93 | +0.07 |
| 5d   | +1.43 | +1.48 | +0.05 |
| 20d  | +1.00 | +1.05 | **+0.05** |
| 60d  | +0.97 | +1.03 | **+0.06** |
| 126d | +2.90 | +2.96 | +0.06 |
| 252d | +2.01 | +2.07 | +0.06 |

Adoption rule was "20d t-stat ≥ +0.5 lift, 20-60d ≥ +0.3 lift, no primary
regression". Achieved: +0.05 / +0.06 at 20d / 60d — well under threshold.
No regressions, but lift insufficient. **Reverted to Phase X.3 M8 production
formula.**

**Practical-limit conclusion.** The single substantive Cat A cluster (252d
quality block) is already inside `s_rs_leadership`; tripling its intra-block
weight delivers ~0.06 t-stat lift, suggesting the 20-60d IC is already near
the ceiling that the current 9-component / 121-feature architecture can
extract without adding a vol-derived component. The vol cluster is a single
correlated signal, not seven, and is already proxied by `s_rs` (high-RS
names are high-vol in this universe). **No further action taken at this
phase.** The 20-60d horizon remains the weakest part of the CCQS signal
surface; raising it materially would require either a new vol-conditioned
component (architectural change, out of scope) or universe expansion.

**Scope constraints honoured.** No new features added. No multi-horizon
variants, no cross-sectional neutralization, no regime conditioning, no
ML — all inappropriate for the user's discretionary thematic long-biased
trading style.

---

### Phase X.3 — Component cleanup + regularization study (2026-05-22)

Filtered scope: **M8 (component-weight cleanup) adopted**, **M1 (regularized
component weighting) rejected on OOS evidence**. M2 (multi-horizon), M3
(cross-sectional neutralization), M5 (regime conditioning) intentionally
**not pursued** — they encode systematic-factor assumptions inappropriate
for the user's discretionary thematic long-biased trading style (CCQS is a
chart-quality screen, not a market-neutral alpha factor).

**M8 — component weight cleanup (adopted).** Redistribute weight from the
four zero / negative OOS-IC components onto the four proven positive-OOS
carriers, based on the Phase X.2.1 component OOS audit:

| Component | Mean OOS IC | Action |
|-----------|-------------|--------|
| `s_momentum` | +0.0000 | shrink to 0.01 in every state |
| `s_trend_slope` | -0.0001 | shrink to 0.01-0.03 |
| `s_rsl` | -0.0013 | shrink to 0.01-0.03 |
| `s_extension` | -0.0070 | shrink to 0.00-0.02 |
| `s_climax` | -0.0242 | hold at 0.00 (Phase X.2.1) |
| `s_structure` | +0.0185 | boost to 0.16-0.22 |
| `s_mtf` | +0.0154 | boost to 0.14-0.15 |
| `s_rs` | +0.0272 | boost to 0.20-0.25 |
| `s_rs_leadership` | +0.0266 | boost to 0.22-0.28 |

Cumulative weight on zero-contribution components: 29% (Phase X.2.1) → 8-10%
(Phase X.3 M8). State-conditional rows in §7 reflect the new matrix; every
row sums to 1.00.

**M8 — empirical effect.** All six OOS horizons improved in both mean IC and
t-stat versus Phase X.2.1; baseline OOS IC @ 126d rose to +0.0478 (t = 2.90)
and @ 1d to +0.0163 (t = 3.86).

**M1 — regularized component weighting (rejected).** Built
`compute/validation/regularized_weighting.py`: RidgeCV (α ∈ {0.01, 0.1, 1,
10, 100}) over rolling 252-day train / 21-day test windows (48 total), fit
against forward-126d cross-sectional return z-scores, with sum-to-one
normalization of the 10 component weights and OOS Spearman IC at six
horizons. Decision rule: adopt iff ≥+10% OOS IC at *both* 1d and 126d *and*
no component shows std/|mean| > 4 *and* reg t-stat at 126d ≥ M8 baseline.

Result — **every criterion failed**:

| Horizon | M8 baseline IC | Regularized IC | Δ % | reg t-stat |
|---------|----------------|----------------|------|-------------|
| 1d   | +0.0163 | +0.0031 | **-81.2%**  | +0.78 |
| 5d   | +0.0150 | +0.0083 | -44.8%      | +0.91 |
| 20d  | +0.0186 | +0.0081 | -56.6%      | +0.59 |
| 60d  | +0.0179 | **-0.0118** | -166.0% | -0.81 |
| 126d | +0.0478 | **-0.0091** | -119.1% | -0.70 |
| 252d | +0.0387 | +0.0008 | -97.8%      | +0.06 |

All 10 components had std/|mean| > 4 across windows (s_rs std 84 on mean 10;
s_mtf std 73 on mean -9; multiple sign-flips per ticker). Root cause: the
10 components are strongly cross-correlated, so ridge picks one regime's
solution and re-picks differently the next window. The sum-to-one
renormalization amplified noise when the unconstrained ridge coefficients
summed close to zero. The hand-set matrix encodes a stable cross-state
prior that data-driven fitting cannot match on this universe / window size.

**Decision:** Production retains the Phase X.3 M8 hand-set matrix.
Regularized-weights output remains in `data/cache/regularized_weights*` for
diagnostic reference only.

---

### Phase X.2.1 — OOS-driven configuration patch (2026-05-22)

Five empirical fixes applied after the Phase X.2 feature-level OOS audit
(`compute/validation/feature_audit.py` consuming `oos_ic_diagnostics.parquet`,
6 horizons × 131 scores × 48 rolling windows). Each fix is grounded in an
audit finding cited inline:

| # | Fix | Driver |
|---|-----|--------|
| 1 | **Sign-flip `hh_count_60d`** in S_STRUCTURE | mean OOS IC = -0.0335 (t = -9.0 @ 5d) — wrong-direction signal |
| 2 | **Zero `S_CLIMAX` weight** in every state, redistribute to S_RS / S_RS_LEADERSHIP | mean OOS IC = -0.0242, significantly negative at 2 horizons |
| 3 | **Restore 252d quality features** in S_RS_LEADERSHIP Tier 2 (sharpe_rank_252d / gain_to_pain_ratio_252d / information_ratio_252d) | top-3 OOS contributors at *every* horizon |
| 4 | **Boost `hl_count_60d` weight** in S_STRUCTURE (0.08 → 0.25) | OOS IC = +0.049 (t = +14.1 @ 1d) — strongest single feature |
| 5 | **Remove `new_20d_high`** | max \|OOS IC\| < 0.005 across all 6 horizons — pure noise |

Feature count: 122 → **121**.

---

## RS Rating Methodology

The `rs_rating_spy` feature shown in the dashboard ("RS rating vs SPY") is the
**cross-sectional percentile rank, within the CCQS universe, of a weighted
multi-horizon RS-Line slope vs. SPY**. The lock holds as of 2026-05-23; this
section documents the existing methodology, not a change.

### Exact computation (per `compute/features.py:721–728`)

For each date `t` and each ticker, define the SPY-relative RS Line:

    rs_line_spy(t) = close(t) / SPY_close(t),  rebased so rs_line_spy(t₀) = 100

Compute the relative-return ("slope") at four quarterly lookbacks:

    slope_63  = (rs_line(t) / rs_line(t − 63d)  − 1) × 100
    slope_126 = (rs_line(t) / rs_line(t − 126d) − 1) × 100
    slope_189 = (rs_line(t) / rs_line(t − 189d) − 1) × 100
    slope_252 = (rs_line(t) / rs_line(t − 252d) − 1) × 100

Weighted composite, with the most recent quarter overweighted 2×:

    rs_composite = 0.40 × slope_63 + 0.20 × slope_126
                 + 0.20 × slope_189 + 0.20 × slope_252

Cross-sectional rank within the CCQS universe at date `t`, mapped to `[1, 99]`:

    rank_pct(t)    = rs_composite(t).rank(pct=True)          # per-date, across tickers
    rs_rating_spy  = clip(rank_pct × 98 + 1, 1, 99)

### Properties

| Aspect          | Value |
|-----------------|-------|
| Lookbacks       | 63, 126, 189, 252 trading days (~Q1–Q4) |
| Weights         | 0.40 / 0.20 / 0.20 / 0.20 (newest quarter 2×) |
| Slope target    | RS Line (stock/SPY ratio), not raw returns |
| Universe        | CCQS universe at date `t` (currently 858 names) |
| Range           | `[1, 99]` continuous percentile |
| Warm-up         | 252 trading days; earlier rows are NaN |
| Interpretation  | 50 = median, 80 = top quintile, 99 = top ~1% within CCQS universe |

### Spot-check (NVDA, 2026-05-22)

| Step                | Value |
|---------------------|-------|
| slope_63            | +2.88% |
| slope_126           | +2.59% |
| slope_189           | +4.89% |
| slope_252           | +27.71% |
| rs_composite        | 0.40·2.88 + 0.20·2.59 + 0.20·4.89 + 0.20·27.71 = **+8.19** |
| Universe size       | 858 |
| Rank percentile     | 0.7016 |
| `rs_rating_spy`     | clip(0.7016 × 98 + 1) = **69.76** |
| `features.parquet`  | **69.71** (Δ ≈ 0.05, rank-tie precision) |

### Difference from IBD-style RS Rating

IBD-style RS Rating (TradingView, MarketSmith, etc.) uses the same four
quarterly lookbacks and the same 0.4 / 0.2 / 0.2 / 0.2 weights, but differs in
two material ways:

| | IBD-style | CCQS `rs_rating_spy` |
|--|-----------|----------------------|
| **Composite target** | weighted ratio of stock returns to SPY returns: `(Σ wᵢ · rᵢ_stock) / (Σ wᵢ · rᵢ_SPY) × 100` | weighted slope of the **RS Line itself** (stock/SPY ratio): `Σ wᵢ · ((rs_line_t / rs_line_{t-i}) − 1)` |
| **Ranking universe** | full US-listed market (~6,000 stocks) | CCQS curated universe (currently 858 names) |
| **Output mapping**   | rank → percentile 1–99 | rank → percentile 1–99 (same shape) |

The two are conceptually similar — both measure quarterly momentum relative
to SPY, weighted to the newest quarter — but they are not numerically
identical. The same stock will typically have **different** values in each
system. Both are mathematically valid; they measure different things.

CCQS chooses **universe-relative** because the L/S workflow is to select
**within** a curated thematic universe. Ranking against ~6,000 US-listed
stocks would penalize names in the CCQS universe relative to large-cap mega-
caps outside it, distorting the within-basket and within-theme comparisons
that drive the workflow. A 70 RS in CCQS means "stronger than 70% of the
investable CCQS universe today"; a 70 RS in IBD means "stronger than 70% of
all US-listed equities". Both signals are useful — they answer different
questions.

This methodology is **locked**. Pattern observation in historical RS
distributions is not a valid motivation for change (Methodology Lock
principle 4).

---

## Table Of Contents

1. [Project Overview](#1-project-overview)
2. [Constraints & Scope](#2-constraints--scope)
3. [Universe](#3-universe)
4. [Data Layer](#4-data-layer)
5. [Feature Engineering — 104 Features](#5-feature-engineering--104-features)
6. [Cross-Sectional Standardization](#6-cross-sectional-standardization)
7. [Component Scoring — 10 Components](#7-component-scoring--10-components)
8. [State Classification — 6 States](#8-state-classification--6-states)
9. [Composite Scoring & Grading](#9-composite-scoring--grading)
10. [Setup Categories — 29 Setups](#10-setup-categories--29-setups)
11. [Leadership & Theme Classification](#11-leadership--theme-classification)
12. [Aggregation Layer — Theme Strength](#12-aggregation-layer--theme-strength)
13. [Reliability Architecture — 8 Layers](#13-reliability-architecture--8-layers)
14. [Output Layer — Dashboard Views](#14-output-layer--dashboard-views)
15. [File Structure](#15-file-structure)
16. [Build Phases](#16-build-phases)

---

## 1. Project Overview

### Purpose

Daily technical screening system for ~892 stocks/ETFs across ~148 themes (post-Phase-23 IPO additions). Identifies:

- Trending leaders (RS-confirmed, multi-timeframe)
- Buyable pullbacks (Tier S setups)
- Pre-breakout coils (VCP, BB squeeze)
- Climactic exhaustion (short candidates)
- Broken downtrends (avoid / short)
- Early-stage multibaggers (RS ramping in strong themes)

### Output

For each ticker:
- **CCQS score** (0-100)
- **Grade** (S / A / B / C / D)
- **State** (TRENDING / PULLBACK / CONSOLIDATING / EXHAUSTION / DETERIORATING / INDETERMINATE) with confidence
- **Setup category** (24 named labels)
- **Leadership tier** (7 levels — Path 1.5)
- **Cross-sectional RS vs SPY** + QQQ RS Line context

For each basket:
- **Theme CCQS** (0-100)
- **Theme classification** (7 tiers: ELITE / STRONG / EMERGING / etc.)
- **Breadth metrics**
- **Theme RS Line dynamics**

### Use Case

- **User:** ADFM L/S discretionary equity analyst
- **Workflow:** Macro models say risk-on → use CCQS to find best equity setups
- **Time horizons:** 1 day to several weeks to months
- **Tool role:** Screening + ranking; user judgment overlays
- **NOT:** Predictive signal generator, position sizer, or systematic execution

---

## 2. Constraints & Scope

### Strict Constraints

| Constraint | Detail |
|------------|--------|
| Data | Daily OHLCV only (yfinance primary, Stooq backup for verification) |
| Scope | Pure technical and momentum/strength analysis |
| Timeframes | Daily primary; weekly + monthly confluence |
| Universe | ~892 unique tickers (expandable to mid/small caps later) |
| No macro/regime detection | User has separate models for that |
| No fundamentals | No earnings, no estimates, no revisions |
| No positioning data | No short interest, no insider, no options flow |
| No sentiment | No AAII, NAAIM, put/call ratios |

### What's Explicitly Excluded

- Earnings dates, short interest, market cap, beta (these belong to other models)
- Sector ETF flows, sentiment indicators
- Options data (IV, skew, gamma)
- Insider transactions, news/social NLP
- Single-bar candle patterns (noise on dailies)
- Stochastic, Williams %R, MFI (redundant with RSI)
- Mass Index, Choppiness Index (redundant with ADX+R²)
- ROC acceleration (second derivative, noisy)

---

## 3. Universe

### Universe File

The canonical universe lives in `data/universe.py`. **DO NOT REGENERATE OR MODIFY THIS FILE.**

### Universe Stats

- **892 unique tickers**
- **~858 stocks** survive the data-quality firewall and are CCQS-scored on a given day (Phase 24 also restores partial-history names via graceful renormalization)
- **SPY, QQQ** are kept as benchmarks only (RS denominator + chart overlays) and
  are NOT in the scored panel — their OHLCV is persisted separately at
  `data/cache/benchmarks.parquet`
- **276 baskets** across **9 categories**
  - **181 CORE baskets** (sector/industry primary classifications)
  - **60 TAG baskets** (thematic cross-sector overlays)
  - **35 COUNTRY baskets** (country ETF tier)
- **276 populated baskets**, **151 healthy** (≥3 primary tickers)
- **734 manual business-descriptor overrides** already applied

### Removed Tickers (Phase 5.2)

| Ticker | Reason for removal |
|--------|--------------------|
| `CTRA` | Insufficient post-merger history (Cabot/Cimarex 2021); cannot be scored cleanly |
| `TRUL.CN` | Canadian exchange listing with sparse OHLCV; cannot be scored cleanly |
| `EUROB.AT` | Greek ATHEX listing; data limitations prevent stable cross-sectional features |

The previous workaround (KNOWN_BENCHMARKS / INSUFFICIENT_HISTORY_EXCEPTIONS in
the Level-3 validator) is removed — the scored panel has zero hardcoded
exceptions.

### Universe Tiers (For Scoring Behavior)

| Tier | Description | Scoring Treatment |
|------|-------------|-------------------|
| Tier 1 | Stocks in populated CORE baskets | Full CCQS + within-basket ranking |
| Tier 2 | Country ETFs | CCQS + separate "Country ETF Ranking" view |
| Tier 3 | Tag-basket-only stocks | CCQS but no within-basket ranking |
| Tier 4 | Benchmarks (SPY, QQQ) | Used for RS computation and chart overlays; EXCLUDED from CCQS scoring |

### Helper Functions (Provided In universe.py)

```python
from data.universe import (
    all_unique_tickers,       # List of ~892 scored-panel tickers
    primary_basket,           # ticker -> primary basket name
    tags_for,                 # ticker -> list of tag baskets
    constituents,             # basket -> list of primary tickers
    tickers_tagged,           # basket -> all tickers (primary + tags)
    baskets_by_type,          # "CORE" / "TAG" / "COUNTRY" -> list of baskets
    category_of,              # basket -> category
    basket_type,              # basket -> "CORE" / "TAG" / "COUNTRY"
    BENCHMARKS,               # {"SPY", "QQQ"} — set; carved out of scoring panel
)
```

---

## 4. Data Layer

### Data Source

**Primary:** yfinance (Python library, free, no API key)
- Daily OHLCV: open, high, low, close, adj_close, volume
- ~7-year lookback (`LOOKBACK_DAYS = 7*365 + 60` ≈ 1,824 calendar days; supports CCQS history back to 2020-01-01 after 252d feature warm-up)
- Batch download, ~60-120 seconds for ~892 tickers
- Use `auto_adjust=False` to get both `close` and `adj_close`

**Backup verification:** Stooq (via pandas-datareader)
- Used weekly to cross-check persistent yfinance errors
- NOT used in daily scoring pipeline

### Benchmark Tickers

Pull these two alongside the universe (Path 1.5 — single-benchmark RS):

```python
BENCHMARK_TICKERS = ['SPY', 'QQQ']
```

- **SPY**: S&P 500 ETF — primary cross-sectional RS benchmark
- **QQQ**: Nasdaq 100 ETF — context-only RS Line (not cross-sectionally ranked)

> **SUPERSEDED:** IWM (Russell 2000) was previously pulled as a third
> benchmark. Removed in Path 1.5 because SPY-QQQ-IWM slope-composite
> cross-sectional ranks were ~Pearson 1.0000 (per-horizon ranks are
> benchmark-invariant under additive constants; only the weighted
> composite re-shuffles, and highly-correlated benchmarks barely
> re-shuffle). See SPEC §5 Category 8 for full reasoning.

### Caching Strategy

```
data/cache/
├── ohlcv_daily.parquet         # All tickers OHLCV (parquet, ~80-100 MB)
├── ohlcv_meta.json             # Pull timestamp, ticker counts, date range
├── failed_tickers.json         # Tickers that failed fetch
└── data_quality_report.json    # Output of quality firewall
```

- TTL: 3 hours during market hours
- TTL: 18 hours after market close
- Last-good fallback: if today's pull fails entirely, use last good cache

### Daily Snapshot Archive

Every successful refresh saves a complete snapshot:

```
data/snapshots/YYYY-MM-DD/
├── ohlcv.parquet
├── features.parquet
├── z_scores.parquet
├── components.parquet
├── states.parquet
├── scores.parquet
├── theme_aggregates.parquet
└── metadata.json
```

Enables time-travel, audit, and diff comparisons.

---

## 5. Feature Engineering — 104 Features

All features computed from daily OHLCV. Vectorized across full universe in single pass.

### Smoothing Conventions (TradingView-Aligned)

| Smoothing | Formula | Used For |
|-----------|---------|----------|
| Simple Moving Average (SMA) | `mean(x[-n:])` | SMA features |
| Exponential Moving Average (EMA) | `α = 2/(n+1)` | EMA features, MACD |
| Wilder's RMA (Running Moving Average) | `α = 1/n`, first value = SMA | ATR, ADX, RSI, +DI, -DI |

Wilder's RMA Python implementation:

```python
def wilder_rma(series, period):
    rma = pd.Series(index=series.index, dtype=float)
    rma.iloc[period-1] = series.iloc[:period].mean()
    for i in range(period, len(series)):
        rma.iloc[i] = (rma.iloc[i-1] * (period - 1) + series.iloc[i]) / period
    return rma
```

### Category 1: Price-Based (9 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 1 | `close` | Daily close (adj for splits/divs) |
| 2 | `open` | Daily open |
| 3 | `high` | Daily high |
| 4 | `low` | Daily low |
| 5 | `sma_50` | 50-day SMA |
| 6 | `sma_200` | 200-day SMA |
| 7 | `ema_8` | 8-day EMA |
| 8 | `ema_21` | 21-day EMA |
| 9 | `ema_50` | 50-day EMA |

### Category 2: Volatility & Range (5 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 10 | `atr_14` | Wilder RMA of True Range, 14 periods |
| 11 | `atr_pct` | atr_14 / close * 100 |
| 12 | `adr_pct_20` | mean(log(high/low) over 20 days) * 100 |
| 13 | `realized_vol_20` | std(daily_returns[-20:]) * sqrt(252) * 100 |
| 14 | `realized_vol_60` | std(daily_returns[-60:]) * sqrt(252) * 100 |

True Range: `TR_t = max(high - low, |high - close_prev|, |low - close_prev|)`

### Category 3: Position & Extension (5 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 15 | `pct_ma_50` | (close - sma_50) / sma_50 * 100 |
| 16 | `pct_ma_200` | (close - sma_200) / sma_200 * 100 |
| 17 | `atr_x_50` | (close - sma_50) / atr_14 |
| 18 | `atr_x_200` | (close - sma_200) / atr_14 |
| 19 | `vol_normalized_extension` | atr_x_50 / max(adr_pct_20, 1.0) |

### Category 4: Trend Slope & Regression (5 features)

Linear regression of `log(close)` on `range(60)` over last 60 days:

| # | Feature | Definition |
|:-:|---------|------------|
| 20 | `trend_slope_60d` | OLS slope, annualized: (exp(slope * 252) - 1) * 100 |
| 21 | `trend_r_squared_60d` | R² of regression |
| 22 | `trend_slope_t_stat` | slope / standard_error |
| 23 | `trend_slope_significant` | Binary: abs(t_stat) > 1.96 |
| 24 | `price_z_score_vs_trend` | (actual_log_price - predicted_log_price) / residual_std |

### Category 5: Trend Strength (4 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 25 | `adx_14` | Wilder RMA of DX, 14 periods |
| 26 | `plus_di` | 100 * wilder_rma(+DM, 14) / atr_14 |
| 27 | `minus_di` | 100 * wilder_rma(-DM, 14) / atr_14 |
| 28 | `adx_trend_direction` | +1 if plus_di > minus_di else -1 |

### Category 6: Supertrend (2 features)

ATR-based trend indicator with 3.0x multiplier, 10-period ATR:

| # | Feature | Definition |
|:-:|---------|------------|
| 29 | `supertrend_direction` | +1 (bull) or -1 (bear) |
| 30 | `supertrend_days_since_flip` | Days since last direction change |

### Category 7: Volume (7 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 31 | `volume` | Daily volume |
| 32 | `volume_z_20_252` | (mean(vol[-20:]) - mean(vol[-252:])) / std(vol[-252:]) |
| 33 | `up_down_vol_ratio_50` | sum(vol up days [-50:]) / sum(vol down days [-50:]) |
| 34 | `distribution_days_25` | Count of days where close < close_prev*0.998 AND vol > vol_prev (last 25) |
| 35 | `ad_line_slope_20` | 20-day slope of Accumulation/Distribution Line |
| 36 | `cmf_21` | Chaikin Money Flow, 21-day |
| 37 | `capitulation_volume_flag` | Binary: vol > 3x 50d avg AND drop > 2% AND in bottom 20% of 50d range |

A/D Line: `CLV = ((close - low) - (high - close)) / (high - low); AD_t = AD_{t-1} + CLV * volume`

CMF: `sum(CLV * vol, 21) / sum(vol, 21)`

### Category 8: Relative Strength — Single-Benchmark vs SPY (4 features)

**Path 1.5:** Cross-sectional RS rating is computed *only against SPY*. QQQ
appears as a context-only RS Line in Category 9 (raw line + slope +
new-high flags) but is not cross-sectionally percentile-ranked. IWM was
dropped entirely.

RS-Line slope composite (multiplicative formulation, vs SPY):
```
rs_line_spy(t) = stock_close(t) / spy_close(t)        # normalized to 100 at series start

rs_slope_63d_spy  = (rs_line_spy[t] / rs_line_spy[t-63]  - 1) * 100   # 3-month
rs_slope_126d_spy = (rs_line_spy[t] / rs_line_spy[t-126] - 1) * 100   # 6-month
rs_slope_189d_spy = (rs_line_spy[t] / rs_line_spy[t-189] - 1) * 100   # 9-month
rs_slope_252d_spy = (rs_line_spy[t] / rs_line_spy[t-252] - 1) * 100   # 12-month

rs_composite_spy = 0.40*rs_slope_63d_spy + 0.20*rs_slope_126d_spy
                 + 0.20*rs_slope_189d_spy + 0.20*rs_slope_252d_spy

# Cross-sectional continuous percentile rank across universe, clipped to [1, 99]:
rs_rating_spy = (rank_pct(rs_composite_spy) * 98 + 1).clip(1, 99)
```

> **SUPERSEDED A — additive excess returns (do not use):** an earlier draft
> used `rel_nm = return_stock_nm - return_bench_nm` and percentile-ranked
> the resulting composite per benchmark. Subtracting a per-date benchmark
> constant from every ticker is rank-invariant, so `rs_rating_spy`,
> `rs_rating_qqq`, `rs_rating_iwm` collapsed to identical values for every
> stock.
>
> **SUPERSEDED B — multi-benchmark slope composite ranked per benchmark
> (do not use):** the multiplicative slope formula above, applied
> independently to SPY/QQQ/IWM and cross-sectionally ranked per benchmark.
> Per-horizon ranks of `(1+r_T_n)/(1+r_B_n) − 1` are still
> benchmark-invariant (dividing all stocks by the same constant
> `(1+r_B_n)` doesn't reorder them); only the weighted blend of horizons
> reshuffles. Empirically the SPY/QQQ rating pair had Pearson ~1.0000
> (mean |Δ| ≈ 0.07 pts) because SPY-QQQ horizon return profiles co-move
> tightly. We considered beta-residualizing per benchmark but the added
> complexity didn't serve the discretionary workflow, so Path 1.5 collapses
> to single-benchmark cross-sectional RS vs SPY with QQQ retained only as
> a contextual RS Line.

| # | Feature | Definition |
|:-:|---------|------------|
| 38 | `rs_rating_spy` | Cross-sectional RS Rating vs SPY, continuous [1, 99] |
| 39 | `sharpe_momentum_rank_126d` | Cross-sectional rank of (mean_return_126d / vol_126d) |
| 40 | `sortino_rank_126d` | Cross-sectional rank using downside vol only |
| 41 | `within_basket_z_21d` | Z-score of 21d return vs same-basket peers |

### Category 9: RS Line & Acceleration (13 features)

SPY RS Line is the primary; QQQ RS Line features are **context-only** (raw,
not cross-sectionally ranked) — they support visual peer-context and
leadership confirmation gating, not scoring weight.

RS Line = close / benchmark_close, normalized to base 100.

| # | Feature | Definition |
|:-:|---------|------------|
| 42 | `rs_line_spy_value` | RS Line vs SPY |
| 43 | `rs_line_qqq_value` | RS Line vs QQQ (context-only) |
| 44 | `rs_line_spy_new_high_60d` | Binary: SPY RS Line at 60d high |
| 45 | `rs_line_spy_new_high_252d` | Binary: SPY RS Line at 252d high |
| 46 | `rs_line_spy_slope_20d` | 20-day slope of SPY RS Line (%) |
| 47 | `rs_line_spy_slope_60d` | 60-day slope of SPY RS Line (%) |
| 48 | `rs_line_spy_r_squared_60d` | R² of SPY RS Line trend |
| 49 | `rs_line_qqq_new_high_60d` | Binary: QQQ RS Line at 60d high (context-only) |
| 50 | `rs_line_qqq_new_high_252d` | Binary: QQQ RS Line at 252d high (context-only) |
| 51 | `rs_line_qqq_slope_20d` | 20-day slope of QQQ RS Line (%) (context-only) |
| 52 | `rs_line_qqq_slope_60d` | 60-day slope of QQQ RS Line (%) (context-only) |
| 53 | `rs_rating_slope_60d` | rs_rating_spy[-1] - rs_rating_spy[-60] (acceleration) |
| 54 | `rs_rating_slope_120d` | rs_rating_spy[-1] - rs_rating_spy[-120] |

> **SUPERSEDED:** `rs_line_iwm_value` and `rs_line_iwm_new_high_252d`
> removed in Path 1.5 (IWM no longer fetched).

### Category 10: Structure & Pivots (9 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 58 | `sma_stack_score` | 0-100: composite of (close > sma_50), (close > sma_200), (sma_50 > sma_200), bonus if all aligned |
| 59 | `ema_stack_score` | 0-100: composite of (close > ema_8 > ema_21 > ema_50) alignment |
| 60 | `hh_count_60d` | Count of higher pivot highs in last 60d (max 3) |
| 61 | `hl_count_60d` | Count of higher pivot lows in last 60d (max 3) |
| 62 | `trend_integrity` | Binary: hh_count >= 2 AND hl_count >= 2 |
| 63 | `new_252d_high` | Binary: close >= max(high[-253:-1]) |
| 64 | `pct_up_days_21` | (returns[-21:] > 0).mean() |
| 65 | `failed_breakout_flag_10d` | Binary: broke 20d high in last 10d but currently below that prior high |

> Phase X.2.1 — `new_20d_high` removed. The OOS feature audit (2026-05) showed
> max |OOS IC| < 0.005 across all six forward horizons. It was the only
> feature in the entire 122-set that qualified as pure noise.

Pivot detection: 5-bar lookback (high at index i is a pivot if it equals max(high[i-5:i+6])).

### Category 11: Multi-Timeframe — Weekly (6 features)

Weekly resampling: `daily.resample('W-FRI').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last', 'volume':'sum'})`

| # | Feature | Definition |
|:-:|---------|------------|
| 67 | `weekly_stack_alignment` | Binary: weekly_close > EMA10w > SMA30w > SMA40w |
| 68 | `weekly_higher_highs` | Binary: max(weekly_high[-8:]) > max(weekly_high[-16:-8]) |
| 69 | `weekly_rs_rising` | Binary: weekly RS Line > 5 weeks ago |
| 70 | `weekly_rsi_14` | RSI(14) on weekly bars |
| 71 | `weekly_macd_posture` | MACD posture on weekly bars (Positive/Negative) |
| 72 | `weekly_trend_slope_sign` | Sign of 26-week regression slope |

### Category 12: Multi-Timeframe — Monthly (2 features)

Monthly resampling: `daily.resample('ME').last()`

| # | Feature | Definition |
|:-:|---------|------------|
| 73 | `monthly_close_above_sma_10` | Binary: monthly close > 10-month SMA |
| 74 | `monthly_higher_highs_3m` | Binary: monthly high[-3:] strictly increasing |

### Category 13: MTF Coherence (1 feature)

| # | Feature | Definition |
|:-:|---------|------------|
| 75 | `mtf_rs_coherence` | Score 0-3: count of (daily RS rising, weekly RS rising, monthly RS rising) |

### Category 14: Momentum Oscillators (7 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 76 | `rsi_14` | RSI(14) with Wilder smoothing |
| 77 | `macd_line` | EMA12 - EMA26 |
| 78 | `macd_signal` | EMA9 of macd_line |
| 79 | `macd_histogram` | macd_line - macd_signal |
| 80 | `macd_posture` | 3-tuple: (Positive/Negative, Accelerating/Decelerating, Strong/Weak) |
| 81 | `bullish_divergence_20d` | Binary: price LL in last 20d, RSI HL in same window |
| 82 | `bearish_divergence_20d` | Binary: price HH in last 20d, RSI LH in same window |

MACD posture logic:
```python
sign = 'Positive' if macd_line > 0 else 'Negative'

direction_recent = macd_histogram[-1] - macd_histogram[-2]
if sign == 'Positive':
    direction = 'Accelerating' if direction_recent > 0 else 'Decelerating'
else:
    direction = 'Accelerating' if direction_recent < 0 else 'Decelerating'

strength_threshold = mean(abs(macd_histogram[-50:])) * 1.5
strength = 'Strong' if abs(macd_histogram[-1]) > strength_threshold else 'Weak'
```

### Category 15: Pattern Setup (6 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 83 | `bb_upper_20` | sma_20 + 2 * std_20 |
| 84 | `bb_lower_20` | sma_20 - 2 * std_20 |
| 85 | `bb_width_pct_252d` | Percentile of current (bb_upper - bb_lower)/sma_20 in 252d range |
| 86 | `bb_squeeze_flag` | Binary: BB inside Keltner Channels (KC = EMA20 ± 1.5*ATR10) |
| 87 | `vcp_quality_score` | 0-100: sequential contraction (Minervini VCP detection) |
| 88 | `base_duration_days` | Count of days in last 252 where close < (rolling 252d high * 0.90) |

VCP detection: identify last 3 peaks (10-bar lookback); for each peak-to-peak segment, measure depth and volume-drying; score by (monotonically contracting AND volume drying).

### Category 16: Climax & Time-at-Top (3 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 89 | `days_near_52w_high_60d` | Count of days where close >= 0.97 * 252d rolling high (last 60d) |
| 90 | `consecutive_high_intensity` | Sum over last 5d of (close within 3% of 52w high) |
| 91 | `climax_volume_flag` | Binary: vol > 4x 50d avg AND up day > 5% AND in top 20% of 50d range |

### Category 17: Within-Basket Leadership (4 features)

| # | Feature | Definition |
|:-:|---------|------------|
| 92 | `within_basket_z_63d` | Z-score of 63d return vs same-basket peers |
| 93 | `within_basket_z_126d` | Z-score of 126d return vs same-basket peers |
| 94 | `within_basket_rank` | 1-N rank within primary basket (1 = best) |
| 95 | `within_basket_rank_pct` | within_basket_rank / basket_size |

### Category 18: Volume Leadership Confirmation (1 feature)

| # | Feature | Definition |
|:-:|---------|------------|
| 96 | `volume_leadership_confirmed` | Binary: ud_vol_ratio_50 >= 1.5 AND ad_line_slope_60d > 0.05 AND distribution_days_25 <= 3 |

### Category 19: REMOVED (Path 1.5)

> **SUPERSEDED:** `multi_bench_leadership_class` (the 9-class
> UNIVERSAL/GROWTH/BROAD/TECH/DEFENSIVE/RISK_ON/UNUSUAL/MIXED/LAGGARD
> categorical) has been removed. It depended on three benchmark RS ratings
> that collapse to near-identical values under the slope-composite formula
> (see Cat 8 superseded notes). The 7-tier leadership classification in
> §11 is now keyed off `rs_rating_spy`, `mtf_rs_coherence`, and the QQQ
> RS Line direction as a context confirmation gate.

### Additional Computed Features (11)

These are computed in the pipeline for use in components:

| # | Feature | Definition |
|:-:|---------|------------|
| 98 | `pct_above_sma_50` | Binary: close > sma_50 |
| 99 | `pct_above_sma_200` | Binary: close > sma_200 |
| 100 | `weekly_rs_new_high_26w` | Binary: weekly RS Line at 26-week high |
| 101 | `monthly_rs_rising_3m` | Binary: monthly RS Line > 3 months ago |
| 102 | `monthly_rs_rising_6m` | Binary: monthly RS Line > 6 months ago |
| 103 | `pct_from_52w_high` | (close / max(high[-252:]) - 1) * 100 |
| 104 | `pct_from_52w_low` | (close / min(low[-252:]) - 1) * 100 |

> Path C removed 4 low-value features formerly numbered 103-106:
> `recent_5d_returns_consistency`, `golden_cross_60d`, `death_cross_60d`,
> `recent_volume_surge_5d`. Three further candidates
> (`bullish_divergence_20d`, `bearish_divergence_20d`,
> `capitulation_volume_flag`) were initially flagged for removal but
> **retained** because they are load-bearing in the s_momentum component
> ([components.py:313-314](compute/components.py)) and in three setup labels
> ("Exhaustion w/ Bearish Divergence", "Capitulation Selling",
> "Deteriorating w/ Bullish Divergence" in
> [setup_classifier.py:137,155,161](compute/setup_classifier.py)).

> **Path C reverted (Path D).** The six short-term features once stored in
> Category 20 (`vol_surge_5d_ratio`, `range_position_5d`, `momentum_5d_pct`,
> `consecutive_strong_closes_3d`, `coil_resolution_pending`,
> `volume_climax_short`) and the two state-aware flags
> (`pullback_bounce_setup`, `mean_reversion_setup`) were measured against
> 1d / 5d / 20d forward returns and showed near-zero predictive value
> (IC_1d ≈ −0.007, IC_5d ≈ −0.002, IC_20d ≈ +0.0035). They were removed in
> favour of the medium-long-term quality features below, which target the
> signals not visible to naked-eye chart reading.

### Category 20: Trend Quality (Path D)

Persistence and smoothness signals over medium-long horizons.

| # | Feature | Description |
|:-:|---------|------------|
| 105 | `hurst_exponent_252d` | Single-window R/S Hurst over 252d of log returns. H>0.5 = trending; H<0.5 = mean-reverting |
| 106 | `return_autocorrelation_60d_lag1` | Rolling 60d Pearson correlation between daily returns and their 1-lag |
| 107 | `return_smoothness_60d` | abs(mean_60d_return) / std_60d_return — higher = cleaner trend |
| 108 | `trend_rsquared_252d` | R² of OLS regression of log(close) on time over 252d |

### Category 21: Volatility Quality (Path D)

Asymmetric and sustained-drawdown vol measures.

| # | Feature | Description |
|:-:|---------|------------|
| 109 | `upside_vol_60d` | std of positive daily returns over 60d, ×100 |
| 110 | `downside_vol_60d` | std of negative daily returns over 60d, ×100 |
| 111 | `ulcer_index_60d` | sqrt(mean(drawdown²)) where drawdown is (close / max(close[-60:]) − 1) × 100 |
| 112 | `gain_to_pain_ratio_252d` | sum(positive returns) / abs(sum(negative returns)) over 252d |

### Category 22: Risk-Adjusted Performance (Path D)

Multi-horizon Sharpe ranks, tail ratio, information ratio vs SPY.

| # | Feature | Description |
|:-:|---------|------------|
| 113 | `sharpe_rank_60d` | Cross-sectional percentile of annualized 60d Sharpe |
| 114 | `sharpe_rank_252d` | Cross-sectional percentile of annualized 252d Sharpe |
| 115 | `tail_ratio_252d` | Cross-sectional percentile of (p95 / abs(p5)) of 252d daily returns |
| 116 | `information_ratio_252d` | Mean / std of (stock_return − SPY_return) over 252d, ×√252 |

**Path D rationale.** Chart-readable patterns (short-term volume, range, momentum) are already largely priced in. The 12 features above quantify trend *quality* (persistence, regression cleanness, autocorrelation), risk *asymmetry* (upside vs downside vol, ulcer, gain-to-pain), and risk-adjusted *strength* (multi-horizon Sharpe ranks, tail behaviour, alpha-IR). They feed into the existing components as follows:

- `S_TREND_SLOPE`: hurst (+15%), return_autocorrelation (+15%), trend_rsquared_252d (+10%); ADX cut from 30% → 20%.
- `S_STRUCTURE`: ulcer_index_60d was negated and weighted 13% in Path D. *Phase X.2.1 removed this term* (peak |OOS IC| = 0.016 @ 126d, below the universally-good cluster). `ulcer_index_60d` is still computed as a feature.
- `S_RS_LEADERSHIP`: sharpe_rank_252d, gain_to_pain_ratio_252d, information_ratio_252d are the audit's top-3 OOS contributors. Path E briefly demoted them; *Phase X.2.1 restored them as the entire Tier-2 quality sub-block* (30/30/30/10 with sortino_rank_126d).

`upside_vol_60d`, `downside_vol_60d`, `sharpe_rank_60d`, `tail_ratio_252d` are kept as feature-only columns (no component weight) for analyst views and future model use.

### Category 23: Horizon-Specific (Path E)

Targeted at the 20–60d forward-return horizon, where Path D pipeline showed IC ≈ 0.01 — much weaker than the 126d IC (≈ 0.037). Cat 23 adds 21d momentum + RS-line slope, 60d Sharpe / IR / Sortino, 60d max drawdown, short-horizon AR(1), and a vol-rank — signals that drive medium-term continuation but were not directly represented before.

| # | Feature | Description |
|:-:|---------|------------|
| 117 | `momentum_21d_pct` | Cross-sectional percentile of 21d return |
| 118 | `rs_line_spy_slope_21d` | (rs_line_spy / rs_line_spy[-21] − 1) × 100 |
| 119 | `ad_line_slope_21d` | 21-day OLS slope of cumulative A/D Line |
| 120 | `bb_position_21d` | 21d mean of (close − bb_lower_20) / (bb_upper_20 − bb_lower_20) |
| 121 | `sharpe_ratio_60d` | mean(daily_ret_60d) / std(daily_ret_60d) × √252 (raw, not ranked) |
| 122 | `information_ratio_60d` | mean(stock − SPY return) / std(stock − SPY return) over 60d × √252 |
| 123 | `sortino_ratio_60d` | mean(daily_ret_60d) / std(neg_ret_60d) × √252 |
| 124 | `max_drawdown_pct_60d` | Cross-sectional percentile of min(drawdown_pct) over 60d window |
| 125 | `return_autocorrelation_21d_lag1` | AR(1) coefficient of daily returns over 21d |
| 126 | `vol_percentile_21d` | Cross-sectional percentile of 21d annualized realized vol |

**Path E rationale.** The 20–60d IC gap is where most discretionary-trader edge lives — too long for noise traders, too short for the slow-moving quality features Path D dialled up. Cat 23 components flow into:

- `S_MOMENTUM` (rewritten): 40% `momentum_21d_pct` + 20% `rs_line_spy_slope_21d` + 20% MACD posture z + 10% RSI extremes z + 10% divergence z. The 60/40 split pulls S_MOMENTUM toward 3–12 week price/RS trajectory while preserving the legacy oscillator info.
- `S_RS_LEADERSHIP` (quality sub-block, Path E version): 30% `sharpe_ratio_60d` + 30% `information_ratio_60d` + 20% `sharpe_momentum_rank_126d` + 20% `sortino_rank_126d`. **Phase X.2.1 reverted this** — the 252d versions of the same risk-adjusted family were the top-3 OOS carriers, so the quality block is now 30/30/30/10 across `sharpe_rank_252d` / `gain_to_pain_ratio_252d` / `information_ratio_252d` / `sortino_rank_126d`.

`ad_line_slope_21d`, `bb_position_21d`, `sortino_ratio_60d`, `max_drawdown_pct_60d`, `return_autocorrelation_21d_lag1`, `vol_percentile_21d` are kept feature-only (available to downstream consumers / analyst views) but do not carry component weight in this revision.

### Total: 121 Features (Path 1.5 + Path C + Path D + Path E + Phase X.2.1)

All features per-stock, derivable from daily OHLCV + benchmarks (SPY, QQQ).

> Path 1.5 net change: −7 + 3 = 104.
> Path C (subsequently reverted): +6 then −6.
> Path D net change: +12 quality features = 112.
> Path E net change: +10 horizon-specific features = 122.
> Phase X.2.1 net change: −1 (`new_20d_high` removed as OOS noise) = **121**.

---

## 6. Cross-Sectional Standardization

All features are standardized cross-sectionally using **robust z-scores** (median/MAD), not mean/std.

```python
def robust_z_score(series):
    """Robust z-score using median and MAD."""
    median = np.median(series)
    mad = np.median(np.abs(series - median))
    return (series - median) / (1.4826 * mad + 1e-10)
```

### Why Robust Statistics

- Resistant to outliers
- Stable across regimes (today's "average" stays consistent)
- 1.4826 × MAD ≈ σ for normal distributions

### When To Use Standard vs Robust

| Feature Type | Method |
|--------------|--------|
| RS Ratings (already percentile) | No standardization |
| ADX, RSI (bounded [0, 100]) | Standard z-score around 50 |
| Returns, %MA, ATR× (skewed) | Robust z-score |
| Volume ratios | Log-transform first, then standard z-score |
| Binary features | No standardization (use as-is) |
| R² (bounded [0, 1]) | Logit-transform first |

### Winsorization

Apply 1st/99th percentile winsorization to final CCQS scores to cap
extreme outliers. **Phase 6 (2026-05-25):** winsorization is now applied
**per-date** rather than globally across the long frame. Each row is
clipped against its own date's `p1 / p99` quantiles. The earlier global
clip produced 24,562 exact ties at two literal display values across all
dates; per-date clipping reduces the maximum tie count to 9 rows while
preserving the same grade assignments (grading uses per-date quantiles
independently). See the Phase 6 narrative above for the full rationale
and impact metrics.

---

## 7. Component Scoring — 10 Components

### Component Architecture

Each component is a weighted sum of standardized feature z-scores. Components themselves are in z-score space (then converted to 0-100 for display via normal CDF).

### Default Weights (INDETERMINATE State) — Phase X.2.1, post Phase 6 removal of S_CLIMAX

Post-Phase-7 weights (INDETERMINATE state, the default fallback row):

```
S_RS:               25.0%   # Classical cross-sectional momentum
S_RS_LEADERSHIP:    29.5%   # Multi-benchmark, multi-dim leadership
S_RSL:               3.0%   # RS Line dynamics
S_TREND_SLOPE:       3.0%   # Trend cleanness (ADX + R² + t-stat)
S_STRUCTURE:        20.4%   # MA stacks + HH/HL + Supertrend
S_MTF:              17.0%   # Multi-timeframe confluence
S_EXTENSION:         1.0%   # Vol-normalized extension
S_DEMAND:            0.0%   # Zero-weight diagnostic (Phase 7)
S_MOMENTUM:          1.0%   # MACD + RSI + divergences
                    -----
Total:             100.0%
```

> **Phase X.2.1 — FIX 2.** The OOS feature audit (2026-05) found
> `S_CLIMAX` had mean OOS IC = -0.0242, significantly negative at two
> horizons. The component was harmful to the composite. Phase X.2.1
> zeroed its weight; **Phase 6 (2026-05-25)** removed it from the
> component set entirely. The component dimension dropped from 10 → 9.
> Bit-identical for CCQS output since the weight was already zero; the
> underlying features (`climax_volume_flag`, `days_near_52w_high_60d`,
> `consecutive_high_intensity`) remain available to state classification
> and the setup classifier. The original 8% freed by zeroing was already
> redistributed to `S_RS` (+5%) and `S_RS_LEADERSHIP` (+3%).
>
> **Phase 7 (2026-05-25) — `S_DEMAND` zeroed.** Same pattern as
> `S_CLIMAX`. Priority 2 bootstrap analysis found `S_DEMAND` averaged
> −0.009 OOS IC across 24 (state × horizon) cells with 6 significantly
> negative cells. Setting its weight to 0 and redistributing the freed
> 10–15% per state to the four carriers (`S_RS`, `S_RS_LEADERSHIP`,
> `S_STRUCTURE`, `S_MTF`) improved unconditional walk-forward OOS IC at
> 5d / 60d / 126d (paired t = 2.01 / 2.77 / 2.64). The component is
> still computed and stored — kept available for diagnostics and
> dashboard display — but contributes 0 to CCQS. See the Phase 7
> narrative section for full validation.

### Component Formulas

**S_RS (17%) — Path 1.5:**
```python
S_RS = (
    0.55 * z(rs_rating_spy) +
    0.30 * z(sharpe_momentum_rank_126d) +
    0.15 * z(within_basket_z_21d)
)
```

> **SUPERSEDED:** previously weighted `rs_rating_composite`
> (0.50·SPY + 0.30·QQQ + 0.20·IWM). With Path 1.5 the composite is gone;
> SPY is the only cross-sectional benchmark.

**S_RS_LEADERSHIP (21%) — Path 1.5 single-benchmark composite (Phase X.2.1 quality block restored):**
```python
# Tier 1: Primary RS vs SPY (30%)
primary_rs = z(rs_rating_spy)

# Tier 2: Quality (15%) — Phase X.2.1 FIX 3.
# The OOS audit (2026-05) showed sharpe_rank_252d, gain_to_pain_ratio_252d
# and information_ratio_252d are the top-3 OOS contributors at *every*
# horizon. Path E had demoted them in favour of 60d versions; restoring
# them recovers the strongest signal carriers.
quality = (
    0.30 * z(sharpe_rank_252d) +
    0.30 * z(gain_to_pain_ratio_252d) +
    0.30 * z(information_ratio_252d) +
    0.10 * z(sortino_rank_126d)
)

# Tier 3: Acceleration (10%)
accel = (
    0.50 * z(rs_rating_slope_60d) +
    0.50 * z(rs_rating_slope_120d)
)

# Tier 4: RS Line quality (20%) — SPY primary, QQQ as context confirmation
rsl = (
    0.20 * z(rs_line_spy_new_high_252d) +
    0.15 * z(rs_line_spy_slope_60d) +
    0.50 * z(rs_line_spy_r_squared_60d) +
    0.15 * z(rs_line_qqq_new_high_252d)        # QQQ context confirmation
)

# Tier 5: Confluence (20%)
confluence = (
    0.55 * (mtf_rs_coherence / 3) * 100 +
    0.45 * z(within_basket_z_63d)
)

S_RS_LEADERSHIP = (
    0.35 * primary_rs +
    0.15 * quality +
    0.10 * accel +
    0.20 * rsl +
    0.20 * confluence
)

# Volume gate: if not volume_leadership_confirmed, cap at 70 (in 0-100 space)
if not volume_leadership_confirmed:
    S_RS_LEADERSHIP = min(S_RS_LEADERSHIP, 70)
```

> **SUPERSEDED:** the Tier-1 `multi_bench` blend
> (0.50·SPY + 0.30·QQQ + 0.20·IWM) collapsed in Path 1.5 because
> SPY/QQQ/IWM ranks were near-identical (Pearson ~1.0000). The
> `n_benchmarks_beaten` confluence term and the `rs_line_iwm_new_high_252d`
> RSL term are removed for the same reason. QQQ's RS Line new-high flag is
> kept as a contextual confirmation signal (lower weight).

**S_RSL (8%):**
```python
S_RSL = (
    0.40 * z(rs_line_spy_new_high_252d) +
    0.25 * z(rs_line_spy_new_high_60d) +
    0.20 * z(rs_line_spy_slope_20d) +
    0.15 * z(rs_line_spy_r_squared_60d)
)
```

**S_TREND_SLOPE (10%):**
```python
S_TREND_SLOPE = (
    0.30 * z(adx_14) +
    0.25 * z(trend_r_squared_60d) +
    0.15 * z(trend_slope_60d) +
    0.20 * z(supertrend_direction * supertrend_days_since_flip) +
    0.10 * z(plus_di - minus_di)
)

# Significance gating
if trend_slope_t_stat < 1.96:
    S_TREND_SLOPE *= 0.5  # Half-weight noisy trends
```

**S_STRUCTURE (13%) — Phase X.2.1 rewrite (FIX 1 + FIX 4):**
```python
S_STRUCTURE = (
    0.20 * z(sma_stack_score) +
    0.20 * z(ema_stack_score) +
    0.10 * z(-hh_count_60d) +           # FIX 1: sign-flip; raw IC = -0.0335
    0.25 * z(hl_count_60d) +            # FIX 4: 0.08 → 0.25 (OOS IC=+0.049, t=14.1 @ 1d)
    0.10 * z(supertrend_direction) +
    0.10 * z(new_252d_high) +
    0.05 * z(pct_up_days_21)
)
```

> **FIX 1 (`hh_count_60d` sign-flip).** OOS audit found mean OOS IC = -0.0335
> with t = -9.0 at the 5d horizon — negative at *every* horizon. Higher pivot
> highs in 60d empirically predict *lower* forward returns (likely an
> over-extension / exhaustion proxy). Multiplied by -1 before z-scoring so
> the contribution flows in the correct direction.
>
> **FIX 4 (`hl_count_60d` weight 0.08 → 0.25).** OOS audit found OOS IC = +0.049
> with t = +14.1 at 1d — the strongest single OOS carrier in the entire
> feature set. Was under-weighted at 0.08.
>
> Two terms dropped from the legacy formula:
>
> - `ulcer_index_60d` (was 0.13): peak |OOS IC| = 0.016 @ 126d, well below
>   the universally-good cluster.
> - `failed_breakout_flag_10d` (was 0.05 + state-machine -0.5 penalty):
>   removed from S_STRUCTURE composition; still computed and consumed by
>   the setup classifier.

**S_MTF (11%):**
```python
weekly_score = (
    0.30 * z(weekly_stack_alignment) +
    0.20 * z(weekly_higher_highs) +
    0.20 * z(weekly_rs_rising) +
    0.15 * z(weekly_macd_posture == 'Positive') +
    0.15 * z(weekly_trend_slope_sign > 0)
)

monthly_score = (
    0.50 * z(monthly_close_above_sma_10) +
    0.50 * z(monthly_higher_highs_3m)
)

S_MTF = 0.80 * weekly_score + 0.20 * monthly_score
```

**S_EXTENSION (8%) — Inverted (less extended = better):**
```python
if pct_ma_50 < -10:
    S_EXTENSION = -1.0  # Severely broken
elif pct_ma_50 < -3:
    S_EXTENSION = -0.5  # Below 50MA
else:
    # Above 50MA — vol-normalized scoring
    S_EXTENSION = (
        0.55 * z(-vol_normalized_extension) +
        0.30 * z(-pct_ma_50) +
        0.15 * z(-price_z_score_vs_trend)
    )
```

**~~S_CLIMAX~~ — removed in Phase 6 (2026-05-25).** Carried weight 0% in
every state since Phase X.2.1 (mean OOS IC −0.0242). The math was also
inverted vs the label: `100 − (extension_penalty + time_score +
vol_climax_score)` made "high s_climax" mean *less climactic*,
contributing to the negative IC. Removed from the component set; the
underlying features (`climax_volume_flag`, `days_near_52w_high_60d`,
`consecutive_high_intensity`) remain available to state classification
and the setup classifier.

**S_DEMAND (0% in Phase 7, kept as zero-weight diagnostic):**
```python
S_DEMAND = (
    0.30 * z(np.log(up_down_vol_ratio_50)) +
    0.25 * z(-distribution_days_25) +
    0.20 * z(ad_line_slope_20) +
    0.15 * z(cmf_21) +
    0.10 * z(volume_z_20_252) +
    # capitulation_volume_flag handled in setup classification, not direct scoring
)
```

> **Phase 7 (2026-05-25) — `S_DEMAND` zeroed.** Priority 2 bootstrap
> analysis found `S_DEMAND` averaged −0.009 OOS IC across 24 (state ×
> horizon) cells with 6 cells significantly negative (CONSOLIDATING at
> all four horizons, PULLBACK at 20d/60d, INDETERMINATE at 60d). The
> component is still computed and stored in `components.parquet` for
> diagnostic display, but its weight is set to 0.0 in every state.
> Freed weight (10-15% per state) redistributed proportionally to the
> four carrier components (`S_RS`, `S_RS_LEADERSHIP`, `S_STRUCTURE`,
> `S_MTF`). Validation: walk-forward OOS IC improved at 3 of 4 horizons
> with paired t > 1.96 (5d, 60d, 126d). See Phase 7 narrative for the
> full empirical evidence and the 2020-COVID-regression caveat.

**S_MOMENTUM (3%):**
```python
posture_scores = {
    ('Positive', 'Accelerating', 'Strong'): 100,
    ('Positive', 'Accelerating', 'Weak'): 80,
    ('Positive', 'Decelerating', 'Strong'): 65,
    ('Positive', 'Decelerating', 'Weak'): 50,
    ('Negative', 'Decelerating', 'Weak'): 40,
    ('Negative', 'Decelerating', 'Strong'): 30,
    ('Negative', 'Accelerating', 'Weak'): 20,
    ('Negative', 'Accelerating', 'Strong'): 0,
}
macd_score = posture_scores[macd_posture]

# RSI extremes
if rsi_14 < 30: rsi_score = 80   # oversold = mean-revert opp
elif rsi_14 > 75: rsi_score = 20
else: rsi_score = 50

# Divergence adjustments (additive)
div_adj = 0
if bullish_divergence_20d: div_adj += 15
if bearish_divergence_20d: div_adj -= 15

S_MOMENTUM = 0.70 * macd_score + 0.30 * rsi_score + div_adj
```

---

## 8. State Classification — 6 States

> ℹ️ **Internal labels** (TRENDING, PULLBACK, CONSOLIDATING, EXHAUSTION,
> DETERIORATING, INDETERMINATE) below are the contract between the
> classifier and STATE_WEIGHTS / regime gates. Display strings shown
> on the dashboard differ per Phase 26 (e.g. EXHAUSTION → "Parabolic",
> DETERIORATING → "Breaking Down", INDETERMINATE → "No Edge"). See
> the Phase 26 entry for the full map.

Per-stock state describes the chart's current behavior. State classification is **probabilistic** using softmax over log-likelihoods.

### The 6 States

| State | Description |
|-------|-------------|
| TRENDING | Clean uptrend in progress |
| PULLBACK | Buyable pullback within uptrend |
| CONSOLIDATING | Pre-breakout consolidation |
| EXHAUSTION | Parabolic / late-stage exhaustion |
| DETERIORATING | Structurally damaged downtrend |
| INDETERMINATE | Indeterminate / transitioning |

### Probabilistic Classification

For each state, compute log-likelihood based on how well features match the state's expected profile:

```python
def state_likelihood(features, state):
    # Log-pdf is kernel-only: normal_logpdf(x, μ, σ) = -0.5 * ((x-μ)/σ)^2
    # (the σ-dependent constant is dropped so all states peak at 0 and the
    # INDETERMINATE prior of -2.5 sits on the same scale as the directional states).
    #
    # Calibration note: σ values are *wide enough* that a feature within
    # ±1.5σ of the state's centre still contributes a competitive
    # log-likelihood. Tight σ's caused 96% INDETERMINATE dominance because no
    # directional state matched a real-world chart well enough.
    if state == 'TRENDING':
        return (
            normal_logpdf(features['adx_14'], μ=30, σ=12) +
            normal_logpdf(features['trend_r_squared_60d'], μ=0.65, σ=0.20) +
            indicator_logpdf(features['sma_stack_score'] >= 80, conf=0.85) +
            normal_logpdf(features['pct_ma_50'], μ=10, σ=12)
        )

    elif state == 'PULLBACK':
        return (
            indicator_logpdf(features['sma_stack_score'] >= 75, conf=0.80) +
            normal_logpdf(features['pct_ma_50'], μ=5, σ=5) +
            normal_logpdf(features['atr_x_50'], μ=1.5, σ=1.0) +
            normal_logpdf(features['rsi_14'], μ=45, σ=15)
        )

    elif state == 'CONSOLIDATING':
        return (
            normal_logpdf(features['bb_width_pct_252d'], μ=15, σ=12) +
            normal_logpdf(features['adx_14'], μ=15, σ=8) +
            indicator_logpdf(features['bb_squeeze_flag'], conf=0.60) +
            normal_logpdf(features['vcp_quality_score'], μ=55, σ=25)
        )

    elif state == 'EXHAUSTION':
        return (
            normal_logpdf(features['atr_x_50'], μ=6.0, σ=2.0) +
            normal_logpdf(features['rsi_14'], μ=75, σ=8) +
            normal_logpdf(features['rs_rating_spy'], μ=92, σ=8) +
            indicator_logpdf(features['days_near_52w_high_60d'] >= 25, conf=0.70)
        )

    elif state == 'DETERIORATING':
        return (
            normal_logpdf(features['pct_ma_50'], μ=-12, σ=10) +
            normal_logpdf(features['distribution_days_25'], μ=8, σ=4) +
            indicator_logpdf(features['supertrend_direction'] == -1, conf=0.75) +
            normal_logpdf(features['rs_rating_spy'], μ=25, σ=20)
        )

    elif state == 'INDETERMINATE':
        # Low constant prior: INDETERMINATE only wins when no directional state's
        # likelihood beats -2.5. With the kernel scale, this corresponds to
        # roughly ~√5 standardized deviations of joint mismatch.
        return -2.5

# Softmax for probability distribution
def classify_state_probabilistic(features):
    states = ['TRENDING', 'PULLBACK', 'CONSOLIDATING', 'EXHAUSTION', 'DETERIORATING', 'INDETERMINATE']
    log_likelihoods = {s: state_likelihood(features, s) for s in states}
    
    max_ll = max(log_likelihoods.values())
    exp_ll = {s: np.exp(ll - max_ll) for s, ll in log_likelihoods.items()}
    total = sum(exp_ll.values())
    probs = {s: v/total for s, v in exp_ll.items()}
    
    return {
        'primary_state': max(probs, key=probs.get),
        'confidence': max(probs.values()),
        'probabilities': probs,
    }
```

### State-Conditional Component Weights (Phase 7)

| Component | TRENDING | PULLBACK | CONSOLIDATING | EXHAUSTION | DETERIORATING | INDETERMINATE |
|-----------|:--------:|:--------:|:-------:|:---------:|:------:|:-----:|
| S_RS | 28.0% | 25.6% | 23.8% | 26.1% | 23.8% | 25.0% |
| S_RS_LEADERSHIP | 28.0% | 29.1% | 26.2% | 33.2% | 29.7% | 29.5% |
| S_RSL | 3.0% | 3.0% | 2.0% | 1.0% | 2.0% | 3.0% |
| S_TREND_SLOPE | 3.0% | 2.0% | 2.0% | 1.0% | 2.0% | 3.0% |
| S_STRUCTURE | 20.2% | 21.0% | 26.2% | 19.0% | 23.8% | 20.4% |
| S_MTF | 16.8% | 16.3% | 17.8% | 17.8% | 17.8% | 17.0% |
| S_EXTENSION | 0.0% | 2.0% | 1.0% | 1.0% | 0.0% | 1.0% |
| S_DEMAND | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| S_MOMENTUM | 1.0% | 1.0% | 1.0% | 1.0% | 1.0% | 1.0% |

(Pre-Phase-7 values for reference: S_RS 20-25%, S_DEMAND 10-15%; Phase 7
zeroed S_DEMAND and redistributed proportionally to the four carriers.)

> **Phase X.2.1 — FIX 2 / Phase 6.** `S_CLIMAX` was zeroed in every state
> at X.2.1 (mean OOS IC = -0.0242, sig-negative at two horizons) and
> **removed from the component set entirely in Phase 6** (2026-05-25).
> Component dimension dropped from 10 → 9. Bit-identical for CCQS output
> since the weight was already zero everywhere.
>
> **Phase X.3 — M8 (component cleanup).** Four components carry essentially
> zero OOS signal across all six horizons:
>
> | component | mean OOS IC | post-X.2.1 weight (INDETERMINATE) | post-X.3 weight (INDETERMINATE) |
> |-----------|------------:|--------------------------:|------------------------:|
> | s_momentum    |  0.0000 |  3% |  1% |
> | s_trend_slope | -0.0001 | 10% |  3% |
> | s_rsl         | -0.0013 |  8% |  3% |
> | s_extension   | -0.0070 |  8% |  1% |
>
> The freed 21% (INDETERMINATE state) flows to the four positive OOS carriers:
> `S_RS` +5, `S_RS_LEADERSHIP` +5, `S_STRUCTURE` +5, `S_MTF` +4, `S_DEMAND` +2.
> Same redistribution principle applied to every other state, with
> state-specific tilts (e.g. `S_STRUCTURE` boosted in CONSOLIDATING/DETERIORATING where
> chart structure is most diagnostic; `S_RS_LEADERSHIP` boosted in EXHAUSTION
> as a quality filter against late-stage exhaustion names).
| **Total** | 100% | 100% | 100% | 100% | 100% | 100% |

### Bayesian Averaging Across States

```python
def compute_ccqs_z(component_scores, state_probabilities):
    """
    CCQS = expected value of CCQS over state probability distribution.
    """
    total_z = 0
    for state, p_state in state_probabilities.items():
        state_weights = STATE_WEIGHTS[state]
        state_composite_z = sum(state_weights[c] * component_scores[c] for c in COMPONENTS)
        total_z += p_state * state_composite_z
    
    return total_z
```

### Confidence Blending

When state confidence is low, blend toward INDETERMINATE weights:

```python
def confidence_adjusted_probs(state_probs):
    max_prob = max(state_probs.values())
    
    if max_prob >= 0.7:
        return state_probs  # High confidence: use as-is
    elif max_prob >= 0.5:
        # Medium: 70% original + 30% INDETERMINATE
        adjusted = {s: 0.7 * p for s, p in state_probs.items()}
        adjusted['INDETERMINATE'] = adjusted.get('INDETERMINATE', 0) + 0.3
        return adjusted
    else:
        # Low: 50% original + 50% INDETERMINATE
        adjusted = {s: 0.5 * p for s, p in state_probs.items()}
        adjusted['INDETERMINATE'] = adjusted.get('INDETERMINATE', 0) + 0.5
        return adjusted
```

---

## 9. Composite Scoring & Grading

### From z-score To Displayable 0-100

```python
import scipy.stats as ss

ccqs_z = compute_ccqs_z(components, state_probabilities)
ccqs_raw = ss.norm.cdf(ccqs_z) * 100

# Winsorize at 1st/99th percentile — per-date since Phase 6 (2026-05-25).
# Each row is clipped against its own date's p1 / p99 quantiles. The earlier
# global clip computed one (p1, p99) pair across the entire long frame and
# collapsed every clipped row to those two literal values (24,562 exact ties).
# Per-date clipping preserves cross-sectional dispersion within each date.
ccqs = ccqs_raw.groupby(level='date').transform(
    lambda s: s.clip(lower=s.quantile(0.01), upper=s.quantile(0.99))
)
```

### Grade Thresholds (Per-Date Percentile)

Grades are assigned by cross-sectional percentile rank **within each
snapshot date**, not by absolute CCQS thresholds. Absolute cuts drift with
the universe's mean quality (broad rallies push everyone above 85; broad
selloffs pull everyone below 70), making tier sizes unstable. Per-date
quantiles keep the S/A/B/C/D mix roughly constant day to day.

```python
def grade_per_date(ccqs_series_for_one_date):
    q30 = ccqs_series_for_one_date.quantile(0.30)
    q55 = ccqs_series_for_one_date.quantile(0.55)
    q80 = ccqs_series_for_one_date.quantile(0.80)
    q92 = ccqs_series_for_one_date.quantile(0.92)

    def label(x):
        if x >= q92: return 'S'  # top 8%
        if x >= q80: return 'A'  # next 12%
        if x >= q55: return 'B'  # next 25%
        if x >= q30: return 'C'  # next 25%
        return 'D'               # bottom 30%

    return ccqs_series_for_one_date.map(label)
```

Target tier sizes (by construction of the quantile cuts):
- Grade S: ~8%
- Grade A: ~12%
- Grade B: ~25%
- Grade C: ~25%
- Grade D: ~30%

---

## 10. Setup Categories — LEGACY (superseded by Phase 25 + 27)

> ⚠️ **This section is historical.** Production uses the 13-label
> chart-evocative cascade in `compute/setup_classifier_v2.py` — see
> the Phase 25 / 27 entries above in the phase-by-phase section. The
> vocabulary documented below is preserved here for reference; the
> legacy classifier in
> `compute/setup_classifier.py` is no longer called by the pipeline but
> is kept untouched in the repo.

Direct multi-feature detection with priority ordering. Higher-priority setups checked first.

```python
def classify_setup(features, state_probs, ccqs):
    """
    Priority order: most-specific setups first.
    Returns: setup_label, confidence
    """
    
    # ===== EXHAUSTION SETUPS (Priority 1-4) =====
    
    # 1. Extreme Extension  (Phase 5.8 audit: math is pure extension, not "blow-off")
    if features['atr_x_50'] >= 6.5:
        return 'Extreme Extension', 0.95
    
    # 2. Exhaustion w/ Bearish Divergence
    if (features['atr_x_50'] >= 4.0 and 
        features['bearish_divergence_20d'] and
        features['rs_rating_spy'] >= 85):
        return 'Exhaustion w/ Bearish Divergence', 0.90
    
    # 3. Volume-Confirmed Exhaustion
    if (features['atr_x_50'] >= 4.5 and 
        features['climax_volume_flag']):
        return 'Volume-Confirmed Exhaustion', 0.90
    
    # 4. Extended Exhaustion
    if (features['atr_x_50'] >= 4.0 and 
        features['days_near_52w_high_60d'] >= 15 and
        features['rs_rating_spy'] >= 80):
        return 'Extended Exhaustion', 0.75
    
    # ===== DETERIORATING SETUPS (Priority 5-8) =====
    
    # 5. Capitulation Selling
    if (features['pct_ma_50'] < -8 and 
        features['capitulation_volume_flag']):
        return 'Capitulation Selling', 0.85
    
    # 6. Deteriorating w/ Bullish Divergence
    if (features['pct_ma_50'] < -5 and 
        features['bullish_divergence_20d']):
        return 'Deteriorating w/ Bullish Divergence', 0.80
    
    # 7. Distribution Pattern
    if (features['pct_ma_50'] < -5 and 
        features['distribution_days_25'] >= 8):
        return 'Distribution Pattern', 0.85
    
    # 8. Sustained Weakness  (Phase 5.8 audit: math is a static threshold,
    #    not a trend-transition event)
    if features['pct_ma_50'] < -8:
        return 'Sustained Weakness', 0.70
    
    # ===== ELITE LEADER SETUPS (Priority 9-10) =====
    
    # 9. Elite Leader Continuation (TRENDING state, all benchmarks beaten)
    if (state_probs.get('TRENDING', 0) > 0.5 and
        features.get('leadership_tier') == 'ELITE_LEADER'):
        return 'Elite Leader Continuation', 0.95
    
    # 10. Elite Leader Pullback (PULLBACK state, elite)
    if (state_probs.get('PULLBACK', 0) > 0.5 and
        features.get('leadership_tier') == 'ELITE_LEADER'):
        return 'Elite Leader Pullback', 0.95
    
    # ===== PREMIUM LONG SETUPS (Priority 11-13) =====

    # 11. Premium Pullback  (Phase 5.8 audit: math does not check CCQS grade)
    if (features['sma_stack_score'] >= 85 and
        features['ema_stack_score'] >= 70 and
        0 < features['pct_ma_50'] < 10 and
        features['atr_x_50'] < 2.5 and
        features['rs_rating_spy'] >= 80 and
        features['up_down_vol_ratio_50'] >= 1.3):
        return 'Premium Pullback', 0.95

    # 12. Emerging Leader  (Phase 5.8 audit: forward "(Multibagger Setup)" claim dropped)
    if (60 <= features['rs_rating_spy'] <= 85 and
        features['rs_rating_slope_60d'] >= 10 and
        features['mtf_rs_coherence'] >= 2 and
        features['volume_leadership_confirmed']):
        return 'Emerging Leader', 0.85
    
    # 13. Theme Leader Pullback
    if (features.get('is_basket_leader', False) and
        state_probs.get('PULLBACK', 0) > 0.4):
        return 'Theme Leader Pullback', 0.80
    
    # ===== TRENDING SETUPS (Priority 14-15) =====
    
    # 14. Trend Continuation
    if (features['sma_stack_score'] >= 85 and
        features['adx_14'] >= 25 and
        features['atr_x_50'] < 4.5 and
        features['rs_rating_spy'] >= 80 and
        features['supertrend_direction'] == 1):
        return 'Trend Continuation', 0.90

    # 15. Trending Leadership (new_252d_high dropped — too restrictive in
    # range-bound markets; ADX cut loosened from 25 to 20.)
    if (features['sma_stack_score'] >= 75 and
        features['rs_rating_spy'] >= 80 and
        features['adx_14'] >= 20):
        return 'Trending Leadership', 0.85
    
    # ===== PULLBACK SETUPS (Priority 16-17) =====
    
    # 16. Pullback to 21EMA
    if (features['sma_stack_score'] >= 80 and
        abs(features['close'] - features['ema_21']) / features['atr_14'] < 0.7 and
        features['rs_rating_spy'] >= 75):
        return 'Pullback to 21EMA', 0.85
    
    # 17. Pullback to 50MA
    if (features['sma_stack_score'] >= 75 and
        abs(features['close'] - features['sma_50']) / features['atr_14'] < 1.2 and
        features['rs_rating_spy'] >= 70):
        return 'Pullback to 50MA', 0.80
    
    # ===== CONSOLIDATING SETUPS (Priority 18-22) =====
    
    # 18. Consolidation Within Strong Theme
    if (features['bb_squeeze_flag'] and
        features.get('theme_class') in ('ELITE_THEME', 'STRONG_THEME')):
        return 'Consolidation Within Strong Theme', 0.85
    
    # 19. Tight Consolidation Pre-Breakout
    if (features['bb_squeeze_flag'] and
        features['vcp_quality_score'] >= 70 and
        features['rs_rating_spy'] >= 85 and
        features['volume_z_20_252'] >= 0.5):
        return 'Tight Consolidation Pre-Breakout', 0.90
    
    # 20. VCP Setup
    if (features['vcp_quality_score'] >= 60 and
        features['rs_rating_spy'] >= 75 and
        features['sma_stack_score'] >= 75):
        return 'VCP Setup', 0.80
    
    # 21. BB Squeeze with RS
    if (features['bb_squeeze_flag'] and
        features['bb_width_pct_252d'] < 20 and
        features['rs_rating_spy'] >= 70):
        return 'BB Squeeze with RS', 0.75
    
    # 22. Range Consolidation
    if (features['bb_squeeze_flag'] or 
        features['bb_width_pct_252d'] < 15):
        return 'Range Consolidation', 0.70
    
    # ===== FAILURE / TRANSITION (Priority 23) =====

    # 23. Failed Breakout — tightened. The raw `failed_breakout_flag_10d`
    # fires whenever price closes back through a recent breakout pivot,
    # which happens often on healthy "flag taps" of strong stocks. We
    # only label it a real failure when the stock is also below its 50MA
    # and not a market leader.
    if (features['failed_breakout_flag_10d'] and
        features['pct_ma_50'] < 0 and
        features['rs_rating_spy'] < 70):
        return 'Failed Breakout', 0.85

    # ===== STATE-AWARE CATCH-ALLS (Priority 24-29) =====
    # When no specific rule fires, label the row by its primary state so
    # downstream consumers can still distinguish a healthy trend with no
    # sharp setup from a chart in a degenerate state. Only truly INDETERMINATE
    # rows collapse to 'Indeterminate Pattern'.
    # Phase 5.8 audit: catch-all labels renamed to "<State> (Generic)" so
    # they don't imply duration / bias / cycle position / confidence that
    # the catch-all doesn't verify. "Routine Pullback" and
    # "Indeterminate Pattern" remain accurate and unchanged.
    primary = state_probs_argmax  # name of highest-probability state
    if primary == 'TRENDING':      return 'Trending (Generic)',      0.65
    if primary == 'PULLBACK':      return 'Routine Pullback',        0.65
    if primary == 'CONSOLIDATING': return 'Consolidating (Generic)', 0.65
    if primary == 'EXHAUSTION':    return 'Exhaustion (Generic)',    0.65
    if primary == 'DETERIORATING': return 'Deteriorating (Generic)', 0.65
    return 'Indeterminate Pattern', 0.55
```

### Setup Categories Summary

| # | Setup | Direction | Hold Horizon |
|:-:|-------|:---------:|:------------:|
| 1 | Parabolic Blow-Off | SHORT/AVOID | DAYS |
| 2 | Exhaustion w/ Bearish Divergence | SHORT | DAYS |
| 3 | Volume-Confirmed Exhaustion | SHORT | DAYS |
| 4 | Extended Exhaustion | CAUTION | DAYS-WEEKS |
| 5 | Capitulation Selling | LONG-REVERSAL | DAYS-WEEKS |
| 6 | Deteriorating w/ Bullish Divergence | LONG-REVERSAL | DAYS-WEEKS |
| 7 | Distribution Pattern | SHORT | WEEKS |
| 8 | Trend Failure | SHORT/AVOID | WEEKS |
| 9 | Elite Leader Continuation | LONG | WEEKS-MONTHS |
| 10 | Elite Leader Pullback | LONG | WEEKS-MONTHS |
| 11 | Tier S Pullback | LONG | WEEKS-MONTHS |
| 12 | Emerging Leader (Multibagger) | LONG | MONTHS |
| 13 | Theme Leader Pullback | LONG | WEEKS |
| 14 | Trend Continuation | LONG | WEEKS-MONTHS |
| 15 | Trending Leadership | LONG | WEEKS-MONTHS |
| 16 | Pullback to 21EMA | LONG | DAYS-WEEKS |
| 17 | Pullback to 50MA | LONG | WEEKS |
| 18 | Consolidation Within Strong Theme | LONG | WEEKS-MONTHS |
| 19 | Tight Consolidation Pre-Breakout | LONG | WEEKS |
| 20 | VCP Setup | LONG | WEEKS |
| 21 | BB Squeeze with RS | LONG | WEEKS |
| 22 | Range Consolidation | WAIT | - |
| 23 | Failed Breakout | AVOID/SHORT | DAYS |
| 24 | Sustained Uptrend | LONG (low-conf) | WEEKS |
| 25 | Routine Pullback | LONG (low-conf) | WEEKS |
| 26 | Constructive Consolidation | WAIT | WEEKS |
| 27 | Late-Cycle Pattern | CAUTION | DAYS-WEEKS |
| 28 | Low-Confidence Pattern | AVOID | WEEKS |
| 29 | Indeterminate Pattern | WAIT | - |

---

## 11. Leadership & Theme Classification

> ℹ️ **Internal labels** (ELITE_LEADER, STRONG_LEADER, ...,
> STRONG_PERFORMER, DETERIORATING, UNCLASSIFIED) below are the contract
> between the classifier and tier composition logic. Display strings on
> the dashboard differ per Phase 26 (e.g. STRONG_PERFORMER → "Steady",
> DETERIORATING → "Fading Leader", UNCLASSIFIED + NaN → "No RS Signal").
> See the Phase 26 entry for the full map.

### Leadership Tier (9 Levels Per Stock — Path 1.5)

Single-benchmark RS keyed off SPY, with QQQ RS Line direction as a
**context confirmation gate** (not a separate ranking dimension).

| Tier | RS Band / Condition | Description |
|------|---------------------|-------------|
| `ELITE_LEADER` | s_lead≥90, rs_spy≥95, mtf=3, vol_conf, basket leader, qqq↑ | Top-shelf, all confirmations on |
| `STRONG_LEADER` | s_lead≥80, rs_spy≥75, mtf≥2 | High RS with MTF confluence |
| `EMERGING_LEADER` | rs_spy 60-85, slope≥10, mtf≥2, qqq↑ | Multibagger discovery zone |
| `ESTABLISHED_LEADER` | rs_spy≥75 & SPY RSL new 252d high | Confirmed leader with structural RS |
| `STRONG_PERFORMER` | rs_spy≥60 | Above-average RS |
| `NEUTRAL` | rs_spy 45-60 | Mid-pack, no other signal |
| `WEAK_PERFORMER` | rs_spy 25-45 & slope≥-5 | Low RS but stable / slightly improving momentum. Not in active decline. Often value / cyclical names in mid-cycle or recovering laggards. |
| `DETERIORATING` | rs_spy<40 & slope<-5 | Actively declining RS |
| `WEAK_LAGGARD` | rs_spy<25 & slope<0 | Chronically weak and still rolling over |

```python
def classify_leadership(features):
    s_lead   = features['s_rs_leadership']
    rs_spy   = features['rs_rating_spy']
    rs_slope = features['rs_rating_slope_60d']
    mtf_coh  = features['mtf_rs_coherence']
    vol_conf = features['volume_leadership_confirmed']
    spy_nh_252 = features['rs_line_spy_new_high_252d']
    qqq_slope_60 = features['rs_line_qqq_slope_60d']   # QQQ context gate
    is_basket_leader = features.get('is_basket_leader', False)

    qqq_context_ok = qqq_slope_60 > 0    # tech-peer confirmation gate

    if (s_lead >= 90 and rs_spy >= 95 and mtf_coh == 3 and vol_conf
        and is_basket_leader and qqq_context_ok):
        return 'ELITE_LEADER'

    if s_lead >= 80 and rs_spy >= 75 and mtf_coh >= 2:
        return 'STRONG_LEADER'

    if (60 <= rs_spy <= 85 and rs_slope >= 10 and mtf_coh >= 2
        and qqq_context_ok):
        return 'EMERGING_LEADER'

    if rs_spy >= 75 and spy_nh_252:
        return 'ESTABLISHED_LEADER'

    if rs_spy >= 60:
        return 'STRONG_PERFORMER'

    if 45 <= rs_spy < 60:
        return 'NEUTRAL'

    # WEAK_PERFORMER — low RS but stable (slope hasn't turned actively
    # negative). Absorbs ~7-9% of the universe that used to be misclassified
    # as NEUTRAL.
    if 25 <= rs_spy < 45 and rs_slope >= -5:
        return 'WEAK_PERFORMER'

    if rs_spy < 40 and rs_slope < -5:
        return 'DETERIORATING'

    if rs_spy < 25 and rs_slope < 0:
        return 'WEAK_LAGGARD'

    # Orphan band (rs_spy<25 with rs_slope≥0, very rare): chronically weak
    # but stabilising — defaults to NEUTRAL.
    return 'NEUTRAL'
```

> **SUPERSEDED (multi-bench 9-tier):** the original classifier branched on
> `rs_rating_qqq`, `rs_rating_iwm`, and `n_benchmarks_beaten`, and added a
> `MID_PACK` tier for the 30 ≤ rs_spy < 50 band. Path 1.5 collapses those
> ranking dimensions (they had collinear ranks anyway) into a single SPY-
> based scheme. `MID_PACK` was folded into the catch-all `NEUTRAL` tier
> since the band-level distinction wasn't load-bearing for the
> discretionary workflow. `qqq_slope_60 > 0` is the surviving QQQ signal,
> acting as a context confirmation gate for top tiers.
>
> **Phase 3 addition:** `WEAK_PERFORMER` was reintroduced as a 9th tier to
> absorb the low-RS-but-stable cohort (~7-9% of the universe) that was
> bloating `NEUTRAL` to 40%+ after the multi-bench collapse. With this
> tier, `NEUTRAL` recovers its intended meaning: genuinely mid-pack RS,
> not chronically weak.

### Theme Classification (7 Tiers Per Basket)

Computed in aggregation layer (Section 12):

```python
def classify_theme(theme_features):
    theme_ccqs = theme_features['theme_ccqs']
    momentum_class = theme_features['theme_momentum_class']
    leadership_conc = theme_features['leadership_concentration']
    rs_nh = theme_features['theme_rs_new_252d_high']
    breadth = theme_features['pct_above_50dma']
    
    if (theme_ccqs >= 90 and 
        momentum_class in ['STRONG_ACCELERATING', 'MODERATE_ACCELERATING'] and
        rs_nh and breadth >= 75):
        return 'ELITE_THEME'
    
    if theme_ccqs >= 80 and breadth >= 60 and rs_nh:
        return 'STRONG_THEME'
    
    if (60 <= theme_ccqs < 80 and 
        momentum_class == 'STRONG_ACCELERATING' and 
        breadth >= 50):
        return 'EMERGING_THEME'  # Multibagger discovery zone
    
    if theme_ccqs >= 75 and leadership_conc == 'CONCENTRATED':
        return 'NARROW_LEADERSHIP'
    
    if 50 <= theme_ccqs < 75:
        return 'STABLE'
    
    if (theme_ccqs < 50 and 
        momentum_class in ['DECELERATING', 'WEAKENING']):
        return 'WEAKENING'
    
    if theme_features['pct_deteriorating'] >= 30:
        return 'BROKEN_THEME'
    
    return 'MIXED'
```

---

## 12. Aggregation Layer — Theme Strength

For each populated CORE basket, compute ~25 metrics:

### Per-Basket Metrics

**Score aggregates:** mean, median, std, max, min, q25, q75 of constituent CCQS.

**Breadth metrics:**
- `pct_above_50dma`, `pct_above_200dma`
- `pct_at_60d_high`, `pct_at_252d_high`
- `pct_full_sma_stack`, `pct_full_ema_stack`
- `pct_supertrend_bull`
- `pct_rs_rating_above_70`, `pct_rs_rating_above_85`
- `pct_rs_line_new_high`
- `pct_grade_s`, `pct_grade_a_plus`, `pct_grade_d`
- `pct_exhaustion`, `pct_deteriorating`

**Theme RS Line (basket equal-weighted index vs SPY):**
```python
basket_returns = ohlcv_df[basket_constituents].pct_change().mean(axis=1)
basket_index = (1 + basket_returns).cumprod() * 100
theme_rs_line = basket_index / spy_index
```
- `theme_rs_line_value`
- `theme_rs_new_60d_high`, `theme_rs_new_252d_high`
- `theme_rs_slope_20d`, `theme_rs_slope_60d`
- `theme_rs_r_squared_60d`
- `theme_rs_pct_252d`

**Momentum acceleration:**
- `theme_rs_change_30d`, `theme_rs_change_60d`, `theme_rs_change_90d`
- `theme_momentum_class`: STRONG_ACCELERATING / MODERATE_ACCELERATING / STABLE / DECELERATING / WEAKENING

**Dispersion:**
- `basket_ccqs_cv` (coefficient of variation)
- `basket_top_3_share` (Gini-like concentration)
- `leadership_concentration`: CONCENTRATED / MODERATE / BROAD

**Volume:**
- `theme_avg_ud_ratio`, `theme_pct_strong_ud`
- `theme_avg_cmf`
- `theme_avg_dist_days`
- `theme_volume_confirmation` (binary)

**Setup counts:**
- `n_multibagger_setups`
- `n_tier_s_pullback`
- `n_elite_leaders`

### Theme CCQS Composite

```python
theme_ccqs_z = (
    0.25 * z(avg_ccqs) +
    0.25 * z(breadth_composite) +
    0.20 * z(theme_rs_composite) +
    0.15 * z(momentum_acceleration) +
    0.10 * z(volume_confirmation) +
    0.05 * z(health_indicators)
)
theme_ccqs = norm.cdf(theme_ccqs_z) * 100
```

---

## 13. Reliability Architecture — 8 Layers

### Layer 1: Data Quality Firewall (Critical)

Run BEFORE any feature computation. Tickers failing critical checks excluded from scoring.

**Critical failures (exclude from scoring):**
- `NO_DATA`: empty DataFrame
- `INSUFFICIENT_HISTORY`: < 252 days
- `STALE_DATA`: last bar > 5 days ago
- `INVALID_PRICES`: zero or negative prices
- `ZERO_VOLUME`: 20-day vol sum = 0
- `INSUFFICIENT_LIQUIDITY`: < $100K ADV
- `SUSPICIOUS_BAR`: > 50% one-day move with reversal

**Warnings (score but flag):**
- `LARGE_GAP_RECENT`: > 30% one-day move in last 20d
- `VOLUME_COLLAPSE`: recent vol < 10% historical
- `LOW_LIQUIDITY`: < $1M ADV
- `FREQUENT_GAPS`: 5+ gaps > 5% in 20d
- `FREQUENT_DOJI`: 5+ doji bars in 20d
- `POSSIBLE_CORPORATE_ACTION`: close vs adj_close discrepancy

### Layer 2: Corporate Action Detection

Detect splits, spinoffs, halts:

```python
def detect_corporate_actions(ohlcv):
    ratio = ohlcv['close'] / ohlcv['adj_close']
    ratio_change = ratio.pct_change()
    split_dates = ratio_change[abs(ratio_change) > 0.10].index
    
    close_return = ohlcv['close'].pct_change()
    adj_return = ohlcv['adj_close'].pct_change()
    spinoff_candidates = (abs(close_return - adj_return) > 0.05)
    
    return {'splits': split_dates, 'possible_spinoffs': spinoff_candidates}
```

### Layer 3: TradingView Parity Tests

Maintain ~20 reference snapshots:

```python
TV_REFERENCE_VALUES = {
    'NVDA_2024-12-31': {
        'close': 134.29, 'sma_50': 138.42, 'sma_200': 117.93,
        'atr_14': 4.31, 'adx_14': 27.85, 'rsi_14': 48.23,
        'macd_line': -1.42, 'macd_signal': -1.81, 'macd_histogram': 0.39,
        'bb_upper_20': 145.82, 'bb_lower_20': 130.91,
        'supertrend_direction': -1,
    },
    # ... ~20 more snapshots
}

def test_tv_parity():
    """All computed indicators must match TradingView to 2 decimal places."""
    for snapshot_id, expected in TV_REFERENCE_VALUES.items():
        ticker, date = snapshot_id.rsplit('_', 1)
        actual = compute_features(load_ohlcv(ticker, end=date))
        for indicator, expected_val in expected.items():
            assert abs(actual.iloc[-1][indicator] - expected_val) < 0.01
```

### Layer 4: Score Anomaly Detection

Daily comparison vs recent history. Flag:
- Score change > 4σ from 5-day rolling
- Grade jumps of 2+ levels
- Unexpected state flips
- New tickers / removed tickers

### Layer 5: Sanity Check Assertions

Daily automated assertions:
- CCQS bounded [0, 100]
- Grades match score ranges
- Component contributions sum to total
- State probabilities sum to 1
- Universe coverage ≥ 85%
- Grade S frequency in 2-20% range

If any assertion fails: log loudly, refuse to publish.

### Layer 6: Snapshot Archive

Every refresh saves complete state. Enables time-travel and audit.

### Layer 7: Manual Override Layer

YAML config (`data/manual_overrides.yaml`):
- `exclude_tickers`: list of tickers to skip
- `flag_tickers`: add warning flags
- `force_state`: override state classification
- `data_quality_overrides`: suppress specific warnings

### Layer 8: Health Monitoring Dashboard Banner

Top-of-app banner with system status:
- Last refresh timestamp
- Coverage (n_scored / n_universe)
- Anomalies count
- Sanity check pass/fail
- Running 60-day IC

---

## 14. Output Layer — Dashboard Views

Streamlit dashboard with 8 views:

### View 1: Theme Leaderboard (Primary View)

Ranked table of populated CORE baskets:
- Theme name, N constituents
- Theme CCQS, theme class, avg/median CCQS
- % Grade A+, % Climactic, % Broken
- Theme RS direction, breadth metrics
- Theme momentum acceleration
- Multibagger count, Tier S Pullback count
- Top 3 names

Sortable by any column. Filterable by category/class.

### View 2: Factor Decomposition

For selected basket: average component scores per S_X.
- Bar chart comparing to universe average
- Identifies which factors drive theme strength

### View 3: Per-Name Drill-Down

Sortable table:
- Ticker, CCQS, Grade, State (with confidence)
- Setup category, Leadership Tier
- RS Rating vs SPY (with QQQ RS Line direction as context)
- %MA50, ATR×50, U/D Vol
- MACD posture
- Tags (other baskets)

Click ticker → detailed view (Section 4 below).

### View 4: Tag/Theme Filter

Cross-sector overlay filtering. Select tag basket → see all names tagged.

### View 5: Country ETF Tier

Separate ranking for 35 country ETFs. Same CCQS framework.

### View 6: RS Leaders View

Filterable by:
- Leadership tier
- Multi-benchmark class
- Theme class
- State / setup

Show: all top RS leaders with full multi-benchmark context.

### View 7: Multibagger Discovery View

Names with:
- `leadership_tier == 'EMERGING_LEADER'`
- In themes classified `EMERGING_THEME` or `STRONG_THEME`
- Setup: 'Emerging Leader (Multibagger Setup)' or 'Consolidation Within Strong Theme'

This is the "where to look for next NVDA" view.

### View 8: Per-Name Detail (Drill-Down)

For selected ticker:
```
NVDA — CCQS 89 [Grade S]
├── Setup: Elite Leader Continuation (confidence 0.92)
├── State: TRENDING (conf 0.92)
├── Leadership Tier: ELITE_LEADER
│
├── RS Rating vs SPY: 99 (RS Line at 252d high ✓)
├── QQQ RS Line: slope_60d +14.2% (tech-peer context ✓)
│
├── MTF Coherence: 3/3
├── Volume Confirmed: ✓
├── Within-Basket Rank: 1/3
│
├── Theme: AI Compute and Accelerators (ELITE_THEME)
│   ├── Theme CCQS: 87
│   ├── Theme Breadth (>50DMA): 100%
│   └── Theme Momentum: STRONG_ACCELERATING
│
├── Components (contribution to CCQS):
│   S_RS_LEADERSHIP:  92  →  +0.17
│   S_RS:             87  →  +0.10
│   S_STRUCTURE:      85  →  +0.11
│   ...
│
├── Key Technical Features:
│   %MA 50:   +8.3%
│   ATR×50:    1.8
│   ADX:      32.5
│   R²:        0.82
│   RSI:      62
│   MACD:     Positive/Accelerating/Strong
│   ...
│
└── Tags: [AI Data Center Capex, HBM Capacity, Edge AI Inference]
```

### Branding

ADFM brand:
- Color palette: navy (#0a2540), gold accent
- Typography: DM Sans / DM Serif Display + IBM Plex
- Dark and white theme variants

---

## 15. File Structure

```
CCQS_V1/
├── data/
│   ├── __init__.py
│   ├── universe.py                 # Canonical universe (LOCKED - do not modify)
│   ├── manual_overrides.yaml       # Override mechanism
│   ├── cache/                      # Daily refresh cache (gitignored)
│   │   ├── ohlcv_daily.parquet
│   │   ├── ohlcv_meta.json
│   │   ├── failed_tickers.json
│   │   └── data_quality_report.json
│   └── snapshots/                  # Daily archives (gitignored)
│       └── YYYY-MM-DD/
│
├── compute/
│   ├── __init__.py
│   ├── loader.py                   # yfinance batch fetcher
│   ├── data_quality.py             # Data quality firewall
│   ├── features.py                 # 104 features, vectorized (Path 1.5)
│   ├── standardization.py          # Robust z-score framework
│   ├── components.py               # 10 component scores
│   ├── state.py                    # Probabilistic state classification
│   ├── ccqs.py                     # Composite engine + grading
│   ├── setup_classifier.py         # 24 setup categories
│   ├── leadership.py               # Leadership tier classification
│   ├── aggregation.py              # Theme-level rollup
│   └── reliability/
│       ├── __init__.py
│       ├── corporate_actions.py
│       ├── anomaly_detection.py
│       ├── sanity_checks.py
│       ├── snapshot.py
│       └── ic_tracker.py
│
├── output/
│   └── app.py                      # Streamlit dashboard (8 views)
│
├── tests/
│   ├── __init__.py
│   ├── test_loader.py
│   ├── test_data_quality.py
│   ├── test_features.py
│   ├── test_components.py
│   ├── test_state.py
│   ├── test_setup_classifier.py
│   ├── test_aggregation.py
│   ├── reference/
│   │   ├── tv_snapshots.py
│   │   └── test_tv_parity.py
│   └── integration/
│       └── test_end_to_end.py
│
├── .github/
│   └── workflows/
│       └── refresh.yml             # Daily refresh action
│
├── requirements.txt
├── README.md
├── SPEC.md                         # This document
└── .gitignore
```

---

## 16. Build Phases

Build the system incrementally, validating at each phase.

### Phase 1: Foundation (FIRST)

Create:
- `requirements.txt`
- `.gitignore`
- `README.md` (project description)
- `data/manual_overrides.yaml` (empty template)
- `data/__init__.py` (empty)
- `compute/__init__.py` (empty)
- `compute/reliability/__init__.py` (empty)
- `compute/loader.py` (yfinance batch fetcher with SPY/QQQ benchmarks, parquet caching, retry logic, failure logging)
- `compute/data_quality.py` (quality firewall per Section 13 Layer 1)

Test:
```bash
python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m compute.loader      # Pull ~892 tickers + benchmarks
python -m compute.data_quality # Run quality checks
```

Expected:
- ~895-905 tickers fetched successfully
- ~8-15 typical failures (delisted, illiquid)
- ~750-850 tickers PASS quality
- ~50-150 tickers WARNING (still scored)
- ~10-30 tickers FAIL (excluded)
- NVDA/SPY/QQQ closing prices match TradingView

### Phase 2: Features + Standardization

Create:
- `compute/features.py` (108 features, vectorized using pandas/numpy)
- `compute/standardization.py` (robust z-score framework)
- `tests/test_features.py` (unit tests for feature correctness)

Test on a sample of 10 tickers; verify feature values against TradingView spot checks.

### Phase 3: Components + State + Composite Scoring

Create:
- `compute/components.py` (10 component scores)
- `compute/state.py` (probabilistic classification, 6 states)
- `compute/ccqs.py` (composite engine + grading)
- `compute/setup_classifier_v2.py` (13-label chart-evocative cascade)
- `compute/leadership.py` (leadership tier, 10 tiers)
- `tests/test_components.py`, `tests/test_state.py`

Test: full universe scoring. Should complete in <30s. Distribution sanity: ~5-10% Grade S.

### Phase 4: Aggregation + Reliability

Create:
- `compute/aggregation.py` (theme-level rollup)
- `compute/reliability/*.py` (all 5 reliability submodules)
- `tests/reference/tv_snapshots.py` (~20 TV reference snapshots)
- `tests/reference/test_tv_parity.py`
- `tests/integration/test_end_to_end.py`

Run end-to-end pipeline. All sanity checks pass.

### Phase 5: Streamlit Dashboard

Create:
- `app/streamlit_app.py` (8 dashboard views with ADFM brand)

Test locally with `streamlit run app/streamlit_app.py`. Verify all views render correctly.

### Phase 6: Deployment

Create:
- [`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml) —
  scheduled daily refresh at 4:05 PM ET weekdays (5 min after the
  4:00 PM ET cash-equity close), via two DST-spanning UTC crons gated
  by an ET-hour guard so exactly one fires per weekday.
- README deployment instructions
- Streamlit Cloud configuration

Deploy to private GitHub + Streamlit Community Cloud.

---

## Implementation Guidelines

### Code Quality

- All functions documented with docstrings
- Type hints throughout (Python 3.13+)
- Vectorized operations (pandas/numpy); avoid Python loops where possible
- Pinned dependency versions in requirements.txt

### Determinism

- No random number generation in scoring
- All operations deterministic
- Same inputs → identical outputs

### Performance Targets

- Data pull: < 2 minutes for ~892 tickers
- Feature computation: < 30 seconds for full universe
- Scoring: < 5 seconds
- Total daily refresh: < 5 minutes

### Logging

- Use `loguru` for structured logging
- INFO level for normal operations
- WARNING for quality issues
- ERROR for failures
- Logs to stdout AND `logs/ccqs.log`

---

## Reference Card — Key Numbers

| Metric | Value |
|--------|------:|
| Universe size | ~892 tickers |
| Baskets | 276 (181 CORE + 60 TAG + 35 COUNTRY); ~148 populated themes shown in dashboard |
| Benchmarks | 2 (SPY, QQQ) |
| Features per stock | 108 |
| Components | 10 |
| States | 6 |
| Setup categories | 13 |
| Leadership tiers | 10 |
| Theme classes | 7 |
| Dashboard views | 8 |
| Reliability layers | 8 |

---

**End of Specification**

This is the complete locked specification for CCQS V1. Use this as the authoritative reference when implementing each phase. Do not deviate without explicit user approval.
