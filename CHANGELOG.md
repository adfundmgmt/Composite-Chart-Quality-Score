# CCQS V1 — Changelog

Phase-by-phase implementation history. Companion to `SPEC.md` (authoritative methodology document) and `USER_GUIDE.md` (user-facing interpretation manual).

## Phase 32 — "Focus 25" model watchlist (2026-06-03) — DISPLAY-LAYER ONLY

Implements the Phase 31 validated configuration (P2: top-25 by CCQS, 4-week
rebalance, equal-weight) as a dashboard watchlist + exportable artifact.
**No methodology change** — consumes existing pipeline outputs only. CCQS,
components, STATE_WEIGHTS, classifiers, regime logic all untouched.

### What shipped
- `compute/focus25.py` — frozen-membership builder. Selects top-25 by CCQS on
  the latest pipeline date; refreshes every 20 trading days (4 weeks);
  membership frozen between refreshes (daily values update, membership does
  not). Writes `focus25_current.parquet`, appends `focus25_history.parquet`
  (live track record), writes `focus25_meta.json`.
- Wired into `compute/build_dashboard_cache.py` (after regime context;
  wrapped in try/except so it can never break the cache commit).
- `app/utils/data_loader.py` — `load_focus25()`, `load_focus25_history()`.
- `app/streamlit_app.py` — "Focus 25" section (Section 1.5): refresh/freeze
  status, basket-concentration block with amber chip >8 names, adds/drops on
  refresh, per-name table (rank, ticker, CCQS, grade, tier, state, setup, B→A
  flag, basket, % from 52w high, ADR%), and the required guardrail caption.

### Selection rule (fixed)
Pure top-25 by score — no B→A filter, no setup filter, no manual overrides
(Phase 31 P9/P10 precedent: overlays-as-hard-filters degrade results). No
caps, no quotas. Equal-weight reference (4% each); score-weighting (Phase 31
P10) and inverse-vol (Phase 33) were tested and rejected.

### B→A flag (annotation only)
Definition: weekly CCQS grade landing on A from B within **28 calendar days**
(4 calendar weeks) of the latest pipeline date. Calendar window (not weekly-
snapshot count) so a transition ~4 weeks old is still flagged. Validated
spot-check on 2026-06-03 data: flagged set within top-25 = {ACMR, BLDP, CORZ,
CRWD, ILMN, TECK} — exactly the 6 expected names (6/6).

  NOTE on the window: the initial snapshot-count implementation (`iloc[-4:]`,
  4 weekly rows) flagged only CRWD + ILMN, because the BLDP/ACMR/TECK/CORZ
  B→A landings (2026-05-08) are the 5th weekly row back — yet only 26 days
  before 06-03, i.e. within 4 *calendar* weeks. Switching to a 28-day calendar
  window reproduced all 6. This was caught by the pre-registered validation
  gate, investigated, and resolved before deploy (not a bug — a window-
  definition match).

### Basket concentration
Counts per primary basket shown above the table; amber chip when any single
basket > 8 names. Today: top basket = Memory and Storage (4) — no amber.
Concentration vector stored in history each refresh. Display-layer only;
selection rule stays pure top-25 (no theme caps).

### Validation (all PASS before deploy)
- 91/91 pytest (incl. 11/11 pipeline sanity)
- 140/140 TradingView reference parity — no scored field changed
- B→A spot-check 6/6 expected names
- Frozen-membership behavior: 2nd same-day build kept identical members, did
  not duplicate the history row, flipped is_refresh_today→False
- All scored values (CCQS/components/state/tier/setup) bit-identical pre/post
  (display-only addition)

## Phase 30.1–30.4 — Aggregation + display-layer follow-ups (2026-05-29)

Four sub-phases shipped after Phase 30 reorganized the universe. Each
addressed a pocket of code that still assumed PRIMARY-only basket
membership and broke the new "Magnificent Seven" cohort UX.

### Phase 30.1 — Aggregation source switched to all tagged members (`854cead`)
**Problem.** After Phase 30, Mag7 did not appear in the Themes view.
**Cause.** `compute/aggregation.py:_basket_membership_long` built the
membership table from `PRIMARY_BASKET_CONSTITUENTS` (primary-only) and
filtered baskets with fewer than 3 PRIMARY members. Mag7 has 1
(AAPL) → excluded. Same logic also hid ~41 TAG baskets.
**Fix.** Source switched to `CATEGORIES` (primary + tag members). >=3
total-member threshold preserved for statistical reliability.
**Effect.** `theme_aggregates.parquet`: 148 → 241 baskets (+93 newly
visible thematic baskets including AI Data Center Capex, AI Power
Demand, Quantum Computing, Sovereign AI Infrastructure, Humanoid
Robotics, Autonomous Vehicles and Robotaxis, etc.). Mag7 row populates
with n_constituents=7, avg_ccqs=63.21.
**Test update.** `tests/test_metric_integrity.py:test_theme_pct_above_50dma_correct`
recompute switched from PRIMARY_BASKETS-only to `tickers_tagged()` to
mirror the new aggregation source. Without this, the recompute
membership and the cached aggregate membership would diverge by ~93
baskets and produce false-positive violations.

### Phase 30.2 — Themes view top_member / members columns (`cd80260`)
**Problem.** Mag7 row appeared in the Themes view but with em-dash
("—") in Top Member and Members columns.
**Cause.** `app/utils/data_loader.py:load_themes_data` used
`_basket_map()` (PRIMARY-only). For Mag7, only AAPL maps to it; the
group held one row and apparently did not materialize through the
Streamlit cache.
**Fix.** New helper `_all_membership_long()` builds a long
(ticker, basket) DataFrame from CATEGORIES. CCQS values merged
against it before groupby — Mag7 group now holds all 7 mega-caps.
**Effect.** Top Member = GOOGL (highest CCQS in cohort, 86.83);
Members = "GOOGL, AAPL, AMZN, NVDA, TSLA, MSFT, META". ~40 other TAG
baskets surfaced similarly.

### Phase 30.3 — Stock Detail "Basket Peers" panel (`9e870ff`)
**Problem.** AAPL's Basket Peers section rendered just AAPL alone.
**Cause.** `app/streamlit_app.py:354` filtered the per-ticker
DataFrame by `df["basket"] == "Magnificent Seven"`, but the "basket"
column there stores each ticker's PRIMARY. Only AAPL's primary is
Mag7, so the peer set was one row — AAPL itself.
**Fix.** Resolve peer set via `tickers_tagged(basket)`, pulling all
basket members (primary + tag). Sort by CCQS desc, top 10.
**Effect.** AAPL Basket Peers now shows the full 7-name Mag7 cohort.
Verified no regression on NVDA (basket = AI Compute, all members
already primary) and MSFT (basket = Hyperscalers, all 5 already
primary).

### Phase 30.4 — Basket Peers panel: Theme column reflects viewed basket (`63cd80f`)
**Problem.** User screenshot: AAPL's Basket Peers listed all 7 Mag7
names but the Theme column showed each row ticker's PRIMARY
(Hyperscalers for the 4 megacaps, AI Compute for NVDA, EV for TSLA).
Visually scrambled even though all 7 are genuine Mag7 peers.
**Fix.** Override `peers["basket"] = basket` before rendering — every
row in this panel is by definition a peer in the viewed basket, so
the Theme column should reflect that, not each row's own primary.
**Effect.** AAPL's panel now shows "Magnificent Seven" cleanly in
every Theme cell. NVDA / MSFT panels unchanged (those baskets'
members already had matching primaries pre-fix).

### Validation (all four sub-phases combined)
- ✓ 91/91 pytest passed
- ✓ 140/140 TV reference parity passed (all canaries within tolerance)
- ✓ Universe consistency: AAPL primary = Mag7; Hyperscalers no AAPL;
  6 other Mag7 names tagged
- ✓ theme_aggregates: 241 baskets (~93 newly visible)
- ✓ Mag7 row: 7 constituents, all valid CCQS, avg 63.21
- ✓ Streamlit Cache TTL refreshes every 30 min; pushes also auto-
  redeploy the Streamlit Cloud app within ~3 min

## Phase 30 — Magnificent Seven basket added; AAPL moved out of Hyperscalers (2026-05-29)

User-driven universe reorganization. A new CORE basket "Magnificent Seven"
is added under the "Technology, AI and Internet" category, containing all
7 mega-cap leaders (AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA).

### Universe changes

**`data/universe.py`:**
- `CATEGORIES["Technology, AI and Internet"]["Hyperscalers"]`: removed `'AAPL'` (now 5 members: MSFT, AMZN, GOOGL, META, ORCL)
- `CATEGORIES["Technology, AI and Internet"]["Magnificent Seven"]`: NEW basket with 7 members
- `BASKET_PRIORITY["Magnificent Seven"] = 13` (positioned next to Hyperscalers in the priority stack; immaterial for dedup since AAPL is hard-set via PRIMARY_BASKETS)
- `MANUAL_OVERRIDES["AAPL"]`: `'Hyperscalers'` → `'Magnificent Seven'`
- `PRIMARY_BASKETS["AAPL"]`: `'Hyperscalers'` → `'Magnificent Seven'`
- `PRIMARY_BASKET_CONSTITUENTS["Hyperscalers"]`: removed `'AAPL'`
- `PRIMARY_BASKET_CONSTITUENTS["Magnificent Seven"]`: NEW, `['AAPL']`
- `TAGS[t]` for `t in {MSFT, AMZN, GOOGL, META, NVDA, TSLA}`: appended `'Magnificent Seven'`
- Module-docstring stats: 275 → 276 baskets, 180 → 181 CORE

The 6 non-AAPL Mag7 members keep their existing primary baskets
(Hyperscalers for MSFT/AMZN/GOOGL/META, AI Compute and Accelerators for
NVDA, Electric Vehicles for TSLA). Magnificent Seven appears as a TAG
overlay on those names — additive, no methodology disruption to their
within-basket comparisons.

