# CCQS V1 — Composite Chart Quality Score

**Daily technical, momentum, and strength screening tool** for L/S discretionary equity analysis.

Production system: scores ~860 stocks/ETFs across ~148 thematic baskets every weekday at 4:05 PM ET (5 min after NYSE close). Live dashboard at **[composite-chart-quality-score.streamlit.app](https://composite-chart-quality-score.streamlit.app/)**.

## What it does

CCQS produces a **0–100 chart-quality score** and **S/A/B/C/D grade** for each name, plus three categorical labels that describe what the chart is doing right now:

| Layer | Labels | Question it answers |
|---|---|---|
| **State** | Trending · Pullback · Consolidating · Parabolic · Breaking Down · No Edge | What's the current trend regime? |
| **Leadership Tier** | Elite Leader → Strong Leader → Established Leader → Emerging Leader → Steady → Neutral → Weak Performer → Fading Leader → Weak Laggard · No RS Signal | What kind of RS profile does it have today? |
| **Setup** | New High · Breakout · Failed Breakout · Tight Base · Coiling · Shallow Pullback · Deep Pullback · Extended · At Highs · Basing Low · Breakdown · Reclaim · Sideways · (blank) | What chart pattern does the recent price action match? |

See [USER_GUIDE.md](USER_GUIDE.md) for the institutional interpretation guide and [SPEC.md](SPEC.md) for the full methodology specification.

---

## Architecture — compute vs display

```
GITHUB ACTIONS (compute layer)             GITHUB REPO (storage)
Triggered: cron 4:05 PM ET Mon-Fri         data/cache/dashboard/*.parquet
   │                                          ▲
   ▼ 1. loader        → fetch yfinance        │ commit refreshed cache to main
     2. data_quality  → firewall              │
     3. features      → 108 features          │
     4. standardization → z-scores            │
     5. pipeline      → CCQS / state /        │
                        leadership / setup    │
     6. build_dashboard_cache                 │
     7. Hard-gate tests (140/140 TV parity,   │
                          11/11 sanity, 91/91 pytest)
     8. git commit + push  ────────────────────┘

STREAMLIT CLOUD (display layer ONLY)
Entry: app/streamlit_app.py
  • Reads parquets from data/cache/dashboard/
  • Renders tables, sidebar filters, stock detail panel
  • Does NOT compute CCQS / state / leadership / setups
  • Does NOT touch yfinance
```

**Compute happens on GitHub Actions, not Streamlit.** Streamlit is purely the display layer reading committed parquets. If Streamlit is down, the next morning's compute still runs on schedule; scores just won't be viewable until it's back.

---

## Setup (local development)

Requires Python 3.13.

```bash
git clone https://github.com/schhabra2003/Composite-Chart-Quality-Score.git
cd Composite-Chart-Quality-Score
python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Daily pipeline (manual run)

```bash
python -m compute.loader              # 1. fetch OHLCV from yfinance
python -m compute.data_quality        # 2. quality firewall
python -m compute.features            # 3. derive 108 features
python -m compute.standardization     # 4. cross-sectional z-scores
python -m compute.pipeline            # 5. CCQS / state / leadership / setup
python -m compute.build_dashboard_cache  # 6. slim parquets for Streamlit
```

Or run the dashboard locally against the cached data:

```bash
streamlit run app/streamlit_app.py
```

---

## Quality gates (auto-run by CI before any cache commit)

| Gate | What it catches |
|---|---|
| **TradingView reference parity** — 140 pinned field checks across 10 large-cap canaries | Methodology drift |
| **Pipeline integrity** — 11 sanity checks (CCQS bounded, state probs sum to 1, no inf values, etc.) | Computation errors |
| **Universe coverage** — yfinance fetched ≥95% of declared universe | yfinance regressions |
| **Cache freshness** — latest date within 7 days | Stale data |
| **IC baseline** — per-date IC vs Phase 11 baseline within tolerance | Forward-return regressions |

If any hard-gate fails, the workflow fails and no new cache is committed. Yesterday's good cache stays in place.

---

## Project structure

```
CCQS_V1/
├── .github/workflows/
│   └── pipeline.yml             # Daily cron + hard-gate tests
├── .streamlit/config.toml       # Light theme config (Streamlit Cloud)
├── app/
│   ├── streamlit_app.py         # Dashboard entry point
│   └── utils/                   # Tables / colors / data loader
├── compute/
│   ├── loader.py                # yfinance batch fetcher
│   ├── data_quality.py          # Quality firewall
│   ├── features.py              # 108 standardized features
│   ├── standardization.py       # Per-date robust z-scores
│   ├── components.py            # 10 composite components
│   ├── state.py                 # 6-state probabilistic classifier
│   ├── ccqs.py                  # Composite scoring + grading
│   ├── setup_classifier.py      # Legacy 27-label (preserved, not called)
│   ├── setup_classifier_v2.py   # Current 13-label cascade (Phase 25 + 27)
│   ├── leadership.py            # 10-tier leadership classifier
│   ├── aggregation.py           # Theme-level rollup
│   ├── display_labels.py        # Phase 26 internal→display translations
│   └── build_dashboard_cache.py # Slim parquets for Streamlit
├── data/
│   ├── universe.py              # Canonical universe (~892 tickers)
│   ├── manual_overrides.yaml    # Per-ticker overrides
│   └── cache/                   # Daily refresh artifacts
├── tests/                       # 91 pytest tests + TV parity
├── CHANGELOG.md                 # Phase-by-phase deployment log
├── SPEC.md                      # Full methodology specification
├── USER_GUIDE.md                # Institutional interpretation guide
└── README.md                    # This file
```

---

## Phase status

System is **fully deployed and live in production**. Phase numbering reflects iterative methodology refinements; see CHANGELOG.md for the full audit trail.

| Phase | Description | Status |
|---|---|---|
| 1–22 | Foundation, methodology, deployment, UI cleanup | ✅ Shipped |
| 23 | Add major recent IPOs to universe | ✅ |
| 24 | Graceful CCQS degradation for partial-history names | ✅ |
| 25 | Setup label redesign (27-label → 12-cascade; Phase 27 made it 13) | ✅ |
| 26 | State + Leadership Tier display rename + cron move | ✅ |
| 27 | Setup cascade bug fix + "Reclaim" label (13th) | ✅ |
| 28 | s_demand permanently removed + 0-weight rows hidden | ✅ |
| 29 | 30 unused features dropped + Methodology section trim | ✅ |
| 30 | "Magnificent Seven" CORE basket added; AAPL moved out of Hyperscalers | ✅ |
| 30.1–30.4 | Aggregation source fix + Themes / Basket-Peers display follow-ups | ✅ |
| 31 | Top-N watchlist configuration validated (equal-weight beat score-weighting & inverse-vol) — research only, **no methodology change** | ✅ |
| 32 | Internal watchlist prototyped on the dashboard (display-layer only) | ↩︎ Reverted by 32R |
| 32R | Watchlist reverted to **private local-only tooling**; no public dashboard surface. Methodology bit-identical throughout | ✅ |

> **Methodology is locked at the Phase 11E.2 baseline and unchanged through Phase 32R** — every phase since has touched only the universe, display layer, or private tooling, never the scoring. See `CHANGELOG.md` for the full audit trail and `SPEC.md` for the methodology.

---

## Data

- **Source:** yfinance (no API key required)
- **Cadence:** Daily refresh, 4:05 PM ET Mon–Fri
- **Lookback:** ~7 years (1.55M ticker-days)
- **Benchmarks:** SPY, QQQ
- **Universe:** ~892 tickers across ~148 themes; defined in `data/universe.py`

---

## Use case

- **User:** ADFM L/S discretionary equity analyst
- **Workflow:** Macro models say risk-on → use CCQS to find best equity setups
- **Time horizons:** Days to weeks to months
- **Tool role:** Screening + ranking; analyst judgment overlays
- **NOT:** Predictive signal, position sizer, or systematic execution

---

## Live dashboard

**[composite-chart-quality-score.streamlit.app](https://composite-chart-quality-score.streamlit.app/)**

Refreshed daily by GitHub Actions at 4:05 PM ET (5 min after NYSE close).
