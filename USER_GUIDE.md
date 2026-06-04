# CCQS V1 — User Guide

**How to interpret the output.** Last updated 2026-05-26 (Path C complete, methodology baseline Phase 11E.2).

This guide complements `SPEC.md`. SPEC is the authoritative methodology document; this guide is the user-facing interpretation manual.

---

## TL;DR

CCQS V1 is **NOT** a single continuous "buy/sell" score. It is a **categorical screening + within-category ranking tool**. Use it in two steps:

1. **First, filter by classification** (leadership tier, state, setup) — this is the primary forward-return signal (97.3% of cross-sectional R²).
2. **Then rank within the filtered set by CCQS** — but only in high-quality regimes. In low-quality regimes (WEAK_LAGGARD, DETERIORATING tier), CCQS ranking **inverts** (mean reversion dominates).

The dashboard's reliability chips (green / amber) tell you which regime the current stock is in.

---

## A. What CCQS V1 actually is

CCQS V1 produces three outputs for every (stock, date):

1. **CCQS score** (0–100) — a continuous quality / momentum composite.
2. **Three classification layers**:
   - **State** (6 values): cycle position — TRENDING, PULLBACK, CONSOLIDATING, EXHAUSTION, DETERIORATING, INDETERMINATE.
   - **Setup** (27 values): specific technical pattern detected.
   - **Tier** (10 values): RS-quality classification — ELITE_LEADER, STRONG_LEADER, EMERGING_LEADER, ESTABLISHED_LEADER, STRONG_PERFORMER, NEUTRAL, WEAK_PERFORMER, DETERIORATING, WEAK_LAGGARD, UNCLASSIFIED.
3. **Grade** (S / A / B / C / D) — per-date quantile bucket of CCQS.

**The classifications carry 97.3% of the system's cross-sectional R² at 60d forward returns. CCQS itself carries 2.7%.**

The CCQS score is the within-category ranking key; the classifications are the screening filter.

---

## B. How to use the output (recommended workflow)

1. **Decide your strategy** — quality investing, mean reversion, momentum continuation, etc.
2. **Filter by tier** that matches your strategy:
   - Quality investing → tier in {ELITE_LEADER, STRONG_LEADER, ESTABLISHED_LEADER}
   - Mean reversion → tier in {WEAK_LAGGARD, DETERIORATING}
   - Pattern-driven → no tier filter, use setup filter
3. **Filter by state** if relevant (e.g., TRENDING for continuation, EXHAUSTION for parabolic-bounce, CONSOLIDATING for breakout-watch).
4. **Filter by setup** for a specific chart geometry (e.g., "Tight Base" for narrow consolidation near highs, "Breakout" for range-expansion above the 40d high). Phase 25 vocabulary (13 labels post-Phase-27) is descriptive — see §D.2.
5. **Within the filtered set, rank by CCQS** to surface the top-of-cohort candidates — but only if the dashboard shows the **green "High-quality regime — CCQS reliable" chip**. If it shows the **amber "Low-quality regime — CCQS may invert" chip**, consider ranking ascending instead (lowest CCQS first) or use CCQS only for screening, not ranking.

---

## C. Regime-aware CCQS interpretation

Phase 11D empirically established that CCQS works in some regimes and inverts in others.

### High-quality regimes (CCQS works as expected) — GREEN chip

Top-CCQS-decile minus Bottom-CCQS-decile spread at 60d:

| Tier | Q10 − Q1 spread | Interpretation |
| ---- | ---------------- | -------------- |
| ELITE_LEADER | (small n) | Top tier — trust CCQS |
| STRONG_LEADER | +3.22% | CCQS works |
| ESTABLISHED_LEADER | +5.26% | CCQS works strongly |

In these tiers, the dashboard shows a green chip: "High-quality regime — CCQS reliable". Higher CCQS predicts higher forward returns.

### Middle regimes (CCQS minimal value) — NO chip

| Tier | Q10 − Q1 spread |
| ---- | ---------------- |
| STRONG_PERFORMER | +3.04% (modest) |
| NEUTRAL | −0.48% (flat) |
| WEAK_PERFORMER | +0.56% |

CCQS has small or negligible ranking power in these tiers. No chip is shown.

### Low-quality regimes (CCQS inverts) — AMBER chip