### Methodological consequence — AAPL within-basket features

AAPL is the sole primary constituent of the new Magnificent Seven basket.
Per `compute/features.py:_within_basket_z` (requires `len(members) >= 3`
to compute) and `_within_basket_rank` (requires `>= 2`), AAPL now emits
NaN for:
- `within_basket_z_21d`
- `within_basket_z_63d`
- `within_basket_rank`
- `within_basket_rank_pct`

These were previously computed against the 6-member Hyperscalers cohort.
The 10-component CCQS panel does not depend on these particular features
(they live deeper in feature space and feed `s_rs_leadership` via other
paths), so AAPL's CCQS remains computable with `weight_present = 1.0` and
all 10 components valid.

### Cache + pipeline refresh

Full pipeline re-run on 2026-05-28 OHLCV with the new universe:
- `compute.features`: 55.6s, 108 features × 1,548,000 rows
- `compute.standardization`: per-date robust z-scores
- `compute.pipeline`: components / state / leadership / CCQS / setups
- `compute.build_dashboard_cache`: slimmed parquets to ~25.5 MB

### Universe-drift effect on canaries (expected, within tolerance)

Cross-sectional ranks (RS rating, CCQS percentile) shift slightly any time
the universe changes — same effect as Phases 23 / 14R / 5.2. All 10 TV
parity canaries pass the existing tolerance band (CCQS ±5, RS ±5):

| Canary | CCQS pre | CCQS post | Δ |
|---|---:|---:|---:|
| NVDA | 74.85 | 74.31 | −0.54 |
| MSFT | 25.65 | 25.13 | −0.52 |
| META | 15.51 | 15.80 | +0.29 |
| GOOGL | 88.54 | 87.90 | −0.64 |
| TSLA | 63.88 | 65.60 | +1.72 |
| AMZN | 84.49 | 85.67 | +1.18 |
| JPM | 45.50 | 45.11 | −0.39 |
| TSM | 86.79 | 87.60 | +0.81 |
| LLY | 71.73 | 71.18 | −0.55 |
| UNH | 82.47 | 81.96 | −0.51 |

All categorical fields (grade, state, leadership_tier, setup) bit-identical.

### Validation

- ✓ 91/91 pytest passed
- ✓ 140/140 TV reference parity passed (all 10 canaries × 14 fields)
- ✓ 11/11 pipeline sanity checks PASS
- ✓ Universe consistency: AAPL primary = Magnificent Seven; Hyperscalers
  no longer contains AAPL; 6 other Mag7 names have Mag7 in their tag list

### AAPL post-refresh snapshot (2026-05-28)

| Field | Value |
|---|---|
| CCQS | 84.76 (grade A) |
| State | TRENDING (conf 0.788) |
| Leadership tier | STRONG_PERFORMER (display "Steady") |
| Setup | Tight Base |
| is_basket_leader | False (1-member basket; trivially the only member) |
| Primary basket | Magnificent Seven |
| Tags | [] |


**Path C overall status:** COMPLETE as of 2026-05-26 (commit `e3a9ada` + Phase 12 closeout documentation).

Status legend:
- ✓ SHIPPED — implementation deployed to production
- ✗ REJECTED — investigated, did not meet criteria
- ↻ DEFERRED — documented for future consideration

---

## Path C — Phase-by-phase summary

### Phase 5.2 — NaN-CCQS root-cause fix + universe cleanup (2026-05-23) ✓ SHIPPED

Initial commit `ed4bf42`. Root-caused why CCQS was NaN for many tickers; cleaned up universe to ensure all ticked-as-scoreable rows produce a finite score. See `SPEC.md` §Phase 5.2.

### Phase 5.3 — Selective SP100 promotion (2026-05-23) ✓ SHIPPED

`ed4bf42`. Promoted high-quality SP100 names back into scoring universe after Phase 5.2 cleanup. See `SPEC.md` §Phase 5.3.

### Phase 5.5 — Naming standardization (2026-05-24) ✓ SHIPPED

Commit `01a887a`. Comprehensive vocabulary audit for institutional presentation. Renamed setups/states for clarity; ensured terminology was internally consistent. See `SPEC.md` §Phase 5.5.

### Phase 5.6 — Coil follow-up (2026-05-24) ✓ SHIPPED

Commits `ad51fdc`, `3442846`. Renamed remaining "Coil" setup labels for vocabulary consistency. See `SPEC.md` §Phase 5.6.

### Phase 5.7 — Climax / Broken sub-setup rename (2026-05-25) ✓ SHIPPED

Commit `871eb75`. Renamed climax/broken sub-setups to align with state-vocabulary parity. See `SPEC.md` §Phase 5.7.

### Phase 5.8 — Setup label accuracy audit (2026-05-25) ✓ SHIPPED

Commit `c8ff584` (combined with Phase 6). Audited 29 setup labels against actual detection logic; renamed where labels overclaimed. See `SPEC.md` §Phase 5.8.

### Phase 6 — Foundation fixes (2026-05-25) ✓ SHIPPED

Commit `c8ff584`. Two foundational changes:
- Per-date winsorization in `compute/ccqs.py` (1st/99th percentile clipping per date)
- `s_climax` removal (carried zero weight since X.2.1; component dimension 10 → 9)

See `SPEC.md` §Phase 6 + §Known caveats.

### Priority 2 — Empirical validation of current methodology (2026-05-25) ✓ DOCUMENTED

Documentation work in commit `c8ff584`. Three sub-tasks:
- **2a**: Bootstrap CIs on STATE_WEIGHTS (54 cells × 4 horizons; ~7.5M paired t-tests)
- **2b**: Conditional IC analysis across regimes (mega-cap, defensive sector, market vol, EXHAUSTION, 2020 COVID)
- **2c**: Synthesis into SPEC

Key finding: 6/24 s_demand cells carried significant NEGATIVE OOS IC — motivated Phase 7.

See `SPEC.md` §Priority 2.

### Phase 7 — Priority 3a: `s_demand` removal + carrier redistribution (2026-05-25) ✓ SHIPPED

Commit `619ba4e`. Zeroed `s_demand` weight in STATE_WEIGHTS; redistributed 10-15% per state to the four positive-OOS carriers (s_rs, s_rs_leadership, s_structure, s_mtf).

**Empirical evidence:** Walk-forward 126d t-stat 1.82 → 2.02 (clears institutional 2.0 threshold).

See `SPEC.md` §Phase 7.

### Priority 3b/3c — Simplification investigations (2026-05-25) ✗ REJECTED

Investigated 4-carrier-only composite (3b) and state-aware hybrid (3c). Both regressed EXHAUSTION-state IC catastrophically:
- 3b: EXHAUSTION 60d/126d down −48%/−27%
- 3c: EXHAUSTION fragility persists due to cross-state Bayesian averaging

**Architectural finding:** Confidence-blending toward INDETERMINATE means EXHAUSTION-state stocks pull 45% of their CCQS from the INDETERMINATE weight column. Further per-state simplification requires relaxing confidence-blending — a material redesign.

See `SPEC.md` §Priority 3.

### Priority 3d — Conditional performance warnings, display layer only (2026-05-25) ✓ SHIPPED

Commit `37646b0`. Added reliability flags surfacing Priority 2b findings as dashboard chips (Mega-cap, Defensive sector, High market vol regime, EXHAUSTION 20d caveat). Display-layer only — CCQS values unchanged.

See `SPEC.md` §Priority 3d.

### Phase 8a — Residual momentum addition (2026-05-26) ✓ SHIPPED

Commit `5bc8eb5`. Added `s_residual_momentum` as the 10th component at ~5% per state. Beta-adjusted idiosyncratic momentum: rolling 252d OLS beta vs SPY, daily residuals summed over 126d.

**Empirical evidence:**
- Standalone IC at 126d-fwd: +0.0466 (t=14.4)
- Orthogonal-to-s_rs IC at 126d: +0.0246 (t=+8.63)
- Walk-forward paired t at 60d: 2.05; at 126d: 2.72
- 23 of 24 (state × horizon) cells improve

Empirical basis: Blitz–Huij–Martens (2011), Robeco production usage.

See `SPEC.md` §Phase 8a.

### Phase 8a.1 — Short-horizon recovery investigation (2026-05-26) ✗ REJECTED

Hypothesis: a new `s_short_term_reversal` component could recover the 5d/20d t-stat erosion from Phase 8a without giving back 60d/126d gains.

**Decision criteria scorecard (4 fails, 2 passes):**
- Walk-forward paired t at any horizon: not significant
- EXHAUSTION regressed catastrophically (5d −0.013, 20d −0.017, 60d −0.002, 126d −0.012)

The Priority-3c architectural fragility re-emerged. No code changes.

See `SPEC.md` §Phase 8a.1.

### Phase 8b — Vol-adjustment standardization investigation (2026-05-26) ✗ REJECTED

Four configurations tested with stricter criteria than Phase 8a (CI-includes-zero counts as failure; walk-forward paired t > +1.96 required at 60d or 126d):
- Config B (Sharpe residual momentum): no-op
- Config C (Sharpe rank for momentum_21d): no-op
- Config D (raw 126d return rank): **−1.01 walk-forward paired t at 126d; EXHAUSTION 126d -0.0201**
- Config E (B+C+D combined): inherits D's regressions

Zero configurations pass all five strict criteria. No code changes.

See `SPEC.md` §Phase 8b.

### Phase 10 — Volume-pattern addition (Config W1, 2026-05-26) ✓ SHIPPED

Commit `0c61191`. Added `s_volume` (bundled `low_rel_vol_10d` + `volume_buzz_50`) as 11th component at 3% per state. Existing 10 components scaled by 0.97.

