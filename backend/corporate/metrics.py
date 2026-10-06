"""Turns pulled reviews into a per-location snapshot, then compares and rolls up locations."""
from collections import defaultdict
from statistics import median
from typing import Dict, List, Optional

from analysis.chart1_sentiment_drift import build_sentiment_drift
from analysis.chart2_wait_time_heatmap import build_wait_summary
from analysis.insights import build_revenue_signals
from analysis.negative_reviews import negative_summary
from analysis.review_utils import text_reviews
from analysis.trends import build_trends

# ---------------------------------------------------------------- snapshot
def _avg(rs: List[dict]) -> Optional[float]:
    return round(sum(r["rating"] for r in rs) / len(rs), 2) if rs else None


def compute_snapshot(reviews_by_source: Dict[str, List[dict]], *, months: int, fresh: Dict[str, int],
                     notes: List[str], prev_avg_rating: Optional[float]) -> dict:
    """A compact, comparable summary of one location's reviews (stored over time)."""
    reviews = [r for rs in reviews_by_source.values() for r in rs]
    n = len(reviews)

    drift = build_sentiment_drift(reviews)
    velocity = drift.get("velocity") or {}
    nlp = drift.get("nlp") or {}
    trends = build_trends(reviews)
    signals = build_revenue_signals(reviews)
    wait = build_wait_summary(reviews)
    negatives = negative_summary(reviews)
    low = sum(1 for r in reviews if r["rating"] <= 2)

    rising = []
    if trends.get("status") == "ok":
        rising = [{"term": t["term"], "recent_pct": t["recent_pct"], "baseline_pct": t["baseline_pct"],
                   "tone": t["tone"], "avg_rating": t["avg_rating"]} for t in trends["rising"][:5]]
    top_signals = []
    if signals.get("status") == "ok":
        top_signals = [{"type": s["type"], "title": s["title"]} for s in signals["signals"][:5]]

    return {
        "months": months,
        "reviews_total": n,
        "reviews_google": len(reviews_by_source.get("google", [])),
        "reviews_yelp": len(reviews_by_source.get("yelp", [])),
        "reviews_text": len(text_reviews(reviews)),
        "avg_rating": _avg(reviews),
        "avg_rating_google": _avg(reviews_by_source.get("google", [])),
        "avg_rating_yelp": _avg(reviews_by_source["yelp"]) if "yelp" in reviews_by_source else None,
        "prev_avg_rating": prev_avg_rating,
        "low_star_pct": round(100 * low / n, 1) if n else None,
        "recent_per_week": velocity.get("recent_per_week"),
        "earlier_per_week": velocity.get("earlier_per_week"),
        "days_since_last": velocity.get("days_since_last"),
        "avg_sentiment": nlp.get("overall_sentiment"),
        "wait_share_pct": wait["share_pct"] if wait and wait.get("total_reviews") else None,
        "negative_count": negatives["count"],
        "rising_topics": rising,
        "signals": top_signals,
        "notes": notes,
        "fresh_reviews": sum(fresh.values()),
    }


# -------------------------------------------------------------- benchmarks
METRICS = {
    "avg_rating":      {"label": "Average rating",   "higher_is_better": True},
    "low_star_pct":    {"label": "1–2★ share",       "higher_is_better": False},
    "recent_per_week": {"label": "Reviews per week", "higher_is_better": True},
    "avg_sentiment":   {"label": "Review tone",      "higher_is_better": True},
    "wait_share_pct":  {"label": "Mentions waiting", "higher_is_better": False},
}
MIN_PEERS = 3


def _ranks(values: Dict[str, float], higher_is_better: bool) -> Dict[str, int]:
    ranks, prev, rank = {}, None, 0
    for i, (lid, v) in enumerate(sorted(values.items(), key=lambda kv: kv[1], reverse=higher_is_better), start=1):
        if v != prev:
            rank, prev = i, v
        ranks[lid] = rank          # ties share a rank
    return ranks


