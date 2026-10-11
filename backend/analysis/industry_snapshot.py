"""A small, storable summary of one location's industry trends, saved with every check so the company pages can
compare locations and chart the company over time without re-reading any reviews."""
from typing import List

from analysis.industry_trends import build_industry_trends
from analysis.subratings import build_subratings

_PRIORITY = {"watch this": 0, "worth a look": 1, "good news": 2, "noted": 3}


def compact_industry(reviews: List[dict], pack: dict) -> dict:
    trends = build_industry_trends(reviews, pack)
    out = {"pack": pack["id"], "status": trends["status"], "reviews": trends.get("reviews", 0), "themes": {}, "sub": None, "top": None}
    if trends["status"] != "ok":
        return out
    flagged = []
    for t in trends["themes"]:
        out["themes"][t["id"]] = {k: t[k] for k in ("share", "recent_share", "earlier_share", "change", "flag", "tone", "mentions", "rating_gap")}
        if t["flag"]:
            flagged.append(t)
    if flagged:
        top = sorted(flagged, key=lambda t: (_PRIORITY.get(t["tone"], 9), -t["mentions"]))[0]
        out["top"] = {"id": top["id"], "label": top["label"], "flag": top["flag"], "tone": top["tone"]}
    if pack.get("subratings"):
        sub = build_subratings(reviews)
        if sub["status"] == "ok":
            out["sub"] = {s["key"]: {"avg": s["average"], "recent": s["recent"], "earlier": s["earlier"], "n": s["n"]} for s in sub["series"]}
    return out