**Empirical evidence (first config in 3 investigations to clear strict criteria):**
- 5d per-date IC delta CI strict > 0 at [+0.000012, +0.000686]
- 5d walk-forward paired t = **+2.01** (clears +1.96 threshold)
- 5d t-stat 2.33 → 2.41; 20d 1.95 → **2.04** (crosses institutional 2.0)
- 60d/126d preserved (NS)
- EXHAUSTION-state IC **+0.006 to +0.016** across every horizon
- Regime-stable (HIGH/MED/LOW all positive at 5d/20d)

**Architectural insight:** Refutes Phase 8b "empirical optimum" conclusion. New orthogonal information additions succeed where weight redistributions fail. EXHAUSTION fragility was a constraint on RS-family redistribution, NOT on the architecture itself.

**Bundled feature requirement (W6 lesson):** Investigation showed `low_rel_vol_10d` alone HURTS CCQS at every horizon (paired t −1.20 to −1.95). Only blended with `volume_buzz_50` is the composite net-positive. Cannot unbundle.

See `SPEC.md` §Phase 10.

### Phase 11A — State Classification Validation (2026-05-26) ✓ DOCUMENTED

Combined with Phase 11.B.1 commit `4951a0c` for documentation. No code changes — investigation only.

**Key findings:**
- 6 states empirically validated; every state statistically distinguishable from every other at every horizon
- **State machine is a CONTEXT classifier, NOT a buy/sell signal.** TRENDING stocks UNDERPERFORM universe (−1.0% at 60d); EXHAUSTION stocks OUTPERFORM (+4.1%)
- State persistence: 72.3% local stability (appropriate)
- All transitions physically sensible; no impossible cells
- Confidence-blending mechanism working as designed
- Threshold sensitivity: most params mid-slope; PULLBACK `mu_rsi_14 = 45.0` most sensitive (deferred for tuning)

See `SPEC.md` §Phase 11A.

### Phase 11.B.1 — Dead setup removal (2026-05-26) ✓ SHIPPED

Commit `4951a0c`. Removed `"Consolidation Within Strong Theme"` from SETUP_LABELS and cascade. Never fired (n=0 in 1.53M rows) — required `theme_strong` flag that was hardcoded False.