def build_benchmarks(locations: List[dict], snapshots: Dict[str, dict], group_by: str = "all") -> dict:
    """Ranks each location against its peers (everyone, or the same brand / region)."""
    def group_key(loc):
        if group_by == "brand":
            return loc.get("brand") or "(no brand)"
        if group_by == "region":
            return loc.get("region") or "(no region)"
        return "All locations"

    with_data = [l for l in locations if l["id"] in snapshots]
    groups: Dict[str, List[dict]] = defaultdict(list)
    for l in with_data:
        groups[group_key(l)].append(l)

    rows, group_info = [], {}
    for key, members in groups.items():
        n = len(members)
        rankable = n >= MIN_PEERS
        info = {"count": n, "rankable": rankable, "median": {}}
        per_metric = {}
        for metric, cfg in METRICS.items():
            vals = {l["id"]: snapshots[l["id"]][metric] for l in members if snapshots[l["id"]].get(metric) is not None}
            if not vals:
                continue
            med = round(median(vals.values()), 2)
            info["median"][metric] = med
            per_metric[metric] = {
                "median": med, "of": len(vals),
                "ranks": _ranks(vals, cfg["higher_is_better"]) if rankable and len(vals) >= MIN_PEERS else {},
                "vals": vals,
            }
        group_info[key] = info

        for l in members:
            metrics_out, flags = {}, []
            for metric, pm in per_metric.items():
                v = pm["vals"].get(l["id"])
                if v is None:
                    continue
                rank = pm["ranks"].get(l["id"])
                of = pm["of"]
                metrics_out[metric] = {
                    "value": v, "median": pm["median"], "vs_median": round(v - pm["median"], 2),
                    "rank": rank, "of": of,
                    "percentile": round(100 * (of - rank) / (of - 1)) if rank and of > 1 else None,
                }
            if rankable:
                m = metrics_out
                if "avg_rating" in m and m["avg_rating"]["rank"]:
                    r = m["avg_rating"]
                    if r["rank"] == r["of"] and r["vs_median"] < 0:
                        flags.append(f"Lowest rating in its group ({r['value']}★ vs median {r['median']}★)")
                    elif r["vs_median"] <= -0.25:
                        flags.append(f"Rating {r['value']}★ is {abs(r['vs_median'])}★ below the group median ({r['median']}★)")
                if "low_star_pct" in m and m["low_star_pct"]["value"] >= max(8, 2 * m["low_star_pct"]["median"]):
                    r = m["low_star_pct"]
                    flags.append(f"1–2★ share is {r['value']}% (group median {r['median']}%)")
                if "recent_per_week" in m and m["recent_per_week"]["median"] >= 1 \
                        and m["recent_per_week"]["value"] <= 0.5 * m["recent_per_week"]["median"]:
                    r = m["recent_per_week"]
                    flags.append(f"Review pace is {r['value']}/week, half the group median ({r['median']})")
                if "wait_share_pct" in m and m["wait_share_pct"]["value"] >= max(10, 2 * m["wait_share_pct"]["median"]):
                    r = m["wait_share_pct"]
                    flags.append(f"Waiting complaints are high: {r['value']}% of written reviews (median {r['median']}%)")
            rows.append({
                "location_id": l["id"], "name": l["name"], "brand": l.get("brand"), "region": l.get("region"),
                "group": key, "run_at": snapshots[l["id"]].get("run_at"),
                "metrics": metrics_out, "flags": flags,
            })

    rows.sort(key=lambda r: (-len(r["flags"]),
                             r["metrics"].get("avg_rating", {}).get("value", 99), r["name"].lower()))
    return {
        "group_by": group_by,
        "groups": group_info,
        "rows": rows,
        "metric_labels": {k: v["label"] for k, v in METRICS.items()},
        "min_peers": MIN_PEERS,
        "awaiting_first_run": [l["name"] for l in locations if l["id"] not in snapshots],
    }


# ---------------------------------------------------------------- overview
def _weighted(rows: List[dict], field: str) -> Optional[float]:
    num = sum(r[field] * r["reviews_total"] for r in rows if r.get(field) is not None and r.get("reviews_total"))
    den = sum(r["reviews_total"] for r in rows if r.get(field) is not None and r.get("reviews_total"))
    return round(num / den, 2) if den else None


