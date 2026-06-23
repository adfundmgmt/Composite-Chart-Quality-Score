"""Export the CCQS dashboard feed to static JSON for the web front-end.

Reads the same cache the Streamlit app reads (via app.utils.data_loader) and
writes compact JSON the build-less dashboard fetches. Designed to be run in CI
right after the pipeline, exactly like the Streamlit cache refresh.

Outputs (web/public/data/):
  core.json    — snapshot meta + all stocks + themes + what-changed + OOS
  detail.json  — per-ticker components + key metrics (small)
  history.json — per-ticker CCQS trajectory (date, ccqs, grade)
"""
import json
import logging
import math
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.getLogger("streamlit").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

import pandas as pd  # noqa: E402

from app.utils.data_loader import (  # noqa: E402
    load_dashboard_data, load_themes_data, get_emerging_leaders_today,
    get_newly_broken_today, get_grade_jumps_today, load_components_for_ticker,
    load_key_metrics_for_ticker, load_ticker_history, load_oos_metrics,
)
from compute.display_labels import display_state, display_tier  # noqa: E402
from data.universe import CATEGORIES  # noqa: E402

_B2C = {}
for _cat, _baskets in CATEGORIES.items():
    for _b in _baskets:
        _B2C[_b] = _cat


def gics_sector(theme):
    """Map a CCQS basket (theme) to a GICS-11 sector via its category + keywords."""
    if not theme:
        return "Other"
    cat = _B2C.get(theme, ""); t = theme.lower()
    if cat == "Technology, AI and Internet":
        if any(k in t for k in ["telecom", "media", "communication", "streaming", "advertis", "social", "cable", "wireless carrier", "entertainment"]):
            return "Communication Services"
        return "Information Technology"
    if cat == "Energy, Power, Infrastructure and Materials":
        if any(k in t for k in ["oil", "gas", "lng", "refin", "midstream", "pipeline", "uranium", "coal", "drill", "oilfield", "e&p", " energy"]):
            return "Energy"
        if any(k in t for k in ["power", "grid", "electric", "utilit", "transformer", "switchgear", "nuclear", "backup", "generator", "electrification", "renewable", "solar"]):
            return "Utilities"
        if any(k in t for k in ["steel", "chemical", "material", "mining", "metal", "copper", "gold", "silver", "cement", "lithium", "aluminum", "fertilizer", "rare earth", "mineral"]):
            return "Materials"
        return "Industrials"
    if cat == "Industrials, Defense and Transport":
        return "Industrials"
    if cat == "Healthcare":
        return "Health Care"
    if cat == "Financials and Real Estate":
        if any(k in t for k in ["reit", "real estate", "property", "homebuild"]):
            return "Real Estate"
        return "Financials"
    if cat == "Consumer, Housing and Travel":
        if any(k in t for k in ["staple", "food", "beverage", "grocery", "household", "tobacco", "beauty", "cosmetic"]):
            return "Consumer Staples"
        return "Consumer Discretionary"
    return "Other"

