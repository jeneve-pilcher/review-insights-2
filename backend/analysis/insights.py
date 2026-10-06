import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from dateutil import parser as date_parser

from analysis.chart2_wait_time_heatmap import DAY_ORDER, HOUR_BUCKETS
from analysis.review_utils import has_text
from analysis.sentiment import WAIT_TIME_PHRASES, contains_any_phrase
from analysis.trends import compare_means, terms_for_text

MIN_REVIEWS = 30          # dated reviews needed before any signal is attempted
TOPIC_MIN_MENTIONS = 4    # a topic must appear in at least 4 written reviews
SLOT_MIN_REVIEWS = 5      # a day/hour slot needs at least 5 reviews
MIN_STAR_EFFECT = 0.7     # topic / slot must differ from the rest by this many stars
P_STRICT = 0.01
MAX_SIGNALS = 8

_TYPE_ORDER = {"warning": 0, "opportunity": 1, "positive": 2}


def _parse_dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _mean_var(n: int, s: float, q: float):
    if n <= 0:
        return 0.0, 0.0
    m = s / n
    var = (q - n * m * m) / (n - 1) if n > 1 else 0.0
    return m, max(var, 0.0)


def _welch_p(n1, m1, v1, n2, m2, v2) -> float:
    """Two-sided p-value (normal approximation) for a difference in means."""
    if n1 < 2 or n2 < 2:
        return 1.0
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return 1.0 if m1 == m2 else 0.0
    return math.erfc(abs((m1 - m2) / se) / math.sqrt(2))


def _hour_label(start: int, end: int) -> str:
    def part(h):
        return h % 12 or 12, "am" if h < 12 else "pm"

    (a, sa), (b, sb) = part(start), part(end)
    return f"{a}–{b}{sa}" if sa == sb else f"{a}{sa}–{b}{sb}"


def _signal(kind, title, detail, action, basis, weight=0.0) -> dict:
    return {"type": kind, "title": title, "detail": detail, "action": action,
            "basis": basis, "_weight": weight}


# ---- 1. Momentum: star average + share of 1-2 star ratings (ALL reviews) ----
def _momentum_signals(reviews: List[dict]) -> List[dict]:
    dated = sorted(
        ((dt, r) for r in reviews if (dt := _parse_dt(r["datetime_utc"])) is not None),
        key=lambda x: x[0],
    )
    if len(dated) < 20:
        return []
    first, last = dated[0][0], dated[-1][0]
    span = (last - first).days
    if span < 28:
        return []

    split = last - timedelta(days=max(14, span / 3))
    base = [r for dt, r in dated if dt < split]
    rec = [r for dt, r in dated if dt >= split]
    if len(base) < 10 or len(rec) < 10:
        return []

    out = []

    cmp = compare_means([r["rating"] for r in base], [r["rating"] for r in rec])
    if cmp["significant"] and abs(cmp["delta"]) >= 0.1:
        b, c, n = cmp["baseline_mean"], cmp["recent_mean"], len(base) + len(rec)
        if cmp["delta"] < 0:
            out.append(_signal(
                "warning",
                f"Your star average is slipping: {b:.2f}★ → {c:.2f}★",
                f"Across all {n} reviews (written and star-only), the recent period averages {c:.2f}★ vs "
                f"{b:.2f}★ earlier. Google says review score and count factor into local ranking, so a "
                f"slide can cost visibility.",
                "Open Emerging Topic Trends to see which topics are rising, and check Negative Review Alerts.",
                "all", abs(cmp["delta"]) * n))
        else:
            out.append(_signal(
                "positive",
                f"Your star average is improving: {b:.2f}★ → {c:.2f}★",
                f"Across all {n} reviews (written and star-only), the recent period averages {c:.2f}★ vs "
                f"{b:.2f}★ earlier.",
                "Check Emerging Topic Trends to see what's fading and rising, and keep doing what's working.",
                "all", abs(cmp["delta"]) * n))

    low_b = sum(1 for r in base if r["rating"] <= 2)
    low_r = sum(1 for r in rec if r["rating"] <= 2)
    p_b, p_r = low_b / len(base), low_r / len(rec)
    pooled = (low_b + low_r) / (len(base) + len(rec))
    se = math.sqrt(pooled * (1 - pooled) * (1 / len(base) + 1 / len(rec)))
    if se > 0 and abs(p_r - p_b) >= 0.04:
        p = math.erfc(abs((p_r - p_b) / se) / math.sqrt(2))
        if p < 0.05:
            if p_r > p_b:
                out.append(_signal(
                    "warning",
                    f"1–2★ ratings are growing: {round(100 * p_b)}% → {round(100 * p_r)}% of reviews",
                    f"Counting every rating, including ones with no comment: {low_r} of {len(rec)} recent "
                    f"reviews were 1–2★ vs {low_b} of {len(base)} earlier.",
                    "Read the recent ones in Negative Review Alerts and reply. Star-only ratings have no "
                    "text, so compare their dates with changes in staffing, menu or policy.",
                    "all", abs(p_r - p_b) * len(rec) * 10))
            else:
                out.append(_signal(
                    "positive",
                    f"1–2★ ratings are shrinking: {round(100 * p_b)}% → {round(100 * p_r)}% of reviews",
                    f"{low_r} of {len(rec)} recent reviews were 1–2★ vs {low_b} of {len(base)} earlier.",
                    "Keep an eye on Negative Review Alerts to make sure it stays that way.",
                    "all", abs(p_r - p_b) * len(rec) * 10))
    return out