def build_overview(locations: List[dict], snapshots: Dict[str, dict], open_alerts: Dict[str, int]) -> dict:
    """Company-wide roll-up: totals, groups by brand/region, who needs attention, shared problems."""
    data = [(l, snapshots[l["id"]]) for l in locations if l["id"] in snapshots]
    snaps = [s for _, s in data]
    org_avg = _weighted(snaps, "avg_rating")

    totals = {
        "locations": len(locations),
        "with_data": len(data),
        "awaiting_first_run": len(locations) - len(data),
        "reviews_total": sum(s.get("reviews_total") or 0 for s in snaps),
        "avg_rating": org_avg,
        "low_star_pct": _weighted(snaps, "low_star_pct"),
        "open_alerts": sum(open_alerts.values()),
    }

    def group(field):
        buckets: Dict[str, list] = defaultdict(list)
        for l, s in data:
            buckets[l.get(field) or f"(no {field})"].append((l, s))
        out = []
        for key, items in buckets.items():
            ss = [s for _, s in items]
            out.append({"key": key, "locations": len(items),
                        "reviews": sum(s.get("reviews_total") or 0 for s in ss),
                        "avg_rating": _weighted(ss, "avg_rating"),
                        "low_star_pct": _weighted(ss, "low_star_pct"),
                        "open_alerts": sum(open_alerts.get(l["id"], 0) for l, _ in items)})
        return sorted(out, key=lambda g: (g["avg_rating"] is None, g["avg_rating"] or 0))

    attention = []
    for l, s in data:
        reasons, score = [], 0
        change = None
        if s.get("avg_rating") is not None and s.get("prev_avg_rating") is not None:
            change = round(s["avg_rating"] - s["prev_avg_rating"], 2)
            if change <= -0.15:
                reasons.append(f"Rating fell {abs(change)}★ since the last check ({s['prev_avg_rating']}★ → {s['avg_rating']}★)")
                score += 3 if change <= -0.3 else 2
        n_open = open_alerts.get(l["id"], 0)
        if n_open >= 3:
            reasons.append(f"{n_open} open negative reviews")
            score += 2
        if (s.get("days_since_last") or 0) >= 30:
            reasons.append(f"No new reviews in {s['days_since_last']} days")
            score += 1
        if (s.get("low_star_pct") or 0) >= 15:
            reasons.append(f"{s['low_star_pct']}% of reviews are 1–2★")
            score += 2
        if org_avg is not None and s.get("avg_rating") is not None and s["avg_rating"] <= org_avg - 0.4:
            reasons.append(f"Rating {s['avg_rating']}★ is well below the company average ({org_avg}★)")
            score += 2
        if reasons:
            attention.append({"location_id": l["id"], "name": l["name"], "brand": l.get("brand"),
                              "region": l.get("region"), "score": score, "reasons": reasons,
                              "avg_rating": s.get("avg_rating"), "rating_change": change})
    attention.sort(key=lambda a: (-a["score"], a["name"].lower()))

    changes = []
    for l, s in data:
        if s.get("avg_rating") is not None and s.get("prev_avg_rating") is not None:
            changes.append({"location_id": l["id"], "name": l["name"],
                            "change": round(s["avg_rating"] - s["prev_avg_rating"], 2), "avg_rating": s["avg_rating"]})
    drops = sorted((c for c in changes if c["change"] < 0), key=lambda c: c["change"])[:5]
    gains = sorted((c for c in changes if c["change"] > 0), key=lambda c: -c["change"])[:5]

    # Problems showing up at several locations at once: the corporate-level signal.
    shared: Dict[str, list] = defaultdict(list)
    for l, s in data:
        for t in s.get("rising_topics") or []:
            if t.get("tone") == "negative":
                shared[t["term"]].append(l["name"])
    shared_topics = sorted(({"term": term, "locations": len(names), "names": sorted(names)[:5]}
                            for term, names in shared.items()), key=lambda t: (-t["locations"], t["term"]))[:8]

    return {"totals": totals, "by_brand": group("brand"), "by_region": group("region"),
            "attention": attention[:10], "drops": drops, "gains": gains, "shared_topics": shared_topics}