SETUP_LABELS: 29 → 28. No CCQS change (setup labels don't feed CCQS).

See `SPEC.md` §Phase 11B + §Phase 11.B.1 patch.

### Phase 11B — Setup Classification Validation (2026-05-26) ✓ DOCUMENTED

Commit `4951a0c` (combined with 11.B.1). No code changes — investigation only.

**Key findings:**
- "**Premium label, no alpha**" pattern: VCP Setup, Emerging Leader, Premium Pullback, Theme Leader Pullback all UNDERPERFORM universe at 60d
- "Weakness-branded" setups (Capitulation Selling, Distribution Pattern, Sustained Weakness, Volume-Confirmed Exhaustion) OUTPERFORM by 4–12pp
- 34 of 325 pairwise comparisons are statistically equivalent (p > 0.05)
- VCP Setup ≡ Emerging Leader (p=0.94) — flagged for Phase 11E.1 merger
- Priority cascade empirically validated (cascade-assigned rows outperform masked for high-priority setups)

See `SPEC.md` §Phase 11B.

### Phase 11C — Leadership Tier Validation (2026-05-26) ✓ DOCUMENTED

Combined with Phase 11.C.1 commit `b2fe003` for documentation. No code changes — investigation only.

**Key findings:**
- Only ELITE_LEADER has a truly distinctive forward edge (+15.24% at 60d, 3× universe)
- All other 8 tiers cluster within ±2.5pp of universe
- Non-monotonic ordering: 4 of 8 adjacent tier pairs have "lower" tier OUTPERFORMING "higher"
- EMERGING_LEADER UNDERPERFORMS universe (premium-label pattern again)
- WEAK_LAGGARD outperforms most upper tiers (mean reversion)
- Tier × State interaction is high-value (ELITE × INDETERMINATE = +18.10%)

**Anomaly discovered:** NEUTRAL has rs_p10=10.97 vs formal definition [45, 60). Default-init bug.

See `SPEC.md` §Phase 11C.

### Phase 11.C.1 — NEUTRAL fall-through fix (2026-05-26) ✓ SHIPPED

Commit `b2fe003`. Added explicit `UNCLASSIFIED` 10th tier. Default initialization in `compute/leadership.py` changed from `"NEUTRAL"` to `"UNCLASSIFIED"`.

**Bug fixed:** ~132,050 rows (8.6% of universe = 42.7% of NEUTRAL pre-patch) had been mis-labeled as NEUTRAL because they fell through the cascade. Three patterns:
1. rs_spy < 25 AND rs_slope ≥ 0 (80,675 rows)
2. rs_spy ∈ [40, 45) AND rs_slope < −5 (28,119 rows)
3. rs_spy < 45 AND rs_slope is NaN (23,256 rows)

**Population shift:** NEUTRAL 21.83% → 12.59%; UNCLASSIFIED 0 → 8.63%. No CCQS impact (leadership tier doesn't feed CCQS).

See `SPEC.md` §Phase 11C / §Phase 11.C.1 patch.

### Phase 11D — Cross-Layer Synthesis (2026-05-26) ✓ DOCUMENTED

Commit `e3a9ada`. No code changes — synthesis investigation.

**Three first-order findings:**
1. **CCQS is regime-dependent** — works in top tiers (Q10−Q1 spread +5.26% in ESTABLISHED_LEADER), inverts in bottom tiers (WEAK_LAGGARD −9.24%)
2. **Categorical labels carry 97.3% of cross-sectional R²** — CCQS as continuous variable adds 2.7%. Setup is the highest-info layer (60.6%).
3. **State × Setup are 77% redundant (Cramér's V = 0.77)** — by design, structural not bug

**System reframing:** "CCQS V1 is a categorical screening + within-category ranking tool."

See `SPEC.md` §Phase 11D + §Path C — Comprehensive Overview.

### Phase 11E.1 — Emerging Leader setup merger (2026-05-26) ✓ SHIPPED

Commit `e3a9ada`. Removed `"Emerging Leader"` from SETUP_LABELS and cascade. Statistically equivalent to VCP Setup (p=0.94 per Phase 11B); both underperformed universe at p < 0.001.

SETUP_LABELS: 28 → 27. The 8,999 rows previously labeled "Emerging Leader" absorbed by lower-priority setups (typically Trending Leadership for rs_spy ≥ 80 stocks). VCP Setup retained.

Cascade renumbering: #13-22 → #12-21; catch-alls #23-28 → #22-27.

See `SPEC.md` §Phase 11D §Phase 11E.1 patch.

### Phase 11E.2 — Dashboard CCQS regime chip (2026-05-26) ✓ SHIPPED

Commit `e3a9ada`. Added per-ticker reliability chip in `app/utils/data_loader.py`:
- **Green chip** "High-quality regime — CCQS reliable" for tier ∈ {ELITE_LEADER, STRONG_LEADER, ESTABLISHED_LEADER}
- **Amber chip** "Low-quality regime — CCQS may invert" for tier ∈ {WEAK_LAGGARD, DETERIORATING}
- No chip for middle tiers (no strong regime claim)

`reliability_flags()` signature extended to accept `leadership_tier`. New "ok" severity color (green) added to `app/streamlit_app.py`.

See `SPEC.md` §Phase 11D §Phase 11E.2 patch.

### Phase 12 — Path C closeout documentation (2026-05-26) ✓ THIS COMMIT

Comprehensive closeout work:
1. Live site verification via Chrome MCP (verified Phase 11E.2 chips on STM/AWK/ABT, NVDA/AAL, 10 components, no "Emerging Leader" setup)
2. SPEC.md comprehensive review + Path C — Comprehensive Overview section
3. USER_GUIDE.md created (user-facing interpretation manual)
4. CHANGELOG.md created (this file)
5. TV reference refresh + parity test (140/140 pass)
6. Final commit + push

**Methodology baseline frozen at Phase 11E.2.** Path C complete.

See `SPEC.md` §Path C — Comprehensive Overview.

---

### Phase 13 — Russell 2000 expansion feasibility (2026-05-26) ✓ INVESTIGATION ONLY

User context shift: discretionary L/S manager requested universe
expansion for idea-flow breadth, especially short candidates.
Investigation found 95% yfinance coverage on stratified 188-name R2K
sample, feature distributions within ~10% of S&P 500 medians, and
**1.37-1.49× richer left tail** (deeper drawdowns at 60-126d). Recommendation:
proceed with expansion. Approved for Phase 14.1.

See `SPEC.md` §Phase 13. Full report: `/tmp/PHASE_13_REPORT.md`.

### Phase 14.1 — Universe expansion experiment (2026-05-26) ✗ REVERTED in Phase 14R

Implemented full universe expansion (884 → 1,837 tickers; +953
net-new Russell 1000 + S&P SmallCap 600 names with GICS auto-sector
basket assignment). Pipeline ran end-to-end with 11/11 sanity checks.

**Conditional IC analysis exposed methodology specialization need:**

| Horizon | Original 884 (within new pipeline) | New 953 R1K/SP600 |
|---------|----------------------------------|-------------------|
| 5d | +0.0114 (t=+2.35) ✓ | +0.0011 (t=+0.26) |
| 20d | +0.0087 (t=+1.97) ✓ | **−0.0068 (t=−1.77)** |
| 60d | +0.0133 (t=+3.46) ✓ | **−0.0054 (t=−1.58)** |
| 126d | +0.0292 (t=+9.10) ✓ | +0.0082 (t=+2.80) |

Methodology produces near-zero or NEGATIVE signal on the new small-cap
names while remaining intact for the original universe. Forcing a
single methodology onto two structurally different universes compromises
both.

**Decision (Approach C):** REVERT Phase 14.1. Build separate Small Cap
CCQS tool (Phase 15) with empirically recalibrated methodology.

See `SPEC.md` §Phase 14.1.

### Phase 14R — Reversion to Path C state (2026-05-26) ✓ SHIPPED

Immediate reversion. CCQS restored to bit-identical Phase 12 / Path C
validated state. Universe back to 884 / 851 quality-gated; 9 categories;
22 MB dashboard cache; 140/140 TV parity; 11/11 sanity checks; IC
matches Phase 11 baseline exactly (5d 0.0115; 60d 0.0137; 126d 0.0296).

Files reverted:
- `data/universe.py` — removed Small Mid Cap (Auto-Sectored) category
- `tests/reference/tv_snapshots.py` — restored AMZN pin to Phase 11 baseline

See `SPEC.md` §Phase 14R.

### Phase 14R.H — DST-aware cron fix (2026-05-26) ✓ SHIPPED

CI workflow `.github/workflows/pipeline.yml` updated so the scheduled
pipeline fires at exactly **4:30 PM ET year-round (M-F)**, regardless of
DST. Previously a single cron (`30 21 * * 1-5` UTC) was correct only
during EST (winter); during EDT (summer, current) it fired at 5:30 PM
ET, one hour late.

Implementation: two cron entries (`30 20` for EDT + `30 21` for EST)
plus a TZ-aware `guard` job that checks `TZ=America/New_York date +%H`.
The heavy `refresh` job has `needs: guard` and only runs when the
guard signals `should_run=true` (ET hour == 16). The wrong-DST cron
firing exits in ~10 seconds via the guard. Manual `workflow_dispatch`
bypasses the guard.

Net effect: exactly one full pipeline execution per weekday at
4:30 PM ET, year-round. No DST drift.

### Phase 14R.K — Workflow push race-condition fix (2026-05-26) ✓ SHIPPED

The Phase 14R.H DST-aware workflow ran successfully end-to-end in run #3
(all compute steps green: fetch OHLCV 1m29s → data quality 5s → features
1m20s → standardization 2m3s → pipeline 12m43s → dashboard build 3s)
BUT the final `git push HEAD:main` step failed with:

  ! [rejected] HEAD -> main (fetch first)
  error: failed to push some refs

Root cause: a developer push to main during the workflow's ~17-minute
run shifted HEAD on remote main. The workflow's commit was based on the
remote main at workflow START; by push time, remote main had moved.

Fix: wrap the push in a 3-attempt retry loop with `git fetch origin main`
+ `git pull --rebase origin main` before each push. This absorbs
concurrent commits cleanly. If a developer pushes 3 times during one
workflow run (extremely unlikely), the workflow fails — but that's a
graceful upper bound.

This was the failure mode that caused run #3 to be reported as failed
even though every actual computation step (fetch + compute + tests +
cache build) was completely successful. Pipeline output for 2026-05-26
was correct; only the metadata-update step was rejected.

### Phase 14R.J — Hard-gate test suite for pipeline reliability (2026-05-26) ✓ SHIPPED

Comprehensive test suite added to gate the daily CI pipeline. If ANY
test fails, the dashboard cache is NOT committed back to main — the
prior good cache stays live. This is the "no issues whatsoever" promise.

**New tests** (48 tests total, all passing locally):

1. **`tests/test_universe_coverage.py`** (7 tests) — yfinance fetched all
   universe tickers correctly:
   - Benchmarks SPY/QQQ present
   - ≥ 95% of declared universe in cache
   - OHLCV latest date within 7 days
   - No silent failures (every missing ticker explicitly in failed_tickers.json)
   - Data quality firewall ≥ 90% PASS+WARNING
   - Benchmarks PASS firewall

2. **`tests/test_cache_freshness.py`** (29 tests) — dashboard caches
   present, non-empty, current:
   - All 8 parquet files + 4 JSON files exist
   - All parquets non-empty
   - CCQS latest date within 7 days
   - 10 components present in dashboard `components.parquet`
   - Cache size within expected 15-40 MB band
   - Regime context current
   - All 11 sanity checks pass

3. **`tests/test_pipeline_integrity.py`** (12 tests) — pipeline outputs
   internally consistent and sane:
   - 11 sanity checks pass
   - CCQS values in [0, 100]
   - CCQS distribution non-degenerate
   - Grade distribution covers all 5 grades
   - 10 components present, no all-NaN columns
   - State/tier/setup distributions non-degenerate
   - STATE_WEIGHTS sum to 1.0 per state
   - Confidence-blending mechanism intact
   - All output parquets share latest date

4. **`tests/reference/test_tv_parity.py`** (existing) — 10 canary tickers
   numerically pinned (140 field checks).

**CI workflow integration:** All four suites run as HARD gates (no
`continue-on-error`) BEFORE the dashboard-cache commit step. If any
fail, the workflow fails, no cache is pushed to main, and the prior
good cache remains live. Legacy `test_phase2_spot_check` and
`test_phase3_validation` continue as soft gates AFTER the commit
(aligned to earlier baselines).

**Net effect:** Daily CCQS pipeline is now guarded against:
- Silent data-fetch failures (universe coverage test)
- Stale or missing caches (freshness test)
- Pipeline integrity failures (sanity, distributions, ranges)
- Numerical regressions against the 10 TV canaries

User direction satisfied: "every day from Monday-Friday without any
fail" with explicit test coverage of "all stocks data fetches properly
and computation happens with no issues whatsoever."

### Phase 15 — Small Cap CCQS (CCQS-SC) development [PLANNED]

Separate Small Cap CCQS tool with independent empirical methodology.
12 sub-phases (15.1-15.12) covering universe definition, data
infrastructure, feature engineering, state classifier, setup classifier,
tier classifier, component weights, comprehensive validation, dashboard
integration, documentation, deployment. Path C rigor throughout.

Begins after Phase 14R is user-confirmed clean.

## Forward expectations (post-Path C)

Per `SPEC.md` Methodology Lock §3, future methodology changes require:
- Forward-looking signal degradation (current OOS IC drops materially), OR
- Independent research findings (new academic work, new data sources), OR
- Clear computational bugs

Patterns observed in dashboard historical displays do NOT constitute valid motivation for methodology changes. This prevents hindsight bias.

## Deferred backlog (post-Path C)

See `SPEC.md` §Path C deferred backlog section for the full list. Highlights:
- STRONG_LEADER + ESTABLISHED_LEADER tier merger (statistically near-identical)
- EMERGING_LEADER tier rename or collapse
- Extended Exhaustion → Late-Stage Trending rename
- Threshold tuning: Distribution Pattern `dist_days_min`, PULLBACK `mu_rsi_14`
- Premium Pullback criteria review
- Dashboard preset filters (high-quality, mean-reversion)
- NaN-tier filter / warning chip

---

## Phase 16-17 — CCQS empirical re-validation + regime-aware deployment

**Status (2026-05-27):** Phase 17 deployed.

After Phase 15.1.D revealed 90% walk-forward failure on small caps, Phase 16
applied the same Sub-Investigation D rigor to LC under the user direction:

> "Apply Sub-Investigation D-level rigor to CCQS validation. Empirically
> verify what CCQS actually does well and what might be illusion. No
> assumptions preserved."

### Phase 16 — Comprehensive CCQS re-validation (16.A-16.I)

Nine sub-investigations on 874-ticker LC universe (4.77 GB feature matrix,
463 features × 2360 dates including all 11 production CCQS components):

- **16.A**: Forward return characterization. LC has stronger mean/hit/skew
  than SC. Universal patterns: HIGH market vol → 4× returns; low-vol anomaly.
- **16.B**: Same 343 base + 84 XS + 25 sector-relative + 11 CCQS components
  feature matrix as Phase 15.1.C, extended history (2017-01+).
- **16.C**: Per-date Spearman IC ranking. **Best CCQS component
  (`s_residual_momentum`) ranks 71/463; `s_momentum` ranks 426/463.** Raw
  `mom_ret_126d` (rank 15) more predictive than ALL CCQS components.
- **16.D**: Axis-stratified regressions on pre-screened 155 features.
  CCQS axis adds +1.4% incremental per-date R² — not redundant.
- **16.E**: Conditional IC across 4 regime axes × 4 horizons. Top 9
  sign-flippers are ALL CCQS components (62% average flip rate).
- **16.F (CRITICAL TEST)**: Walk-forward OOS validation, 88 windows.
  **0/11 CCQS components survived. Only 1/61 features total survived.**
- **16.G**: Time-varying analysis. CCQS components have IC +0.03 in
  STRONG_BULL but −0.08 in STRONG_BEAR — **CCQS is a bull-market signal,
  not all-weather.** 5 useful Tier-1 components, 6 weak/noise Tier-2.
- **16.H**: Production STATE_WEIGHTS vs empirical optimal. Production
  TRENDING weights only 27.5% off empirical optimum. **Production already
  drops worst components to near-zero** (`s_extension` 0%, `s_demand` 0%,
  `s_momentum` 0.3%).
- **16.I**: Honest synthesis — three path-forward options.

### Phase 17 — Regime-aware deployment (17.0-17.9)

User selected the most empirically-grounded improvement:

- **17.0**: Tested 42 candidate regime indicators (trend/vol/drawdown/breadth/
  composite). **`dd_lt_15pct` selected** — SPY drawdown from 252-day high <15%.
  - t-statistic 8.74, p < 0.0001
  - IC differential at 63d: +0.093 (in-regime +0.027 vs off-regime −0.066)
  - On 90% of trading days; real-time computable from SPY price only
- **17.1-17.2**: Built v2 candidates (5 Tier-1 components, renormalized
  weights, empirical bull weights). v2 vs v1 score correlation 0.989;
  top-50 daily overlap 86%.
- **17.4**: Walk-forward validation. **Critical finding**: v2 vs v1 IC
  difference is ~0.001 (immaterial). **Regime filter (`dd_lt_15pct=1`)
  is the actual empirical innovation** — turns 0/12 walk-forward survivors
  → 3/12 (1/12 strictly robust at 126d in-regime).
- **17.5**: Decision gate. Selected Option 2: deploy regime indicator only;
  keep v1 STATE_WEIGHTS (already empirically near-optimal).

### Phase 17.6-17.9 — Regime indicator deployment

`compute/build_dashboard_cache.py::_design_space_regime()` writes new
`ccqs_design_space` key into `data/cache/dashboard/regime_context.json`:

```json
"ccqs_design_space": {
  "indicator": "dd_lt_15pct",
  "spy_dd_from_high": -0.0002,
  "spy_above_200ma": true,
  "in_regime": true,
  "regime_state": "GREEN",
  "regime_label": "Design space — high confidence",
  "empirical_basis": {
    "ic_differential_63d": 0.093,
    "t_statistic": 8.74,
    "p_value_lt": 0.0001
  }
}
```

Three-state classification:
- **GREEN**: `dd_lt_15pct=TRUE AND SPY > 200d MA` — design space, high confidence
- **YELLOW**: `dd_lt_15pct=TRUE AND SPY ≤ 200d MA` — in regime, trend uncertain
- **RED**: `dd_lt_15pct=FALSE` — out of design space; apply discretion

`app/streamlit_app.py` renders prominent regime chip immediately below the
title; RED state also adds explicit `st.error` banner with empirical citation.

**No changes to STATE_WEIGHTS, components.parquet, ccqs.parquet, or TV
references — methodology preserved; regime awareness added as display layer.**

**Net effect**: production CCQS now ships with empirically-validated
design-space awareness. Users see at a glance whether the day's
environment is within the validated working regime.

---

## Phase 18 — UI / UX cleanup pass (2026-05-27)

User-driven dashboard cleanup. Thirteen targeted changes, zero methodology
impact: STATE_WEIGHTS, CCQS computation, and TradingView reference parity
are all preserved bit-identically (140 / 140 fields, 11 / 11 sanity checks).

### Vocabulary

- **18.1** — Dropped the "-LC" suffix everywhere. The system only operates
  on the large-cap universe, so "CCQS-LC" added confusion rather than
  precision. Affected: regime chip copy, `SPEC.md` §16-17, `USER_GUIDE.md`
  §J, `CHANGELOG.md`, internal Phase 17 docstrings.
- **18.10** — Expanded acronyms in every user-facing surface. Component
  display names: `RS` → "Relative Strength", `RSL` → "Relative Strength
  Line", `MTF` → "Multi-Timeframe Alignment". Key-metrics labels: `ADX-14`
  → "Average Directional Index (14)", `RSI-14` → "Relative Strength
  Index (14)", `% from 50 DMA` → "% from 50-day Moving Average", and so
  on. Methodology paragraph rewritten without acronyms.

### Top Stocks table

- **18.2** — Removed the standalone "RS" column. `rs_rating_spy` is already
  one of the strongest inputs to CCQS via `s_rs` and `s_rs_leadership`;
  showing it as a separate column duplicated signal already encoded in
  the rank.
- **18.3** — Replaced the single "Δ Today" column with three Δ CCQS
  columns at 1-day / 5-day / 21-day trading-day horizons. Δ values are
  computed at runtime from the slim dashboard cache (no schema change to
  any parquet); the 5d / 21d offsets step through the sorted unique date
  index in `ccqs.parquet`, so lookbacks are trading-day-accurate
  regardless of market holidays.
- Renamed the "Tier" column header to "Leadership Tier" for clarity.

### Themes table

- **18.4** — Removed the "Members" (constituent count) column. Cardinality
  is metadata, not insight.
- **18.6** — Removed the "% Grade A+" column. It overlapped with the
  `% > 50-day Moving Average` breadth measure; kept the latter as the
  cleaner price-action signal independent of the CCQS score itself.
- **18.5** — Verified the breadth math: `pct_above_50dma` =
  `g["pct_above_sma_50"].mean() × 100` in `compute/aggregation.py:243`,
  where `pct_above_sma_50` is a 0/1 per-ticker binary in
  `features.parquet`. Computation is correct.
- **18.13** — Added a "Constituents" column that lists every basket
  member, sorted by current CCQS descending, comma-joined. Users can
  cross-reference on charting platforms / brokerages without leaving
  the dashboard.

### What Changed Today

- **18.7** — Replaced the threshold-gated lists with magnitude-ranked
  top-10 lists. Section headers renamed:
  - "New Emerging Leaders" → **"Strongest Risers"** (top 10 by 1-day Δ CCQS)
  - "Newly Deteriorating" → **"Largest Decliners"** (bottom 10 by 1-day Δ CCQS)
  - "Grade Jumps" → **"Grade Changes"** (top 10 by |Δ CCQS|; grade-letter
    changers preferred, padded with the next largest absolute movers when
    fewer than 10 changed grade letters on the day)

### Stock detail

- **18.8** — Rebuilt the header to a two-tier layout: a large-weight ticker
  symbol, then a row of labeled key-value chips (Score, Leadership Tier,
  State, Theme). Replaces the previous flat middle-dot pipe.
- **18.9** — Removed the reliability chips block entirely. CCQS is a
  technical scoring system, not a predictive model; per-stock "reliability"
  framing was misleading (e.g., labelling mega-caps as a *warning* when
  they are simply a different quintile).

### Market-context caution

- **18.12** — Replaced the always-on three-state regime chip with a
  context-only caution. No banner in GREEN regime (the silent majority
  case). YELLOW shows an `st.info` caution noting the broad market is
  below its 200-day moving average. RED shows an `st.warning` noting the
  broad market is in a meaningful drawdown. Copy is professional and
  measured; CCQS rankings are always described as a screening aid, not
  a directional signal.

### Data correctness

- **18.11** — Confirmed SNDK is already correctly assigned to the
  "Memory and Storage" basket (`data/universe.py` lines 33, 1223, 2090,
  2254). No change needed; the user's "SDNK" was a typo for SNDK
  (SanDisk's NASDAQ ticker).

### Files touched

```
app/streamlit_app.py
app/utils/tables.py
app/utils/data_loader.py
compute/build_dashboard_cache.py
SPEC.md
USER_GUIDE.md
CHANGELOG.md
data/cache/dashboard/regime_context.json   # text refresh from build script
```

### Net effect

The dashboard reads like a focused technical screen: top stocks by CCQS
with three change-horizon columns, themes by basket with breadth and
constituent listing, three magnitude-ranked change boards, and a clean
stock detail with labeled chips. Caution banners only when the broad
market context warrants them. No chip noise on normal days.

---

## Phase 20 — Basket name cleanup (2026-05-27)

Seven basket renames to fix redundancy, jargon, and misleading "and" connectors. No methodology change, no ticker membership change, no TradingView parity impact.

### Renames applied

| Old | New | Reason |
|---|---|---|
| Battery Storage and BESS | **Battery Energy Storage** | Redundant — "BESS" expands to "Battery Energy Storage System". |
| RF and Wireless Connectivity | **Wireless Connectivity Chips** | RF *is* wireless connectivity; "Chips" clarifies these are silicon (QCOM, SWKS) not carriers. |
| Trucking and LTL | **Freight Trucking** | LTL is a subset of trucking, not a peer. |
| Restaurants and QSR | **Quick Service Restaurants** | All members are QSR/fast food (MCD, YUM, etc.); peer basket "Casual Dining" already covers the sit-down names. |
| Cannabis and MSOs | **Cannabis Multi-State Operators** | Expands the acronym; consistent with Phase 18's acronym-cleanup pattern. |
| Volatility and Market Plumbing | **Market Infrastructure and Exchanges** | "Plumbing" is industry slang; "Infrastructure and Exchanges" is the standard term for CBOE/CME/ICE/NDAQ/etc. |
| CRO and Clinical Services | **Contract Research and Clinical Services** | Expands the acronym. CRO = Contract Research Organization. |

### Files touched

`data/universe.py` (CATEGORIES, BASKET_PRIORITY, PRIMARY_BASKETS, PRIMARY_BASKET_CONSTITUENTS — 94 occurrences); `SPEC.md`; `USER_GUIDE.md`; `CHANGELOG.md`. Pipeline aggregation re-run; dashboard cache rebuilt.

### Validation

- 25/25 metric integrity tests PASS
- 140/140 TradingView reference fields PASS (methodology unchanged)
- 147 baskets in `theme_aggregates.parquet` (unchanged count)
- 6 of 7 renamed baskets show in the dashboard's Themes table with new names; 7th ("Market Infrastructure and Exchanges") is a tag overlay whose constituents all dedup into higher-priority primary baskets (Exchanges and Market Data, Brokers and Trading Platforms, etc.), so it surfaces only when used as a tag — rename takes effect there.


---

## Phase 21 — SNDK basket coverage (2026-05-27)

SNDK (SanDisk, post-WDC spinoff Feb 2025) was in only 1 basket (Memory and
Storage) while peers MU/WDC/STX are in 3 baskets each. Added SNDK to three
additional baskets where its peers live and where the business fits.

### Additions

| Basket | Reason |
|---|---|
| **Servers and AI Hardware** | Same coverage as WDC, STX. SanDisk SSDs go into the same server platforms. |
| **Enterprise Storage and Data Infrastructure** | Same coverage as WDC, STX. SanDisk is a pure-play enterprise flash vendor. |
| **AI Hardware Supply Chain** | Same coverage as MU. NAND flash is a critical part of the AI hardware supply chain (training/inference workloads need fast storage tiers). |

### Skipped (intentional)

- **HBM and Advanced Memory** — SanDisk is NAND flash, not HBM (High Bandwidth Memory). HBM is a DRAM product made by Micron, Samsung, SK Hynix. Adding SNDK here would be a misclassification.

### Status note

SNDK still has NaN CCQS for ~4-5 more trading days while the
`residual_momentum_252d` rolling window fills in (SNDK started trading
2025-02-18, so it needs through ~early June 2026 to accumulate the full
252-day window). The basket assignments take effect immediately once
scoring begins.

### Validation

- 25/25 metric integrity tests PASS
- 140/140 TradingView reference fields PASS
- SNDK now in 4 baskets (Memory and Storage primary + 3 tag overlays):
  Servers and AI Hardware, Enterprise Storage and Data Infrastructure,
  AI Hardware Supply Chain. Confirmed via PRIMARY_BASKETS + TAGS dict.


---

## Phase 23 — Add 9 major recent IPOs (2026-05-28)

Universe expanded from 883 → 892 tickers. All additions are well-known
recent listings that belong in already-defined baskets.

### Tickers added

| Ticker | Company | Listed | Primary basket | Tag overlays |
|---|---|---|---|---|
| **CRWV** | CoreWeave | Mar 2025 | AI Cloud Challengers and Neocloud | AI Hardware Supply Chain, AI Data Center Capex |
| **ALAB** | Astera Labs | Mar 2024 | AI ASICs and Custom Silicon | AI Hardware Supply Chain |
| **RDDT** | Reddit | Mar 2024 | Consumer Internet | Digital Advertising Platforms |
| **TEM** | Tempus AI | Jun 2024 | Healthcare AI and Automation | Diagnostics and Life Science Tools |
| **CRCL** | Circle Internet Group | Jun 2025 | Stablecoin and Tokenization Proxies | — |
| **PSKY** | Paramount Skydance | Aug 2025 | Streaming and Audio | — |
| **BIRK** | Birkenstock | Oct 2023 | Apparel and Footwear | Luxury Goods |
| **KGS** | Kodiak Gas Services | Jun 2023 | Midstream Pipelines | — |
| **CAVA** | Cava Group | Jun 2023 | Casual Dining | — |

### Methodology note — long warmup

Per the Phase 16 feature-cascade structure, residual-momentum-252d
requires ~504 valid trading days (252 of rs_rating_spy warmup + 252 of
residual slope window). Most of these names won't score immediately:

- BIRK, CAVA, KGS (listed 2023): should score soon (close to 504-day mark)
- RDDT, ALAB (Mar 2024): ~14 months listed → ~290 days short of the 504 threshold
- TEM (Jun 2024): ~11 months listed → ~340 days short
- CRWV (Mar 2025): ~14 months listed → ~290 days short
- CRCL, PSKY (Jun-Aug 2025): just listed; ~250-280 days short

All will surface in the dashboard automatically as their windows fill.
The basket assignments are in place now so the pipeline picks up OHLCV
on the next daily run and tickers appear in basket constituent lists.

### Validation

- 25/25 metric integrity tests PASS
- 140/140 TradingView reference fields PASS (methodology unchanged)
- Universe count: 892 unique tickers across 275 baskets


---

## Phase 24 — Graceful CCQS degradation for partial-history names (2026-05-28)

CCQS composite now renormalizes state weights for tickers that are
missing one or more components due to insufficient post-IPO/spin-off
history. Replaces the prior all-or-nothing behavior where a single NaN
feature would emit a NaN CCQS for the entire ticker.

### Methodology change

In `compute/ccqs.py`, `_state_composite_z()` is replaced with
`_composite_z_with_renormalization()`. The new function:

1. Builds per-row **effective component weights** `e[i, c] = Σ_s p_adj_s[i] · W[s, c]`
   — identical to the existing Bayesian blend across states.
2. For each row, identifies which components are non-NaN.
3. **Renormalizes** the present components so their weights sum to 1.
4. Computes the composite using only valid components.
5. Emits NaN if either:
   - `weight_present < 0.60` (less than 60% of state weight present), OR
   - `n_valid_components < 6` (fewer than 6 of 10 non-NaN).

### Bit-identical guarantee for full-data tickers

For any ticker with all 10 components valid, `weight_present == 1.0`
exactly, the renormalization is the identity, and the composite is
**mathematically equivalent** to the original formula. **TradingView
reference parity remains 140/140** (verified post-implementation; same
canary CCQS values within tolerance).

### New columns in `ccqs.parquet`

| Column | Type | Description |
|---|---|---|
| `weight_present` | float | Share of state weight present per row (1.0 = full data) |
| `n_valid_components` | int | Number of non-NaN components per row (out of 10) |
| `is_partial` | bool | True when `weight_present < 1.0` and CCQS was computed |

### Dashboard disclaimer

The Stock Detail panel shows a yellow caution block on partial-CCQS
tickers explaining how many components were used and the share of state
weight present. Top Stocks / Themes tables remain unchanged in shape
(partial tickers appear with their renormalized scores; the disclaimer
is only on the detail panel).

### Tickers immediately benefiting (2026-05-28 snapshot)

Universe count: 860 scored (up from 849). Two partial-CCQS rows today:

| Ticker | n_valid / 10 | weight_present | CCQS | Grade |
|---|---:|---:|---:|---|
| SNDK | 9 | 0.952 | 98.19 | S (partial) |
| CRWV | 8 | 0.669 | 60.67 | B (partial) |

CRCL is still NaN today (only 6 components, 42% weight present — below
threshold). It needs ~6 more trading days for `rs_rating_spy` to clear
the 252-day warmup, then will auto-enter partial mode.

### Validation

- 25/25 metric integrity tests PASS
- **140/140 TradingView reference fields PASS** (bit-identical preserved)
- 11/11 pipeline sanity checks PASS
- Compute scripts: `_composite_z_with_renormalization()` verified on
  synthetic test panel (full-data row identical to original formula;
  1-NaN row gets renormalized; 4-NaN-heavyweight row correctly NaN'd)

### Threshold tuning rationale

Two gates protect score reliability:

- **Weight gate (0.60)**: at most 40% of state weight may be imputed by
  renormalization. The dominant carriers `s_rs` and `s_rs_leadership`
  account for ~54% in TRENDING; if both are NaN the row is correctly
  rejected as too partial.
- **Component count gate (6 / 10)**: at least 6 of 10 components must
  be present, preventing pathological cases where small-weight
  components dominate due to renormalization.

Above these gates, the renormalized composite is treated as a
legitimate estimate with a disclaimer. Below them, the composite is
emitted as NaN.

## Phase 25 — Setup label redesign (2026-05-28)

Replaces the 27-label setup vocabulary with a 13-label chart-evocative
cascade (12 at Phase 25; Phase 27 added "Reclaim" as the 13th).
**Display-layer only** — no CCQS, state, leadership, or
methodology changes. The legacy classifier in
`compute/setup_classifier.py` is preserved untouched for reference; the
pipeline now calls the new `compute/setup_classifier_v2.py`.

### Design principles

1. Labels are chart-hooks, not indicator-language.
2. Describe present state, never predict future outcome.
3. Decompose patterns into measurable constituents; do not name gestalts
   (no cup-and-handle / wedge / H&S / etc.).
4. Uptrend/Downtrend deliberately omitted — too prevalent to be
   informative.
5. Thresholds are calibrated starting points and may be tuned after
   coverage analysis on the live universe.
6. 1–2 word labels (hard constraint).

### The 13 labels (cascade order, first match wins)

| # | Label | One-line intent |
|---|---|---|
| 1 | New High | Today's close = 252d max, not extended |
| 2 | Breakout | Closed above prior 40d high with range expansion |
| 3 | Failed Breakout | A breakout within last 5 days that has since closed below the cleared level |
| 4 | Tight Base | Bullish stack + bottom-25% cross-sectional ADR + within 5% of 252d high |
| 5 | Coiling | Bullish stack + 20d range < 60% of 60d range + BB-width in bottom-20% of own 252d history |
| 6 | Shallow Pullback | Bullish stack + 3–10% off 20d high + holding 21EMA |
| 7 | Deep Pullback | Bullish stack + 10–20% off 20d high + holding 50d MA |
| 8 | Extended | Bullish stack + %-from-50d-MA above own 80th-percentile |
| 9 | At Highs | Bullish stack + within 5% of 252d high (residual) |
| 10 | Basing Low | Within 10% of 252d low + bottom-40% cross-sectional ADR |
| 11 | Breakdown | Closed below prior 40d low AND below 50d MA |
| 12 | Reclaim | Breakdown within last 5 days now closing back above the failed level |
| 13 | Sideways | 60d range < 20% of price + position within middle 50% of 60d range |

If no condition matches → empty string (`""`). Silence beats noise.
`setup_confidence = 1.0` for any assigned label, `0.0` for blank.

### Thresholds — universe-relative or scale-invariant

All thresholds are either:
- **Cross-sectional percentiles** within the universe-of-the-day (e.g.
  ADR bottom 25 / 40th percentile), OR
- **Self-relative ratios** against the name's own trailing history
  (e.g. BB-width ≤ 20th percentile of its own 252d history), OR
- **Scale-invariant % values** (e.g. 3–10% off 20d high).

No absolute price levels, no per-name hand-tuned values.

### Coverage on 2026-05-28 (universe = 860)

| Label | Count | % |
|---|---:|---:|
| (blank) | 435 | 50.6% |
| Sideways | 89 | 10.3% |
| Shallow Pullback | 71 | 8.3% |
| Basing Low | 59 | 6.9% |
| Extended | 48 | 5.6% |
| Tight Base | 47 | 5.5% |
| Breakdown | 37 | 4.3% |
| Failed Breakout | 20 | 2.3% |
| Breakout | 19 | 2.2% |
| Coiling | 17 | 2.0% |
| Deep Pullback | 12 | 1.4% |
| At Highs | 5 | 0.6% |
| New High | 1 | 0.1% |

Max single-label share 10.3% — well below the 40% spec ceiling.

### Validation-cycle fixes

Two fixes were applied after first-pass coverage review:

- **Fix 1 — Failed Breakout primitive**. First pass used the legacy
  `failed_breakout_flag_10d` (too broad — coverage 22.7%). Replaced
  with spec-correct **5-day** primitive (`failed_breakout_flag_5d_v2`
  in `compute/features.py` Cat 24): within last 5 trading days a
  Breakout (cond #2) fired, AND today's close is below the level that
  breakout cleared. Coverage post-fix: 2.3%.
- **Fix 2 — Sideways widening**. First pass used 60d range < 15%
  AND 30 ≤ position ≤ 70 (coverage 4.8%). User-approved widening to
  60d range < 20% AND 25 ≤ position ≤ 75 (coverage post-fix: 10.3%).
  Preserves Sideways' "deliberately boring, suppress chart-pull" role.

### New features (Cat 24 in `compute/features.py`)

`close_max_40d`, `close_min_40d`, `high_max_20d`,
`pct_from_20d_high`, `range_20d_pct_of_price`,
`range_60d_pct_of_price`, `range_20d_to_60d_ratio`,
`position_in_60d_range`, `pct_ma_50_p80_252d`, `true_range_x_atr14`,
`failed_breakout_flag_5d_v2`. Total `FEATURE_ORDER` length is now 137
(was 126).

### Validation

- 140/140 TradingView reference fields PASS (only `setup` /
  `setup_confidence` changed; all 12 numeric fields × 10 canaries
  bit-identical).
- 11/11 pipeline sanity checks PASS.
- Spot-checks (5 names per label) confirm correct assignment for all
  12 labels.

### Canary setup transitions (REFERENCE_DATE = 2026-05-22)

| Ticker | Old (27-label) | New (12-cascade) |
|---|---|---|
| NVDA | Trending (Generic) | Shallow Pullback |
| MSFT | Range Consolidation | "" (blank) |
| META | Deteriorating (Generic) | "" (blank) |
| GOOGL | Exhaustion w/ Bearish Divergence | Shallow Pullback |
| TSLA | Theme Leader Pullback | "" (blank) |
| AMZN | Range Consolidation | Coiling |
| JPM | Deteriorating (Generic) | Sideways |
| TSM | Pullback to 21EMA | Coiling |
| LLY | Indeterminate Pattern | Extended |
| UNH | Trending (Generic) | Tight Base |

## Phase 26 — State + Leadership Tier display rename + cron move (2026-05-28)

Display-layer rename of 5 state/tier labels plus the NaN/UNCLASSIFIED
consolidation. **No methodology change.** Internal classifier labels
(TRENDING, EXHAUSTION, STRONG_PERFORMER, ...) are unchanged in
`compute/state.py` / `compute/leadership.py` and remain the keys for
`STATE_WEIGHTS` lookup, tier composition logic, regime gates, and every
downstream consumer. Only the user-facing strings rendered on the
Streamlit dashboard are translated.

### Pattern A — translation at render layer

New module `compute/display_labels.py` is the single source of truth.
Parquet columns (`state.parquet`, `leadership.parquet`) keep storing
the internal ALL_CAPS labels exactly as before; the dashboard
translates at the render boundary. No schema change. No cache rebuild
needed for future label tweaks.

### The 5 renames + 1 consolidation

**State (3 of 6 change, 3 kept):**

| Internal (unchanged) | Display |
|---|---|
| TRENDING | Trending |
| PULLBACK | Pullback |
| CONSOLIDATING | Consolidating |
| EXHAUSTION | **Parabolic** |
| DETERIORATING | **Breaking Down** |
| INDETERMINATE | **No Edge** |

**Leadership Tier (3 renames + NaN consolidation, 6 Title Case):**

| Internal (unchanged) | Display |
|---|---|
| ELITE_LEADER | Elite Leader |
| STRONG_LEADER | Strong Leader |
| ESTABLISHED_LEADER | Established Leader |
| EMERGING_LEADER | Emerging Leader |
| STRONG_PERFORMER | **Steady** |
| NEUTRAL | Neutral |
| WEAK_PERFORMER | Weak Performer |
| DETERIORATING | **Fading Leader** |
| WEAK_LAGGARD | Weak Laggard |
| UNCLASSIFIED | **No RS Signal** |
| NaN (insufficient RS history) | **No RS Signal** *(consolidation)* |

### Rationale per rename

- **EXHAUSTION → Parabolic** — descriptive, not predictive (consistent
  with Phase 25 principle: name the geometry, don't predict the outcome).
- **State DETERIORATING → Breaking Down** — resolves the state/tier
  naming collision; "Breaking Down" describes price-structure damage.
- **INDETERMINATE → No Edge** — honest about what the residual state
  means; mirrors Phase 25's "blank" residual pattern (suppresses chart-pull).
- **STRONG_PERFORMER → Steady** — at 33% of universe, "Strong Performer"
  overpromised. "Steady" honestly describes the mid-pack-above-average band.
- **Tier DETERIORATING → Fading Leader** — resolves the state/tier
  collision; captures former-strength + current-decline.
- **UNCLASSIFIED + NaN → "No RS Signal"** — collapses the
  user-facing distinction between two operationally identical "no RS
  signal" states (Phase 11.C.1 catch-all + insufficient-history NaN).
  Internal distinction preserved in parquet for debugging.

### Render points translated (`compute.display_labels.display_*`)

- `app/utils/tables.py`: top_stocks_table, emerging_leaders_table,
  newly_broken_table, peers_table — translate `tiers` / `states` lists
  after color lookup, before passing to `render_table`.
- `app/streamlit_app.py`: sidebar Leadership Tier / State multiselects
  show display strings, filter the dataframe by reverse-mapping to
  internal labels. Stock-detail chips use `display_tier()` / `display_state()`.

### Render points NOT translated (intentional, methodology layer)

- `compute/state.py`, `compute/leadership.py` — classifier output
  values remain ALL_CAPS internal labels.
- `compute/ccqs.py` `STATE_WEIGHTS` — keys remain ALL_CAPS internal.
- `app/utils/data_loader.py` STATE_WEIGHTS lookup — receives internal
  labels from parquet.
- `app/utils/colors.py` `color_tier()` / `color_state()` — palette keys
  remain ALL_CAPS internal (colors computed BEFORE display translation).
- `tests/reference/tv_snapshots.py` — stores ALL_CAPS internal labels.

### TV reference behavior

The TV parity test compares internal labels (parquet column ↔ snapshot
dict). Phase 26 leaves both sides unchanged. **140/140 PASS without
any snapshot modification** (verified post-implementation).

### Validation

- 13/13 new `tests/test_phase26_display_labels.py` PASS:
  full map coverage, NaN consolidation, no state/tier collision,
  STATE_WEIGHTS lookup intact, parquet still stores internal labels,
  coverage distributions identical pre/post translation.
- 38/38 existing pipeline + metric integrity tests PASS.
- **140/140 TradingView reference fields PASS** (bit-identical).
- Coverage distributions match Phase 25 exactly (no detection change).

### Pre-existing test bug fixed in passing

`tests/test_pipeline_integrity.py::test_setup_distribution_non_degenerate`
was checking that no "non-generic" setup exceeded 40%, but failed to
treat the Phase 25 blank `""` residual as a catch-all (it hit 50.6%
post-Phase 25). Fixed by adding `""` to the residual exclusion list
alongside `"(Generic)"` and `"Indeterminate Pattern"`.

### Daily cron moved 4:30 PM ET → 4:05 PM ET

`.github/workflows/pipeline.yml`: cron schedule changed from
`30 20 / 30 21 * * 1-5` (4:30 PM ET) to `5 20 / 5 21 * * 1-5`
(4:05 PM ET — 5 minutes after NYSE close). DST-aware guard unchanged
(still gates on ET hour == 16). The pipeline now publishes the daily
refresh ~25 minutes earlier; data settlement on yfinance's end-of-day
feed is reliable within 5 minutes of cash-equity close.

## Phase 27 — Setup cascade bug fix + "Reclaim" label (2026-05-28)

Two surgical changes to the Phase 25 setup classifier, both
display-layer only. **No methodology change** — CCQS scores, state
classifications, leadership tiers, and STATE_WEIGHTS are bit-identical.
140/140 TV parity preserved.

### Bug fix — extended names mis-labeled as Pullbacks

User flagged INTC's "Deep Pullback" label as wrong on 2026-05-28.
Investigation confirmed the bug: INTC sits at `pct_ma_50 = +45.7%`
while its own 252d 80th-percentile is only `+32.0%` — unambiguously
extended above its 50-day moving average. But the Phase 25 cascade
fired "Deep Pullback" (cond 7) before "Extended" (cond 8) because
INTC also sat 11.1% off its 20-day high, hitting the Deep Pullback
gate.

**Affected names today**: 29 of 83 Shallow/Deep Pullback labels
(35%) carried the same bug. Worst case: UMC at +75% above 50MA vs
own p80 +14%, labelled "Shallow Pullback" pre-fix.

**Fix**: added `pct_ma_50 ≤ pct_ma_50_p80_252d` (own 80th-pct gate) to
both Shallow Pullback (cond 6) and Deep Pullback (cond 7) — matches
the equivalent gate already present on "New High" (cond 1) since
Phase 25. Extended names now correctly fall through to "Extended"
(cond 8). Tight Base (cond 4) and Coiling (cond 5) retain no extension
gate because consolidation near 252d highs after extension is the
institutionally valid "constructive base" pattern.

**Coverage shift after fix:**
- Shallow Pullback: 71 → 36 (-35 names)
- Deep Pullback:    12 →  8 (-4 names)
- Extended:         48 → 75 (+27 names)
- INTC verified: was "Deep Pullback", now "Extended" ✓
- UMC, QCOM, DDOG, FTNT, CRWD, PANW, MRVL, ON, NTAP, ELV, CVS, ... → "Extended" ✓

### New label — "Reclaim" (cond 12, symmetric to Failed Breakout)

Phase 25 had Failed Breakout (cond 3 — a breakout that has been
reversed below the cleared level) but no symmetric bullish analog.
Audit identified this as the one principled gap in the 12-cascade.

Added "Reclaim" as cond 12 (between Breakdown and Sideways): a
Breakdown within the last 5 trading days that has since been
reclaimed (today's close is above the level that was breached). This
is the textbook bear-trap / Wyckoff-spring pattern — a strong
short-covering signal that was previously labeled blank.

**New primitive** `failed_breakdown_flag_5d_v2` in `compute/features.py`
Cat 24 (length 137 → 138), exact symmetric mirror of
`failed_breakout_flag_5d_v2`:

```python
breakdown_today_flag = (c < close_min_40d.shift(1)) & (c < sma_50)
breakdown_level_today = close_min_40d.shift(1)
recent_breakdown_level_5d = (
    breakdown_level_today.where(breakdown_today_flag)
                         .rolling(5, min_periods=1).min()
                         .shift(1)
)
failed_breakdown_flag_5d_v2 = (
    recent_breakdown_level_5d.notna() & (c > recent_breakdown_level_5d)
).astype(float)
```

**Coverage**: 24 names today (2.8%) — comparable to Failed Breakout (2.3%).
Sample: DE, INTU, ISRG, LDOS, PYPL, WMT — names that had a Breakdown
in the past 5d and have since reclaimed the breached level.

### Updated cascade (13 labels)

```
1. New High        8. Extended
2. Breakout        9. At Highs
3. Failed Breakout 10. Basing Low
4. Tight Base      11. Breakdown
5. Coiling         12. Reclaim       (NEW)
6. Shallow Pullback 13. Sideways
7. Deep Pullback
```

Blank residual: 50.6% → 45.6% (down 5pp — 24 ex-blanks now get Reclaim, plus secondary shifts from the bug fix). Still within the 40-50% design band.

### Coverage table after Phase 27

| Label | Pre-Phase 27 (n) | Post-Phase 27 (n) | Δ |
|---|---:|---:|---:|
| (blank) | 435 | 392 | −43 |
| Sideways | 89 | 93 | +4 |
| Extended | 48 | 75 | +27 |
| Basing Low | 59 | 62 | +3 |
| Breakout | 19 | 50 | +31 (note¹) |
| Tight Base | 47 | 42 | −5 |
| Shallow Pullback | 71 | 36 | −35 (bug fix) |
| Breakdown | 37 | 33 | −4 |
| **Reclaim (NEW)** | — | **24** | +24 |
| Failed Breakout | 20 | 20 | 0 |
| Coiling | 17 | 17 | 0 |
| At Highs | 5 | 8 | +3 |
| Deep Pullback | 12 | 8 | −4 (bug fix) |
| New High | 1 | 0 | −1 |

¹ Note on Breakout: between the Phase 25 and Phase 27 cache builds, an
intraday OHLCV refresh pulled fresh bars (Phase 26's loader retry for
the 9 missing names). Several names that were near-breakout on the
earlier snapshot crossed their 40d high on the updated bars. The
+31 Breakout gain is the joint effect of (a) the bug fix freeing some
extended-but-also-breaking-out names from Shallow Pullback to Breakout,
and (b) intraday tape action between the two cache builds.

### Validation

- 140/140 TradingView reference fields PASS (bit-identical, no canary
  changed setup label).
- 11/11 pipeline sanity checks PASS.
- 51/51 pytest tests PASS (pipeline_integrity, metric_integrity,
  phase26_display_labels).
- Spot-checks: 27 of 29 previously-mis-labeled names now correctly
  labeled Extended. Reclaim catches 24 real bear-trap names today.

## Phase 28 — Dead-weight cleanup: s_demand removed + 0-weight rows hidden (2026-05-28)

User-flagged that the Component Contributions table displays rows
contributing literally nothing to CCQS — specifically `s_demand`
(weight 0.0 in every state since Phase 7) and `s_extension` (0-weight
for stocks in TRENDING / DETERIORATING but active in the other 4 states).

### Change A — display: hide 0-weight rows

`app/utils/data_loader.py::load_components_for_ticker` now filters
any component whose weight in the ticker's primary state is `0.0`.
Per-row, not global: a stock in PULLBACK still sees `s_extension`
(weight 1.9% there); a TRENDING stock like NVDA no longer sees it.

### Change B — methodology: drop s_demand permanently

`s_demand` had weight `0.000000` in all six entries of `STATE_WEIGHTS`
since Phase 7. The column was zeroed but never dropped. Now removed
from `COMPONENT_COLS` (compute/components.py), `STATE_WEIGHTS`
(compute/ccqs.py), and display name map (data_loader.py). The
`_compute_s_demand` function body is preserved as reference but no
longer called. Test files updated from 11→10 expected components.

### Validation

- **140/140 TV reference fields PASS** — CCQS bit-identical for all 10
  canaries (the dropped term was always `0 × z = 0`).
- **11/11 pipeline sanity checks PASS**.
- **51/51 pytest tests PASS** (component-count assertions updated).
- Dashboard cache: 25.51 MB (was 25.52 MB — one column gone).

### Audit finding — 30 of 138 features have ZERO downstream references

Separate audit identified 30 features in `compute/features.py`
`FEATURE_ORDER` that are computed daily but never referenced by any
of the four consumers (components, state, leadership, setup classifier).
Candidates for a follow-up cleanup phase. Examples: `ema_8`, `ema_50`,
`atr_pct`, `realized_vol_20`, `macd_line/signal/histogram`,
`rs_line_spy_value`, `rs_line_qqq_value`, `residual_momentum_63d`,
`residual_momentum_252d`, `bb_upper_20`, `bb_lower_20`, `sharpe_ratio_60d`,
`information_ratio_60d`, `sortino_ratio_60d`, `ulcer_index_60d`,
`base_duration_days`, `high_max_20d`, `range_20d_pct_of_price`. Not
removed in Phase 28 — user decides separately.

## Phase 29 — Unused-feature cleanup + Methodology section trim (2026-05-28)

User approved the Phase 28 audit finding ("30 of 138 features have zero
downstream references"). Phase 29 ships that cleanup plus a separate
trim of the Methodology section text that the user flagged as having
"a ton of extra useless info".

### Change A — FEATURE_ORDER cut from 138 → 108

`compute/features.py` `FEATURE_ORDER` list was reduced by 30 entries.
The 30 removed features are NOT referenced by any downstream consumer
— components.py, state.py, leadership.py, setup_classifier_v2.py,
aggregation.py, build_dashboard_cache.py, data_loader.py, tables.py,
charts.py, or streamlit_app.py. They were being computed and persisted
to `features.parquet` every day without ever being read.

Removed features by category:

| Cat | Removed |
|-----|---------|
| 1   | open, high, low, ema_8, ema_50 |
| 2   | atr_14, atr_pct, realized_vol_20 |
| 3   | atr_x_200 |
| 9   | rs_line_spy_value, rs_line_qqq_value, rs_line_qqq_slope_20d |
| 9b  | residual_momentum_63d, residual_momentum_252d (kept 126d) |
| 14  | macd_line, macd_signal, macd_histogram (kept macd_posture) |
| 15  | bb_upper_20, bb_lower_20, base_duration_days |
| 16  | consecutive_high_intensity |
| 17  | within_basket_z_126d |
| 20  | return_smoothness_60d |
| 21  | ulcer_index_60d |
| 23  | bb_position_21d, sharpe_ratio_60d, information_ratio_60d, sortino_ratio_60d |
| 24  | high_max_20d, range_20d_pct_of_price |

**Implementation safety**: only the `FEATURE_ORDER` storage schema was
modified. All `feats["x"] = ...` computation lines in `compute_features()`
remain intact, so any feature still consumed as an intermediate value
by other features inside `features.py` continues to work (e.g. `ema_8`
still feeds `e_align`, `atr_14` still feeds `atr_x_50`, `bb_upper_20` /
`bb_lower_20` still feed `bb_width_pct_252d`). Removing from
`FEATURE_ORDER` excludes them from the persisted parquet but leaves
the in-memory dict unchanged. This is the safest possible cleanup.

**Storage savings**: 30 columns × ~1.55M rows × snappy-compressed
floats = ~80-100 MB removed from `features.parquet` and from every
downstream parquet read.

### Change B — Methodology section trim in `app/streamlit_app.py`

The "System Health & Methodology" expander's prose was trimmed by
~35% to remove:

- **Inaccurate references to removed components**: the previous text
  mentioned `s_climax` (removed in Phase 6) and `s_demand` (removed
  in Phase 28) as "zero-weight diagnostics in the schema". Post-Phase
  28 this is false — `s_demand` is no longer in the schema, and
  `s_climax` hasn't been since Phase 6.
- **Inaccurate weight claim**: previous text said "`s_momentum` carries
  1% in every state" — actually it's 0.28% max (TRENDING) and 0% in
  CONSOLIDATING / EXHAUSTION / DETERIORATING.
- **Phase audit-trail noise**: previous text name-dropped "Phase 7
  Priority 3a validation, the Priority 2 bootstrap analysis of every
  weight cell, and the Priority 3c finding on confidence-blending" —
  these are internal phase tags meaningless to users.
- **Redundant OOS IC section**: there was a separate "Out-of-Sample
  Information Coefficient by Horizon" heading + paragraph that mostly
  duplicated what the Methodology paragraph already said. Merged into
  one tight description.

The trimmed methodology block now (1) accurately states the 10-component
makeup, (2) explains the per-state weighting / 0-100 mapping / grading
in two short paragraphs, (3) explains component contributions including
the Phase 28 zero-weight-row hiding behavior, (4) explains OOS IC + the
60d/126d horizon strength, and (5) points to SPEC.md for full detail.

### Validation

- **140/140 TradingView reference fields PASS** — CCQS bit-identical
  for all 10 canaries (no consumed features changed).
- **11/11 pipeline sanity checks PASS**.
- **51/51 pytest tests PASS**.
- `features.parquet` now has 108 columns (was 138).
- Dashboard cache 25.51 MB (no change — slim cache already excluded
  most of the removed features).