| Tier | Q10 − Q1 spread | Interpretation |
| ---- | ---------------- | -------------- |
| EMERGING_LEADER | −0.82% | Slightly inverted |
| DETERIORATING (tier) | −1.93% | Slightly inverted |
| **WEAK_LAGGARD** | **−9.24%** | Strongly inverted — mean reversion dominates |

In WEAK_LAGGARD and DETERIORATING tiers, the dashboard shows an amber chip: "Low-quality regime — CCQS may invert". The LOWEST CCQS decile actually outperforms the highest by up to 9.24pp at 60d. Mean reversion of extremes dominates the ranking signal.

If you want to do a mean-reversion screen, this is exactly the cohort to look at — but rank ASCENDING by CCQS (lowest first), not descending.

---

## D. Understanding the classification layers

> ℹ️ **Phase 26 display rename note.** Filter expressions, code snippets,
> and the bullets that name specific tiers/states in this section use
> the **internal labels** (ALL_CAPS — what the parquet stores). The
> dashboard renders the **display strings** introduced in Phase 26
> (e.g. EXHAUSTION → "Parabolic", STRONG_PERFORMER → "Steady",
> UNCLASSIFIED/NaN → "No RS Signal"). See the maps in §D.1 / §D.3.

### D.1 State machine (6 values, Phase 11A validated, Phase 26 display rename)

States describe the stock's CURRENT CYCLE POSITION. They do NOT predict forward direction.

**Display string ↔ internal label** (Phase 26 rename; code/parquet
continues to use the ALL_CAPS internal label):

| Display | Internal | Definition | 60d mean return | t vs universe |
| ------- | -------- | ---------- | --------------- | ------------- |
| **Parabolic** | EXHAUSTION | Parabolic / late-stage | **+9.32%** | +20.8 (above) |
| **No Edge** | INDETERMINATE | Transitional / no clear regime | +6.33% | +22.4 (above) |
| **Breaking Down** | DETERIORATING | Structurally damaged | +5.68% | +11.7 (above) |
| *Universe* | — | — | +5.20% | — |
| Trending | TRENDING | Clean uptrend in progress | +4.23% | −22.7 (**BELOW**) |
| Pullback | PULLBACK | Buyable pullback in uptrend | +4.13% | −26.7 (**BELOW**) |
| Consolidating | CONSOLIDATING | Pre-breakout consolidation | +2.70% | −30.6 (**BELOW**) |

**Surprising but empirically true:** Trending and Pullback stocks UNDERPERFORM the universe mean. The "obvious quality" market has already priced them in. Parabolic stocks OUTPERFORM (momentum continuation). The state machine is a CONTEXT classifier, NOT a buy/sell signal.

State persistence is reasonable (72.3% local stability — same state as both yesterday and tomorrow). Breaking Down is the stickiest state (mean 12.9-day run); Pullback is the noisiest active state (mean 3.6-day run).

### D.2 Setup classifier (13 values, Phase 25 redesign + Phase 27 fix/addition)

Setups describe **the present chart state** in 1–2 descriptive words.
First-match-wins along a cascade. Pure descriptive labels — no
predictive language, no gestalt pattern naming (no cup-and-handle /
wedge / H&S). If no condition matches → empty string (silence beats
noise).

| # | Label | What you're seeing on the chart |
| - | ----- | ------------------------------- |
| 1 | New High | Closed at a 252-day high and not extended above the 50-day MA |
| 2 | Breakout | Closed above the prior 40-day high with a range-expansion bar |
| 3 | Failed Breakout | A breakout fired in the last 5 days and price has since closed back below the cleared level |
| 4 | Tight Base | Bullish MA stack, low cross-sectional ADR, sitting within 5% of the 252-day high — quiet, near the highs |
| 5 | Coiling | Bullish stack, 20-day range compressing within the 60-day range, BB-width in bottom 20% of own history — tightening |
| 6 | Shallow Pullback | Bullish stack, 3–10% off the 20-day high, holding the 21EMA, **and not extended above own 80th-pct** (Phase 27 fix) |
| 7 | Deep Pullback | Bullish stack, 10–20% off the 20-day high, holding the 50-day MA, **and not extended above own 80th-pct** (Phase 27 fix) |
| 8 | Extended | Bullish stack and pct-from-50d-MA above the name's own 80th-percentile of history |
| 9 | At Highs | Bullish stack, within 5% of the 252-day high — residual catch-all when no tighter label fits |
| 10 | Basing Low | Within 10% of the 252-day low and low ADR — quiet near a multi-month base |
| 11 | Breakdown | Closed below the prior 40-day low and below the 50-day MA |
| 12 | **Reclaim** | A Breakdown fired in the last 5 days and price has since closed back **above** the breached level — bear-trap / Wyckoff-spring (Phase 27 NEW) |
| 13 | Sideways | 60-day range under 20% of price and position within the middle 50% of the 60-day range |
| – | (blank) | None of the above; suppressed by design |

