"""Trends for an industry pack's themes: how often each theme is mentioned, week by week, and whether it is
rising or falling lately.

Simple and explainable by design: a theme counts as mentioned when one of its words or phrases appears in a
written review. A theme is only flagged when there is enough evidence (minimum counts), because a rise from 1
mention to 2 is noise, not a trend."""
import re
from collections import defaultdict
from datetime import timedelta
from typing import List, Optional

from analysis.chart1_sentiment_drift import _parse_dt, _week_start
from analysis.review_utils import text_reviews

MIN_REVIEWS = 15        # written reviews needed before any trend is shown
RECENT_DAYS = 28        # "lately" = the newest four weeks of reviews
MIN_EARLIER = 10        # written reviews needed in the earlier period to compare against
MIN_HITS = 5            # mentions needed in the recent period before flagging a rise
MIN_SHIFT = 0.05        # at least 5 percentage points of change
MIN_GAP = 0.5           # stars of difference before a theme counts as a complaint (or praise) theme


def _pattern(keywords: List[str]):
    return re.compile(r"(?<![a-z])(?:" + "|".join(re.escape(k.lower()) for k in sorted(keywords, key=len, reverse=True)) + r")(?![a-z])")


def _tone(flag: str, gap: Optional[float]) -> str:
    """Whether a rising/falling theme is good or bad news comes from the data: do reviews that mention it rate lower
    (a complaint theme) or higher (a praise theme)? Without enough evidence it is simply noted."""
    if gap is None or abs(gap) < MIN_GAP:
        return "noted"
    hurting = gap < 0
    if flag == "rising":
        return "watch this" if hurting else "good news"
    return "good news" if hurting else "worth a look"


def _share(hits: int, total: int) -> Optional[float]:
    return round(hits / total, 4) if total else None


def build_industry_trends(reviews: List[dict], pack: dict) -> dict:
    items = []
    for r in text_reviews(reviews):
        items.append({"dt": _parse_dt(r.get("datetime_utc")), "rating": r.get("rating"), "text": r["text"].lower()})
    if len(items) < MIN_REVIEWS:
        return {"status": "too_few", "reviews": len(items), "minimum": MIN_REVIEWS}

    dated = [i for i in items if i["dt"] is not None]
    cutoff = max(i["dt"] for i in dated) - timedelta(days=RECENT_DAYS) if dated else None
    recent = [i for i in dated if i["dt"] > cutoff] if cutoff else []
    earlier = [i for i in dated if i["dt"] <= cutoff] if cutoff else []
    can_compare = len(earlier) >= MIN_EARLIER and bool(recent)

    weeks = sorted({_week_start(i["dt"]) for i in dated})
    by_week = defaultdict(list)
    for i in dated:
        by_week[_week_start(i["dt"])].append(i)

    themes, alerts = [], []
    for theme in pack["themes"]:
        pat = _pattern(theme["keywords"])
        for i in items:
            i.setdefault("hit", {})[theme["id"]] = bool(pat.search(i["text"]))
        hit = lambda i, tid=theme["id"]: i["hit"][tid]
        with_t = [i for i in items if hit(i) and i["rating"] is not None]
        without = [i for i in items if not hit(i) and i["rating"] is not None]
        avg = lambda xs: round(sum(i["rating"] for i in xs) / len(xs), 2) if xs else None
        n_hits = sum(1 for i in items if hit(i))
        recent_hits, earlier_hits = sum(1 for i in recent if hit(i)), sum(1 for i in earlier if hit(i))
        recent_share, earlier_share = _share(recent_hits, len(recent)), _share(earlier_hits, len(earlier))
        change = round(recent_share - earlier_share, 4) if (can_compare and recent_share is not None and earlier_share is not None) else None

        flag = None
        if change is not None and change >= MIN_SHIFT and recent_hits >= MIN_HITS:
            flag = "rising"
        elif change is not None and change <= -MIN_SHIFT and earlier_hits >= MIN_HITS:
            flag = "falling"

        rating_with, rating_without = avg(with_t), avg(without)
        gap = round(rating_with - rating_without, 2) if (rating_with is not None and rating_without is not None and len(with_t) >= MIN_HITS) else None
        entry = {
            "id": theme["id"], "label": theme["label"], "mentions": n_hits,
            "share": _share(n_hits, len(items)),
            "series": [_share(sum(1 for i in by_week[w] if hit(i)), len(by_week[w])) for w in weeks],
            "recent_share": recent_share, "earlier_share": earlier_share, "change": change, "flag": flag,
            "rating_with": rating_with, "rating_without": rating_without, "rating_gap": gap,
            "tone": _tone(flag, gap) if flag else None,
        }
        themes.append(entry)

        if flag:
            pct = lambda v: f"{round(v * 100)}%"
            tail = f" Reviews that mention it average {rating_with}★ versus {rating_without}★ for the rest." if gap is not None else ""
            word = "up" if flag == "rising" else "down"
            alerts.append({"theme": theme["id"], "flag": flag, "tone": _tone(flag, gap),
                           "text": f"{theme['label']} is {word}: {pct(recent_share)} of recent written reviews mention it, against {pct(earlier_share)} before.{tail}"})

    # Bad news that is getting worse comes first, then anything else flagged, then the rest by how often it's mentioned.
    order = {"watch this": 0, "worth a look": 1, "good news": 2, "noted": 3}
    themes.sort(key=lambda t: (order.get(t["tone"], 9), -t["mentions"]))
    alerts.sort(key=lambda a: order.get(a["tone"], 9))
    return {"status": "ok", "reviews": len(items), "dated_reviews": len(dated), "weeks": weeks, "themes": themes,
            "alerts": alerts, "recent_days": RECENT_DAYS, "can_compare": can_compare}


_PATTERNS = {}


def themes_in_text(text: str, pack: dict) -> List[str]:
    """The pack's theme ids a piece of text mentions (for tagging a negative review with its industry themes)."""
    key = pack["id"]
    if key not in _PATTERNS:
        _PATTERNS[key] = [(t["id"], _pattern(t["keywords"])) for t in pack["themes"]]
    low = (text or "").lower()
    return [tid for tid, pat in _PATTERNS[key] if pat.search(low)]
