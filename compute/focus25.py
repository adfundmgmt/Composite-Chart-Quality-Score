"""
CCQS V1 — Focus 25 watchlist builder (Phase 32, display-layer only).

Implements the Phase 31 validated configuration (P2: top-25 by CCQS,
4-week rebalance, equal-weight) as a frozen-membership watchlist.

DISPLAY-LAYER ONLY. Consumes existing pipeline outputs (ccqs, state,
leadership, setups, features). Does NOT touch scoring, components,
STATE_WEIGHTS, classifiers, or any methodology. No scored value changes.

Selection rule (fixed, documented):
  - Top 25 names by CCQS score on the most recent pipeline date.
  - Pure rank — no B→A filter, no setup filter, no manual overrides
    (Phase 31 showed overlays-as-filters degrade results: P9/P10).
  - Refresh every 4 weeks (20 trading days). Between refreshes the
    membership is FROZEN; daily score changes update displayed values
    but do not change membership (mirrors P2's rebalance discipline).

B→A flag (Phase 28/29 validated finding — annotation only, never a
filter): TRUE if the name's weekly CCQS grade landed on A from B
within the last 28 calendar days (4 calendar weeks) of the latest
pipeline date. Calendar window (not snapshot-count) so a transition
~4 weeks old is still flagged.

Outputs (written under data/cache/dashboard/):
  - focus25_current.parquet : the 25 constituents + display columns
  - focus25_history.parquet : appended each refresh (live track record)
  - focus25_meta.json       : refresh dates, adds/drops, concentration

Run standalone:
    python -m compute.focus25
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "data" / "cache" / "dashboard"
FULL = ROOT / "data" / "cache"

DEPTH = 25
REFRESH_TRADING_DAYS = 20          # 4 weeks
BA_WINDOW_DAYS = 28                # 4 calendar weeks for the B→A annotation
CONCENTRATION_AMBER = 8            # amber chip when any basket > 8 names
MODEL_WEIGHT = 1.0 / DEPTH         # 4% equal-weight reference framing

CURRENT_PATH = DASH / "focus25_current.parquet"
HISTORY_PATH = DASH / "focus25_history.parquet"
META_PATH = DASH / "focus25_meta.json"


def _read(name: str, slim_first: bool = True) -> pd.DataFrame:
    p = DASH / name
    if slim_first and p.exists():
        return pd.read_parquet(p)
    return pd.read_parquet(FULL / name)


def _ba_flags(ccqs_hist: pd.DataFrame, latest: pd.Timestamp) -> set[str]:
    """Names with a weekly B→A grade landing within BA_WINDOW_DAYS of latest."""
    gl = ccqs_hist.reset_index()[["ticker", "date", "grade"]].dropna()
    gw = gl.pivot(index="date", columns="ticker", values="grade")
    wk_idx = gw.index.to_series().groupby(gw.index.to_period("W")).max().values
    gw = gw.loc[wk_idx]
    ba = (gw.shift(1) == "B") & (gw == "A")
    cutoff = latest - pd.Timedelta(days=BA_WINDOW_DAYS)
    recent = ba.index[ba.index >= cutoff]
    if len(recent) == 0:
        return set()
    flag = ba.loc[recent].any(axis=0)
    return set(flag[flag].index)


def _trading_days_between(dates: pd.DatetimeIndex, a: pd.Timestamp, b: pd.Timestamp) -> int:
    return int(((dates > a) & (dates <= b)).sum())


def build_focus25() -> dict:
    """Build / refresh the Focus 25 watchlist. Returns the meta dict."""
    from data.universe import primary_basket

    ccqs = _read("ccqs.parquet")
    latest = ccqs.index.get_level_values("date").max()
    all_dates = pd.DatetimeIndex(sorted(ccqs.index.get_level_values("date").unique()))

    # latest-snapshot panels
    day = ccqs.xs(latest, level="date")
    state = _read("state.parquet").xs(latest, level="date")
    lead = _read("leadership.parquet").xs(latest, level="date")
    setups = _read("setups.parquet").xs(latest, level="date")
    feats = _read("features.parquet")
    feats_day = feats.xs(latest, level="date") if latest in feats.index.get_level_values("date") else feats.groupby(level="ticker").tail(1).droplevel("date")

    ba_set = _ba_flags(ccqs, latest)

    # ---- Freeze logic ----------------------------------------------------
    prior_hist = pd.read_parquet(HISTORY_PATH) if HISTORY_PATH.exists() else pd.DataFrame()
    last_refresh = None
    prior_members: list[str] = []
    if not prior_hist.empty:
        last_refresh = prior_hist["refresh_date"].max()
        prior_members = prior_hist[prior_hist["refresh_date"] == last_refresh]["ticker"].tolist()

    if last_refresh is None:
        due = True
    else:
        due = _trading_days_between(all_dates, pd.Timestamp(last_refresh), latest) >= REFRESH_TRADING_DAYS

    if due or not prior_members:
        members = list(day["ccqs"].dropna().sort_values(ascending=False).head(DEPTH).index)
        refresh_date = latest
    else:
        # frozen — keep prior members (display current values), drop any that
        # lost a valid score (data exclusion)
        members = [t for t in prior_members if t in day.index and pd.notna(day.loc[t, "ccqs"])]
        refresh_date = pd.Timestamp(last_refresh)

    # ---- Build current table --------------------------------------------
    rows = []
    for tkr in members:
        rows.append({
            "ticker": tkr,
            "ccqs": float(day.loc[tkr, "ccqs"]) if tkr in day.index else np.nan,
            "grade": str(day.loc[tkr, "grade"]) if tkr in day.index else "",
            "leadership_tier": str(lead.loc[tkr, "leadership_tier"]) if tkr in lead.index else "",
            "primary_state": str(state.loc[tkr, "primary_state"]) if tkr in state.index else "",
            "setup": str(setups.loc[tkr, "setup"]) if tkr in setups.index else "",
            "ba_flag": tkr in ba_set,
            "basket": primary_basket(tkr),
            "pct_from_52w_high": float(feats_day.loc[tkr, "pct_from_52w_high"]) if tkr in feats_day.index and "pct_from_52w_high" in feats_day.columns else np.nan,
            "adr_pct_20": float(feats_day.loc[tkr, "adr_pct_20"]) if tkr in feats_day.index and "adr_pct_20" in feats_day.columns else np.nan,
            "model_weight": MODEL_WEIGHT,
        })
    cur = pd.DataFrame(rows).sort_values("ccqs", ascending=False).reset_index(drop=True)
    cur.insert(0, "rank", np.arange(1, len(cur) + 1))
    cur["refresh_date"] = refresh_date
    cur["as_of_date"] = latest

    # ---- Concentration ---------------------------------------------------
    bcounts = cur["basket"].value_counts()
    concentration = {b: int(n) for b, n in bcounts.items()}
    max_basket, max_n = (bcounts.index[0], int(bcounts.iloc[0])) if len(bcounts) else ("", 0)
    amber = max_n > CONCENTRATION_AMBER

    # ---- Adds / drops (only meaningful on a refresh) --------------------
    adds, drops = [], []
    if due and prior_members:
        cur_set, prev_set = set(members), set(prior_members)
        adds = sorted(cur_set - prev_set)
        for t in sorted(prev_set - cur_set):
            # exit reason: rank decay vs data exclusion
            if t in day.index and pd.notna(day.loc[t, "ccqs"]):
                reason = "rank decay"
            else:
                reason = "data exclusion"
            drops.append({"ticker": t, "reason": reason})

    # next refresh date (20 trading days after refresh; calendar estimate if
    # the panel does not yet extend 20 trading days past the refresh)
    fut = all_dates[all_dates > refresh_date]
    if len(fut) >= REFRESH_TRADING_DAYS:
        next_refresh = fut[REFRESH_TRADING_DAYS - 1]
        next_refresh_estimated = False
    else:
        next_refresh = refresh_date + pd.Timedelta(days=28)  # ~4 calendar weeks
        next_refresh_estimated = True

    meta = {
        "refresh_date": str(refresh_date.date()),
        "as_of_date": str(latest.date()),
        "next_refresh_date": str(next_refresh.date()),
        "next_refresh_estimated": bool(next_refresh_estimated),
        "is_refresh_today": bool(due),
        "n_members": len(cur),
        "concentration": concentration,
        "max_basket": max_basket,
        "max_basket_n": max_n,
        "amber_concentration": bool(amber),
        "adds": adds,
        "drops": drops,
        "model_weight_pct": round(MODEL_WEIGHT * 100, 2),
        "ba_flagged": sorted(cur[cur["ba_flag"]]["ticker"].tolist()),
    }

    # ---- Persist ---------------------------------------------------------
    DASH.mkdir(parents=True, exist_ok=True)
    cur.to_parquet(CURRENT_PATH, index=False)

    # append to history only on a genuine refresh (not every daily build)
    if due or prior_hist.empty:
        hist_row = cur[["ticker", "rank", "ccqs", "grade", "basket"]].copy()
        hist_row["refresh_date"] = refresh_date
        hist_row["max_basket"] = max_basket
        hist_row["max_basket_n"] = max_n
        if not prior_hist.empty:
            # avoid duplicate same-date refresh rows
            prior_hist = prior_hist[prior_hist["refresh_date"] != refresh_date]
            combined = pd.concat([prior_hist, hist_row], ignore_index=True)
        else:
            combined = hist_row
        combined.to_parquet(HISTORY_PATH, index=False)

    META_PATH.write_text(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    meta = build_focus25()
    print("Focus 25 built.")
    print(f"  refresh_date : {meta['refresh_date']}  (as-of {meta['as_of_date']})")
    print(f"  next refresh : {meta['next_refresh_date']}  (refresh today: {meta['is_refresh_today']})")
    print(f"  members      : {meta['n_members']}")
    print(f"  B→A flagged  : {meta['ba_flagged']}")
    print(f"  top basket   : {meta['max_basket']} = {meta['max_basket_n']}  (amber: {meta['amber_concentration']})")
    if meta["adds"] or meta["drops"]:
        print(f"  adds         : {meta['adds']}")
        print(f"  drops        : {meta['drops']}")


if __name__ == "__main__":
    main()