**How to use the cascade.** Earlier labels trump later ones, so labels
on the same row are mutually exclusive. A name with both "Breakout" and
"At Highs" eligibility is labelled "Breakout" — the more specific
event. "Sideways" is intentionally the residual at the bottom of the
cascade for slow, in-the-middle names.

**What's deliberately NOT a label.**
- *Uptrend / Downtrend.* Too prevalent to be useful — you're already
  using state + CCQS for that signal.
- *Cup-and-Handle / Wedge / H&S / VCP.* These are gestalt patterns;
  Phase 25 decomposes them into measurable constituents instead.
- *Predictive language* ("Failed Setup", "Reversal Pending"). Labels
  describe present state only.

**Coverage snapshot (2026-05-28, universe = 860).** Blank 50.6% /
Sideways 10.3% / Shallow Pullback 8.3% / Basing Low 6.9% / Extended
5.6% / Tight Base 5.5% / Breakdown 4.3% / Failed Breakout 2.3% /
Breakout 2.2% / Coiling 2.0% / Deep Pullback 1.4% / At Highs 0.6% /
New High 0.1%. Blank is the attention-saving residual by design — most
names on most days don't sit at a label-worthy chart event.

**Confidence column.** `setup_confidence = 1.0` for any assigned label,
`0.0` for blank. Preserved as a column for downstream compatibility;
boolean classifier under the hood.

### D.3 Leadership tier (10 values, Phase 11C validated, Phase 11.C.1 + Phase 26 display rename)

Tiers describe CURRENT RS-QUALITY POSITION. The hierarchy is NOT monotonic in forward returns.

**Display string ↔ internal label** (Phase 26 rename; code/parquet
continues to use the ALL_CAPS internal label):

| Display | Internal | Definition | μ 60d | Population |
| ------- | -------- | ---------- | ----- | ---------- |
| Elite Leader | ELITE_LEADER | s_lead ≥ 90 + rs_spy ≥ 95 + 4 confirms | **+15.24%** | 0.18% |
| Strong Leader | STRONG_LEADER | s_lead ≥ 80 + rs_spy ≥ 75 + mtf ≥ 2 | +6.32% | 1.15% |
| Emerging Leader | EMERGING_LEADER | rs_spy 60-85 + slope ≥ 10 + mtf ≥ 2 + qqq ok | +4.68% (UNDER universe) | 5.86% |
| Established Leader | ESTABLISHED_LEADER | rs_spy ≥ 75 + RS Line new high | +6.61% | 1.51% |
| **Steady** | STRONG_PERFORMER | rs_spy ≥ 60 | +7.04% | 24.29% |
| Neutral | NEUTRAL | rs_spy 45-60 | +5.90% | 12.59% |
| Weak Performer | WEAK_PERFORMER | rs_spy 25-45 + slope ≥ −5 | +4.41% (UNDER universe) | 8.05% |
| **Fading Leader** | DETERIORATING | rs_spy < 40 + slope < −5 | +4.82% (UNDER universe) | 17.50% |
| Weak Laggard | WEAK_LAGGARD | rs_spy < 25 + slope < 0 | +7.02% | 2.95% |
| **No RS Signal** | UNCLASSIFIED *or* NaN | Doesn't fit any specific tier (Phase 11.C.1) OR insufficient RS history | varies | 8.63% + ~18% NaN |

**Critical takeaway:** Only Elite Leader has a truly distinctive forward-return edge. All other 8 tiers cluster within ±2.5pp of universe. The tier label tells you what KIND of leadership profile the stock has TODAY — not what will happen next.

---

## E. Specific guidance by use case

### E.1 Quality investing