# ---- 2. Review pace and freshness (ALL reviews) ----------------------------
def _pace_signals(reviews: List[dict]) -> List[dict]:
    dts = sorted(dt for r in reviews if (dt := _parse_dt(r["datetime_utc"])) is not None)
    if not dts:
        return []
    now = _now()
    recent_cut = now - timedelta(days=28)
    recent = sum(1 for d in dts if d >= recent_cut)
    earlier = len(dts) - recent
    earlier_days = (recent_cut - dts[0]).days

    out = []
    if earlier_days >= 28 and earlier:
        er, rr = earlier / (earlier_days / 7), recent / 4
        if er >= 1 and rr <= 0.6 * er:
            out.append(_signal(
                "warning",
                f"New reviews have slowed to about {rr:.1f} per week (from about {er:.1f})",
                "This counts every review, star-only ones included. Google says review count factors into "
                "local ranking, so fewer new reviews means your count grows more slowly.",
                "Make asking for reviews part of your routine, following Google's review policies (no incentives).",
                "all", (er - rr) * 4))
        elif rr >= 1.4 * er and recent >= 4:
            out.append(_signal(
                "positive",
                f"Review pace is picking up: about {rr:.1f} per week (from about {er:.1f})",
                "More reviews means your review count and score are built on more evidence.",
                "Keep whatever is prompting customers to review.",
                "all", (rr - er) * 2))

    days_since = (now - dts[-1]).days
    if days_since >= 30:
        out.append(_signal(
            "warning",
            f"No new reviews in {days_since} days",
            "A long gap means your review count isn't growing and your newest reviews are getting stale.",
            "Check that your Google profile is active and consider a gentle review request to recent customers.",
            "all", days_since / 10))
    return out


