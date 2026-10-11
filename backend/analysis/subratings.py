"""OpenTable's four sub-ratings (food, service, ambience, value) over time. Used by the fine-dining pack: a diner can
love the food and still rate the value low, which the overall star rating hides."""
from collections import defaultdict
from datetime import timedelta
from typing import List

from analysis.chart1_sentiment_drift import _parse_dt, _week_start

KEYS = [("food", "Food"), ("service", "Service"), ("ambience", "Ambience"), ("value", "Value")]
MIN_REVIEWS = 8
RECENT_DAYS = 28


def build_subratings(reviews: List[dict]) -> dict:
    rows = [(_parse_dt(r.get("datetime_utc")), r["sub"]) for r in reviews if r.get("source") == "opentable" and r.get("sub")]
    if not rows:
        return {"status": "no_data", "n": 0}
    if len(rows) < MIN_REVIEWS:
        return {"status": "too_few", "n": len(rows), "minimum": MIN_REVIEWS}

    dated = [(dt, s) for dt, s in rows if dt is not None]
    cutoff = max(dt for dt, _ in dated) - timedelta(days=RECENT_DAYS) if dated else None
    weeks = sorted({_week_start(dt) for dt, _ in dated})
    series = []
    for key, label in KEYS:
        vals = [s[key] for _, s in rows if key in s]
        per_week = defaultdict(list)
        recent, earlier = [], []
        for dt, s in dated:
            if key in s:
                per_week[_week_start(dt)].append(s[key])
                (recent if dt > cutoff else earlier).append(s[key])
        avg = lambda xs: round(sum(xs) / len(xs), 2) if xs else None
        r_avg, e_avg = avg(recent), avg(earlier)
        series.append({
            "key": key, "label": label, "n": len(vals), "average": avg(vals),
            "weekly": [avg(per_week[w]) if per_week[w] else None for w in weeks],
            "recent": r_avg, "earlier": e_avg,
            "change": round(r_avg - e_avg, 2) if (r_avg is not None and e_avg is not None and len(earlier) >= 5 and len(recent) >= 3) else None,
        })
    scored = [s for s in series if s["average"] is not None]
    weakest = min(scored, key=lambda s: s["average"]) if scored else None
    return {"status": "ok", "n": len(rows), "weeks": weeks, "series": series,
            "weakest": {"key": weakest["key"], "label": weakest["label"], "average": weakest["average"]} if weakest else None}