Filter:
- `leadership_tier ∈ {ELITE_LEADER}` (or include STRONG_LEADER, ESTABLISHED_LEADER for breadth)
- `primary_state ∈ {TRENDING, EXHAUSTION}` (continuation regimes)
- Rank by CCQS descending — trust the green-chip regime

Watch out for: ELITE_LEADER in EXHAUSTION state has the HIGHEST joint forward return (+22% at 60d) — but these stocks are parabolic with high vol. Position sizing matters.

### E.2 Mean reversion

Filter:
- `leadership_tier ∈ {WEAK_LAGGARD, DETERIORATING}`
- `primary_state ∈ {INDETERMINATE, DETERIORATING}` (state-level mean reversion is strongest in these)
- Look at Phase 25 setups: `Basing Low`, `Breakdown`, `Failed Breakout`
  (geometry of the present chart — pair with the state/tier filters
  above for the empirical mean-reversion edge documented in Phase 11D)
- Rank by CCQS **ASCENDING** (lowest first — that's where the strongest mean reversion lives in WEAK_LAGGARD)
- Heed the amber chip — CCQS ranking inverts here

Top-of-the-list 3D cells from Phase 11D (highest empirical 60d mean
returns) were measured against the legacy 27-label setups. Under
Phase 25 vocabulary use the state/tier filter as the primary regime
gate — the descriptive setup label is geometry, not a return-edge
predictor.

### E.3 Momentum continuation

Filter:
- `setup ∈ {Shallow Pullback, Deep Pullback, Tight Base, Coiling}`
  (continuation-friendly geometries under bullish MA stack)
- `leadership_tier ∈ {STRONG_LEADER, ESTABLISHED_LEADER, STRONG_PERFORMER}`
- Rank by CCQS descending

### E.4 Volatility / exhaustion regime

Filter:
- `primary_state == EXHAUSTION`
- `setup ∈ {Extended, New High}` — the closest Phase 25 substitutes for
  parabolic / volume-confirmed exhaustion. Phase 25 setup labels are
  descriptive (no longer state-conditioned), so use `primary_state` as
  the regime gate and let `setup` decompose the chart geometry.
- CCQS ranking works here (+5.87% Q10−Q1 spread); top-decile EXHAUSTION stocks continue their parabolic move on average

### E.5 Pattern screening (specific setups)

Phase 25 setup labels describe present chart state — use them as
geometry filters, not return-edge predictors. Combine with
`primary_state` / `leadership_tier` / CCQS for return-edge.

- *Tight Base / Coiling* — narrow consolidation near highs;
  pre-breakout geometry. Pair with `primary_state == TRENDING` and
  `leadership_tier ∈ {STRONG_PERFORMER, ESTABLISHED_LEADER}`.
- *Breakout / New High* — fresh range expansion or 252d high. Pair with
  rising CCQS deltas (Δ 5d > 0).
- *Shallow Pullback / Deep Pullback* — bullish-stack pullbacks. Pair
  with high CCQS for "pullback in a leader" entries.
- *Basing Low* — quiet near multi-month low; potential reversal zone.
  Pair with leadership-tier reversal signals or rising Δ 5d.
- *Failed Breakout / Breakdown* — outright avoid for longs; pair with
  Top Movers (down) for short candidates.
- *Sideways* — deliberately boring residual; suppresses chart-pull on
  range-bound, middle-of-the-pack names.

---

## F. Known limitations and caveats

| Caveat | Mechanism | Mitigation |
| ------ | --------- | ---------- |
| Mega-cap underperformance | CCQS 60d IC = −0.017 in top dollar-volume quintile (Priority 2b) | "Mega-cap" reliability chip surfaces this |
| High market vol regime | CCQS 60d IC = −0.014 in HIGH-vol regimes (Priority 2b) | "High market vol" banner + chip |
| Defensive baskets | CCQS has negative IC on 10 defensive baskets (Priority 2b) | "Defensive sector" chip |
| EXHAUSTION 20d signal ≈ 0 | Mean reversion at 20d in EXHAUSTION (Priority 2b) | "EXHAUSTION 20d caveat" chip |
| WEAK_LAGGARD CCQS inversion | Mean reversion dominates ranking (Phase 11D) | "Low-quality regime — CCQS may invert" chip |
| DETERIORATING tier CCQS inversion | Same | Same chip |
| NaN-tier stocks (insufficient RS history) | Cannot be tiered; systematic underperformers | Currently visible in dashboard; could be filtered |
| 2020 COVID long horizons | Phase 7 lost ~0.005 of 126d IC in 2020 (documented) | None — historical caveat |
| Short-horizon use (5d / 20d) | Functional but lower-quality | Use for entry timing, not primary signal |

---

## G. Quick reference: dashboard chip interpretation

| Chip | Color | Trigger | Meaning |
| ---- | ----- | ------- | ------- |
| Mega-cap | amber | dollar-volume Q5 | CCQS has documented weak signal in this cohort (Priority 2b) |
| Defensive sector | amber | basket in 10 defensive baskets | CCQS has documented negative IC on these baskets |
| High market vol regime | amber | SPY 20d realized vol ≥ tercile threshold | CCQS turns negative at 60d/126d in this regime |
| EXHAUSTION 20d caveat | blue/info | state == EXHAUSTION | 20d signal is statistically zero; 5d/60d/126d still carry signal |
| **High-quality regime — CCQS reliable** | **green** | tier in {ELITE/STRONG/ESTABLISHED_LEADER} | Phase 11D: Q10−Q1 spread +3–5pp; CCQS ranking trustworthy |
| **Low-quality regime — CCQS may invert** | **amber** | tier in {WEAK_LAGGARD, DETERIORATING} | Phase 11D: Q10−Q1 spread up to −9.24pp; consider mean-reversion framing |

---

## H. What CCQS V1 is NOT

- **NOT a universal continuous score that always predicts forward returns.** It is regime-dependent.
- **NOT a monotonic ranking system across all regimes.** In low-quality tiers it inverts.
- **NOT a standalone buy/sell signal.** It is a within-category ranking key; the categories carry the primary signal.
- **NOT a substitute for fundamental analysis or risk management.** It is a technical signal screening tool only.
- **NOT calibrated for very short horizons.** 5d/20d horizons work but the system is optimized for 60d/126d institutional-quality signal.

---

## I. Further reading

- **`SPEC.md`** — Authoritative methodology document. Contains the full Phase 11 audit trail (11A/11B/11C/11D/11E), all empirical numbers, validation framework, and architectural findings.
- **`CHANGELOG.md`** — Phase-by-phase commit history with status (shipped / rejected / deferred) and key empirical evidence.
- **`README.md`** — Project layout and run instructions.

---

## J. Market-context caution (Phase 17 / 18)

CCQS is a technical ranking system, not a directional predictive model. The
dashboard surfaces a single, optional **market-context caution** at the top
of the page — visible only when conditions historically associated with
weaker cross-sectional signal are present. There is no chip in normal
markets; the caution itself is the signal.

### When the caution is shown

The trigger is a single empirical gate identified in Phase 17:

**SPY drawdown from its trailing 252-day high.**

| Condition | What the dashboard shows |
|-----------|--------------------------|
| SPY within 15% of its 252-day high **and** above its 200-day moving average | **Nothing.** Use the rankings as normal. |
| SPY within 15% of its 252-day high **but** below its 200-day moving average | An informational caution: long-term trend uncertain; apply additional risk management. |
| SPY more than 15% below its 252-day high | A warning caution: rankings remain valid as a screening aid but should not be relied on as a directional signal. |

### Why this gate

Phase 16-17 walk-forward evidence:
- t-statistic 8.74, p < 0.0001 versus 42 candidate regime indicators tested
- Out-of-sample information coefficient differential at the 63-day forward
  horizon: +0.093 (in-regime +0.027 vs off-regime −0.066)
- Walk-forward survival: 0 of 12 cells without the regime filter, 3 of 12
  with it; the validated signal is the long-horizon (≈ 126 trading-day)
  trending-leader screen

### Daily use, regardless of regime

CCQS is best used as a **cross-sectional ranking and screening tool**. Treat
the score as "who looks technically strongest right now" rather than as a
forward-return forecast for any single name. The leadership tier, state,
setup, and components panel are the working artefacts; the score is the
summary.

---

**Path C baseline:** Methodology Lock §3 preserved. CCQS computation,
component weights, grade thresholds, and TradingView reference parity are
unchanged from the Phase 11E.2 baseline. Phase 17 and Phase 18 only adjust
the display layer — what the user sees and how — not the underlying
scoring methodology.
