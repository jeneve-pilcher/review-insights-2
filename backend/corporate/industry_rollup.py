"""Company-wide industry data: headline numbers, a theme-by-location grid, rankings, a theme trend over time and (fine
dining) OpenTable scores by location. Built only from the compact industry summaries saved with each check, and only
from the locations the person is allowed to see."""
from collections import defaultdict
from typing import Dict, List, Optional

from analysis.chart1_sentiment_drift import _parse_dt, _week_start
from analysis.industries import get_pack, public_pack

TREND_THEMES = 5
RANK_THEMES = 6
RANK_TOP = 3


def _wavg(pairs) -> Optional[float]:
    pairs = [(v, w) for v, w in pairs if v is not None and w]
    total = sum(w for _, w in pairs)
    return round(sum(v * w for v, w in pairs) / total, 4) if total else None


def _usable(snap: Optional[dict], pack_id: str) -> Optional[dict]:
    ind = (snap or {}).get("industry")
    return ind if ind and ind.get("pack") == pack_id and ind.get("status") == "ok" else None


def build_company_industry(org: dict, locations: List[dict], snaps: Dict[str, dict], history: Dict[str, List[dict]]) -> dict:
    pack = get_pack(org.get("industry"))
    rows, stale = [], 0
    for loc in locations:
        snap = snaps.get(loc["id"])
        ind = _usable(snap, pack["id"])
        if ind:
            rows.append((loc, ind))
        elif snap and snap.get("industry") and snap["industry"].get("pack") != pack["id"]:
            stale += 1      # checked under a different industry: it refreshes at its next check
    base = {"pack": public_pack(pack), "locations_total": len(locations), "locations_with_data": len(rows), "stale_locations": stale}
    if not rows:
        return {**base, "status": "no_data", "kpis": [], "theme_grid": None, "rankings": [], "theme_trend": {"dates": [], "series": []}, "subratings": None}

    # --- headline numbers: reviews-weighted across locations
    kpis = []
    for spec in pack.get("kpis", []):
        vals, chg = [], []
        for _, ind in rows:
            w = ind["reviews"]
            if spec["kind"] == "theme":
                t = ind["themes"].get(spec["key"], {})
                vals.append((t.get("share"), w)); chg.append((t.get("change"), w))
            else:
                s = (ind.get("sub") or {}).get(spec["key"])
                if s:
                    vals.append((s["avg"], s["n"]))
                    chg.append(((s["recent"] - s["earlier"]) if s["recent"] is not None and s["earlier"] is not None else None, s["n"]))
        value = _wavg(vals)
        kpis.append({"id": spec["id"], "label": spec["label"], "kind": spec["kind"], "unit": "pct" if spec["kind"] == "theme" else "score",
                     "value": value, "change": _wavg(chg), "locations": sum(1 for v, _ in vals if v is not None)})

    # --- theme x location grid
    themes = [{"id": t["id"], "label": t["label"]} for t in pack["themes"]]
    grid_rows = [{"location_id": l["id"], "name": l["name"], "region": l.get("region"), "reviews": ind["reviews"],
                  "shares": {t["id"]: ind["themes"].get(t["id"], {}).get("share") for t in themes},
                  "flags": {t["id"]: ind["themes"].get(t["id"], {}).get("flag") for t in themes}}
                 for l, ind in sorted(rows, key=lambda x: x[0]["name"].lower())]
    company = {t["id"]: _wavg([(ind["themes"].get(t["id"], {}).get("share"), ind["reviews"]) for _, ind in rows]) for t in themes}
    grid = {"themes": themes, "rows": grid_rows, "company": company}

    # --- which locations mention each theme most
    order = sorted([t for t in themes if (company[t["id"]] or 0) > 0], key=lambda t: -company[t["id"]])[:RANK_THEMES]
    rankings = []
    for t in order:
        ranked = sorted([r for r in grid_rows if r["shares"][t["id"]]], key=lambda r: -r["shares"][t["id"]])[:RANK_TOP]
        rankings.append({"theme": t["id"], "label": t["label"], "company": company[t["id"]],
                         "highest": [{"location_id": r["location_id"], "name": r["name"], "share": r["shares"][t["id"]], "flag": r["flags"][t["id"]]} for r in ranked]})

    # --- the company over time: one point per week, each location's latest check that week
    by_week: Dict[str, Dict[str, dict]] = defaultdict(dict)
    for loc in locations:
        for snap in history.get(loc["id"], []):                      # oldest first
            ind = _usable(snap, pack["id"])
            dt = _parse_dt(snap.get("run_at"))
            if ind and dt:
                by_week[_week_start(dt)][loc["id"]] = ind
    weeks = sorted(by_week)
    trend = {"dates": [], "series": []}
    if len(weeks) >= 2:
        top = sorted([t for t in themes if (company[t["id"]] or 0) > 0], key=lambda t: -company[t["id"]])[:TREND_THEMES]
        trend = {"dates": weeks, "series": [{"id": t["id"], "label": t["label"],
                 "values": [_wavg([(i["themes"].get(t["id"], {}).get("share"), i["reviews"]) for i in by_week[w].values()]) for w in weeks]} for t in top]}

    # --- OpenTable scores by location (industries that use them)
    sub = None
    if pack.get("subratings"):
        keys = ["food", "service", "ambience", "value"]
        srows = [{"location_id": l["id"], "name": l["name"], "n": sum(s["n"] for s in ind["sub"].values()) // max(1, len(ind["sub"])),
                  "scores": {k: (ind["sub"].get(k) or {}).get("avg") for k in keys}} for l, ind in rows if ind.get("sub")]
        if srows:
            sub = {"keys": keys, "rows": sorted(srows, key=lambda r: r["name"].lower()),
                   "company": {k: _wavg([(r["scores"][k], r["n"]) for r in srows]) for k in keys}}
    return {**base, "status": "ok", "kpis": kpis, "theme_grid": grid, "rankings": rankings, "theme_trend": trend, "subratings": sub}