OUT = ROOT / "web" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def num(v, nd=None):
    """NaN/inf-safe number. Returns None for missing; rounds if nd given."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, nd) if nd is not None else f


def s(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return str(v)


def write(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    kb = p.stat().st_size / 1024
    print(f"  wrote {name:14} {kb:8.1f} KB")
    return kb


# ---------------------------------------------------------------------------
df, snap = load_dashboard_data()
themes = load_themes_data()
risers = get_emerging_leaders_today(n=20)
decliners = get_newly_broken_today(n=20)
moves = get_grade_jumps_today(n=20)
oos = load_oos_metrics()

# ---- stocks ----------------------------------------------------------------
stocks = []
for tk, r in df.iterrows():
    stocks.append({
        "t": str(tk),
        "ccqs": num(r.get("ccqs"), 1),
        "grade": s(r.get("grade")),
        "d1": num(r.get("ccqs_change_1d"), 2),
        "d5": num(r.get("ccqs_change_5d"), 2),
        "d21": num(r.get("ccqs_change_21d"), 2),
        "tier": display_tier(r.get("leadership_tier")),
        "tierKey": s(r.get("leadership_tier")),
        "state": display_state(r.get("primary_state")),
        "stateKey": s(r.get("primary_state")),
        "conf": num(r.get("state_confidence"), 2),
        "setup": s(r.get("setup_label")),
        "theme": s(r.get("basket")),
        "sec": gics_sector(s(r.get("basket"))),
        "rs": num(r.get("rs_rating_spy"), 0),
        "ir": num(r.get("information_ratio_252d"), 2),
        "partial": bool(r.get("is_partial", False)),
    })

# ---- themes ----------------------------------------------------------------
theme_rows = []
for _, r in themes.iterrows():
    theme_rows.append({
        "name": s(r.get("basket_name")),
        "ccqs": num(r.get("theme_ccqs"), 1),
        "class": s(r.get("theme_class")),
        "momentum": s(r.get("momentum_class")),
        "pct50": num(r.get("pct_above_50dma"), 0),
        "pct200": num(r.get("pct_above_200dma"), 0),
        "breadth": num(r.get("theme_breadth_score"), 1),
        "rsComposite": num(r.get("theme_rs_composite"), 1),
        "health": num(r.get("theme_health_score"), 1),
        "n": num(r.get("n_constituents"), 0),
        "top": s(r.get("top_member")),
        "members": s(r.get("members")),
    })
theme_rows = [t for t in theme_rows if t["name"] and t["ccqs"] is not None]


def wc_rows(frame, fields):
    out = []
    for tk, r in frame.iterrows():
        row = {"t": str(tk)}
        for key, col, kind in fields:
            v = r.get(col)
            if kind == "num":
                row[key] = num(v, 2)
            elif kind == "tier":
                row[key] = display_tier(v)
            elif kind == "state":
                row[key] = display_state(v)
            else:
                row[key] = s(v)
        out.append(row)
    return out


# ---- per-ticker detail + history + sparkline ------------------------------
detail = {}
spark = {}
hist_dir = OUT / "history"
hist_dir.mkdir(parents=True, exist_ok=True)
tickers = [str(t) for t in df.index]
for i, tk in enumerate(tickers):
    try:
        comp = load_components_for_ticker(tk)
        km = load_key_metrics_for_ticker(tk)
        detail[tk] = {
            "components": [
                {"c": s(c.component), "z": num(c.z_score, 2),
                 "w": num(c.weight, 2), "contrib": num(c.contribution, 3)}
                for c in comp.itertuples()
            ],
            "metrics": [{"m": s(m.metric), "v": s(m.value)} for m in km.itertuples()],
        }
        h = load_ticker_history(tk, period="INCEPTION")
        if not h.empty:
            hd = h[["date", "ccqs", "grade"]].copy() if "date" in h.columns else h.reset_index()
            rows = [{"d": str(row.date)[:10], "v": num(row.ccqs, 1), "g": s(row.grade)}
                    for row in hd.itertuples()][-504:]  # T2: cap (~2y); UI's deepest view uses <=252 points
            (hist_dir / f"{tk}.json").write_text(
                json.dumps(rows, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
            spark[tk] = [r["v"] for r in rows[-24:] if r["v"] is not None]
    except Exception as e:  # noqa
        print(f"  ! {tk}: {e}")
    if (i + 1) % 200 == 0:
        print(f"  …detail {i+1}/{len(tickers)}")

write("detail.json", detail)
n_hist = len(list(hist_dir.glob("*.json")))
print(f"  wrote history/  {n_hist} per-ticker files")

# attach sparkline to each stock; write core LAST so it includes sparks
for st in stocks:
    st["spark"] = spark.get(st["t"], [])

core = {
    "snapshot": snap,
    "nScored": int(len(df)),
    "stocks": stocks,
    "themes": theme_rows,
    "whatChanged": {
        "risers": wc_rows(risers, [("tier", "leadership_tier", "tier"), ("dccqs", "ccqs_change", "num")]),
        "decliners": wc_rows(decliners, [("from", "prev_state", "state"), ("dccqs", "ccqs_change", "num")]),
        "moves": wc_rows(moves, [("move", "grade_move", "str"), ("dccqs", "ccqs_change", "num")]),
    },
    "oos": [
        {"horizon": s(r.get("horizon")), "ic": num(r.get("oos_ic"), 3),
         "t": num(r.get("t_stat"), 2), "hit": num(r.get("hit_rate"), 3)}
        for _, r in oos.iterrows()
    ],
}
print(f"Snapshot {snap}  ·  {len(stocks)} stocks  ·  {len(theme_rows)} themes  ·  {len(spark)} sparks")
write("core.json", core)
print("Done.")