# ---- 3. Topics linked to star ratings (written text + stars) ---------------
def _overlap(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def _redundant(c: dict, chosen: dict) -> bool:
    """Same story told twice: nearly the same reviews, or one term contains the other."""
    if _overlap(c["docs"], chosen["docs"]) >= 0.8:
        return True
    a, b = c["term"], chosen["term"]
    return (" " in a) != (" " in b) and (a in b.split() or b in a.split())


def _pick_terms(cands: List[dict], n: int = 2) -> List[dict]:
    """Top terms by impact, preferring phrases, skipping ones that repeat an
    already-chosen term (so 'friendly staff' and 'lovely place' from the same
    reviews don't become two separate signals)."""
    chosen: List[dict] = []
    # Phrases first (they say more than a lone word), then by impact.
    for c in sorted(cands, key=lambda c: (" " not in c["term"], -c["score"], c["term"])):
        if len(chosen) == n:
            break
        if not any(_redundant(c, k) for k in chosen):
            chosen.append(c)
    return chosen


def _topic_signals(reviews: List[dict]) -> List[dict]:
    written = [r for r in reviews if has_text(r)]
    w_count = len(written)
    if w_count < 20:
        return []

    acc = defaultdict(lambda: [0, 0.0, 0.0, []])
    total_s = total_q = 0.0
    for idx, r in enumerate(written):
        x = r["rating"]
        total_s += x
        total_q += x * x
        for term in terms_for_text(r["text"]):
            a = acc[term]
            a[0] += 1
            a[1] += x
            a[2] += x * x
            a[3].append(idx)

    n_all = len(reviews)
    sum_all = sum(r["rating"] for r in reviews)

    negative, positive = [], []
    for term, (n, s, q, docs) in acc.items():
        if n < TOPIC_MIN_MENTIONS or w_count - n < TOPIC_MIN_MENTIONS:
            continue
        m_t, v_t = _mean_var(n, s, q)
        m_o, v_o = _mean_var(w_count - n, total_s - s, total_q - q)
        diff = m_t - m_o
        if abs(diff) < MIN_STAR_EFFECT:
            continue
        # Relative difference isn't enough: 4.0★ vs 5.0★ is not a problem, and
        # 3.5★ vs 2.5★ is not a strength. Require the rating itself to be weak/strong.
        if (diff < 0 and m_t >= 4.0) or (diff > 0 and m_t < 4.0):
            continue
        if _welch_p(n, m_t, v_t, w_count - n, m_o, v_o) >= P_STRICT:
            continue
        item = {"term": term, "n": n, "mean": m_t, "others": m_o, "score": n * abs(diff), "s": s, "docs": set(docs)}
        (negative if diff < 0 else positive).append(item)

    out = []
    for c in _pick_terms(negative):
        # Rough arithmetic on YOUR reviews (all of them, star-only included): what the
        # overall average would be if reviews mentioning this scored like the rest.
        rest_mean = (sum_all - c["s"]) / (n_all - c["n"]) if n_all > c["n"] else c["mean"]
        gain = c["n"] * (rest_mean - c["mean"]) / n_all
        gain_text = (
            f" If reviews mentioning it scored like your other reviews, your overall average (all "
            f"{n_all} reviews) would be about +{gain:.2f}★ higher. That is simple arithmetic on your own "
            f"reviews, not a forecast."
        ) if gain >= 0.01 else ""
        out.append(_signal(
            "warning",
            f"\"{c['term']}\" goes with lower ratings ({c['mean']:.1f}★ vs {c['others']:.1f}★ for other written reviews)",
            f"{c['n']} written reviews mention it and average {c['mean']:.1f}★, vs {c['others']:.1f}★ for "
            f"your other written reviews.{gain_text}",
            "Read examples in Emerging Topic Trends or Negative Review Alerts and fix the process behind it.",
            "both", c["score"] * 2))
    for c in _pick_terms(positive):
        out.append(_signal(
            "opportunity",
            f"\"{c['term']}\" goes with higher ratings ({c['mean']:.1f}★ vs {c['others']:.1f}★ for other written reviews)",
            f"{c['n']} written reviews mention it and average {c['mean']:.1f}★, vs {c['others']:.1f}★ for "
            f"your other written reviews: a strength customers notice.",
            "Feature it in your Google profile description, photos and review replies.",
            "written", c["score"]))
    return out


# ---- 4. Weakest day/hour slot (ALL reviews, plus wait phrases in the text) --
def _timeslot_signal(reviews: List[dict]) -> List[dict]:
    def bucket(hour):
        for start, end in HOUR_BUCKETS:
            if start <= hour < end:
                return start, end
        return None

    cells = defaultdict(list)
    for r in reviews:
        dt = _parse_dt(r["datetime_utc"])
        b = bucket(dt.hour) if dt else None
        if dt and b:
            cells[(DAY_ORDER[dt.weekday()], b)].append(r)

    all_s = sum(r["rating"] for rs in cells.values() for r in rs)
    all_q = sum(r["rating"] ** 2 for rs in cells.values() for r in rs)
    n_all = sum(len(rs) for rs in cells.values())

    best = None
    for (day, (start, end)), rs in cells.items():
        n = len(rs)
        if n < SLOT_MIN_REVIEWS or n_all - n < SLOT_MIN_REVIEWS:
            continue
        s = sum(r["rating"] for r in rs)
        q = sum(r["rating"] ** 2 for r in rs)
        m_c, v_c = _mean_var(n, s, q)
        m_o, v_o = _mean_var(n_all - n, all_s - s, all_q - q)
        diff = m_c - m_o
        if diff > -MIN_STAR_EFFECT or _welch_p(n, m_c, v_c, n_all - n, m_o, v_o) >= P_STRICT:
            continue
        score = n * abs(diff)
        if best is None or score > best["score"]:
            best = {"day": day, "start": start, "end": end, "n": n, "mean": m_c, "rest": m_o,
                    "score": score, "reviews": rs}
    if not best:
        return []

    waits = sum(1 for r in best["reviews"] if has_text(r) and contains_any_phrase(r["text"], WAIT_TIME_PHRASES))
    gain = best["n"] * (best["rest"] - best["mean"]) / n_all
    parts = [
        f"Reviews posted then average {best['mean']:.1f}★ across {best['n']} reviews vs {best['rest']:.1f}★ "
        f"for the rest (written and star-only; based on when reviews were posted, a rough proxy for visit time)."
    ]
    if waits:
        parts.append(f"{waits} of them mention waiting or slow service.")
    if gain >= 0.01:
        parts.append(f"If that slot matched your other reviews, your overall average would be about +{gain:.2f}★ higher.")
    return [_signal(
        "warning",
        f"{best['day']} {_hour_label(best['start'], best['end'])} is your weakest slot ({best['mean']:.1f}★)",
        " ".join(parts),
        "Check staffing and prep for that slot. The Wait-Time Heatmap shows the same pattern.",
        "both" if waits else "all", best["score"] * 2)]


def build_revenue_signals(reviews: List[dict]) -> dict:
    """Takes an already-fetched review list (no scraping happens here).

    Uses EVERY review (written and star-only) for ratings, volume, pace and
    time-of-day, and written reviews for topics. Output is signals worth acting
    on - not a measurement of revenue, which this app cannot see."""
    dated = [r for r in reviews if _parse_dt(r["datetime_utc"]) is not None]
    if len(dated) < MIN_REVIEWS:
        return {
            "status": "insufficient_data",
            "message": (
                f"Revenue signals need at least {MIN_REVIEWS} dated reviews (found {len(dated)}). "
                "Try a longer time window."
            ),
            "signals": [],
        }

    signals = (
        _momentum_signals(reviews)
        + _timeslot_signal(reviews)
        + _topic_signals(reviews)
        + _pace_signals(reviews)
    )
    signals.sort(key=lambda s: (_TYPE_ORDER[s["type"]], -s["_weight"]))
    signals = signals[:MAX_SIGNALS]
    for s in signals:
        del s["_weight"]
    return {"status": "ok", "signals": signals}


def trim_signals_for_preview(result: dict, keep: int = 2) -> dict:
    """Free-tier taste: the top couple of signals, with a count of what's hidden."""
    if not result or result.get("status") != "ok":
        return result
    preview = dict(result)
    preview["hidden"] = max(0, len(result["signals"]) - keep)
    preview["signals"] = result["signals"][:keep]
    preview["preview"] = True
    return preview
