import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import nltk
from dateutil import parser as date_parser
from nltk.corpus import stopwords

from analysis.pii import redact_pii
from analysis.review_utils import has_text
from analysis.sentiment import score_sentiment

nltk.download("stopwords", quiet=True)

# Negators are kept (not treated as stopwords) so "not friendly" and
# "never clean" survive as phrases instead of collapsing into "friendly".
NEGATORS = {
    "not", "never", "nor", "cannot", "don't", "didn't", "doesn't", "wasn't",
    "weren't", "isn't", "aren't", "won't", "wouldn't", "couldn't",
    "shouldn't", "hasn't", "haven't", "hadn't",
}

_EXTRA_STOP = {
    "would", "could", "also", "really", "just", "even", "much", "went",
    "got", "get", "one", "us", "ive", "im",
}
_STOP = (set(stopwords.words("english")) | _EXTRA_STOP) - NEGATORS

# Too generic to be useful as a standalone one-word topic (they still count
# inside two-word phrases, e.g. "great service").
_GENERIC_UNIGRAMS = {
    "place", "good", "great", "nice", "love", "like", "back", "time", "food",
    "always", "best", "amazing", "awesome", "excellent", "recommend",
}

MIN_REVIEWS_PER_WINDOW = 5
MIN_SPAN_DAYS = 14
MIN_TERM_DOCS = 3          # a topic must appear in at least 3 reviews
G2_THRESHOLD = 6.63        # chi-square, 1 degree of freedom, p < 0.01
TOP_N = 8


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


def _tokens(sentence: str) -> List[str]:
    words = [w.strip("'") for w in re.findall(r"[a-z][a-z']*", sentence.lower())]
    return [w for w in words if len(w) >= 3 and (w in NEGATORS or w not in _STOP)]


def _review_terms(text: str) -> Dict[str, tuple]:
    """term -> (sentence it appeared in, that sentence's VADER score). One entry
    per term per review, so a term repeated in one review counts once."""
    found: Dict[str, tuple] = {}
    # Emails and links would otherwise be split into junk "topics" like "bob com".
    text = re.sub(r"\S+@\S+|https?://\S+|www\.\S+", " ", text)
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        sentence = sentence.strip()
        if not sentence:
            continue
        toks = _tokens(sentence)
        if not toks:
            continue
        score = score_sentiment(sentence)
        terms = set()
        for t in toks:
            if t not in NEGATORS and t not in _GENERIC_UNIGRAMS:
                terms.add(t)
        for a, b in zip(toks, toks[1:]):
            terms.add(f"{a} {b}")
        for t in terms:
            found.setdefault(t, (sentence, score))
    return found


def _g2(a: int, b: int, c: int, d: int) -> float:
    """Dunning log-likelihood ratio for a 2x2 table.
    a/b = recent reviews with/without the term; c/d = earlier with/without."""
    n = a + b + c + d
    row1, row2, col1, col2 = a + b, c + d, a + c, b + d

    def part(o, e):
        return 0.0 if o == 0 else o * math.log(o / e)

    return 2 * (
        part(a, row1 * col1 / n) + part(b, row1 * col2 / n)
        + part(c, row2 * col1 / n) + part(d, row2 * col2 / n)
    )


def _collect(window: List[dict]):
    df: Counter = Counter()
    rating_sum: Dict[str, float] = defaultdict(float)
    sent_sum: Dict[str, float] = defaultdict(float)
    example: Dict[str, str] = {}
    for r in window:  # window is in date order, so later examples overwrite earlier
        for term, (sentence, score) in _review_terms(r["text"]).items():
            df[term] += 1
            rating_sum[term] += r["rating"]
            sent_sum[term] += score
            example[term] = sentence
    return df, rating_sum, sent_sum, example


def _tone(avg_rating: float) -> str:
    if avg_rating <= 2.5:
        return "negative"
    if avg_rating >= 4.0:
        return "positive"
    return "mixed"


def _compare(baseline: List[float], recent: List[float]) -> dict:
    """Welch's t-test with a normal approximation for the p-value."""
    def stats(xs):
        n = len(xs)
        m = sum(xs) / n
        v = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
        return n, m, v

    n1, m1, v1 = stats(baseline)
    n2, m2, v2 = stats(recent)
    se = math.sqrt(v1 / n1 + v2 / n2)
    p = math.erfc(abs((m2 - m1) / se) / math.sqrt(2)) if se > 0 else 1.0
    significant = p < 0.05
    delta = m2 - m1
    direction = "flat" if not significant else ("up" if delta > 0 else "down")
    return {
        "baseline_mean": round(m1, 3),
        "recent_mean": round(m2, 3),
        "delta": round(delta, 3),
        "p_value": round(p, 4),
        "significant": significant,
        "direction": direction,
    }


def _example(sentence: str) -> str:
    text = redact_pii(sentence.strip())
    return text if len(text) <= 180 else text[:177] + "…"


def _pick(candidates: List[dict]) -> List[dict]:
    """Prefer two-word phrases; drop a single word if a chosen phrase already
    contains it (so we show 'long wait', not 'long', 'wait' and 'long wait')."""
    def order(c):
        return (-c["score"], -max(c["recent_count"], c["baseline_count"]), c["term"])

    candidates = sorted(candidates, key=order)
    phrases = [c for c in candidates if " " in c["term"]][:TOP_N]
    covered = {w for c in phrases for w in c["term"].split()}
    singles = [c for c in candidates if " " not in c["term"] and c["term"] not in covered]
    return sorted(phrases + singles[:TOP_N], key=order)[:TOP_N]


def build_trends(reviews: List[dict]) -> dict:
    """Takes an already-fetched review list (no scraping happens here)."""
    dated_all = []
    for r in reviews:
        dt = _parse_dt(r.get("datetime_utc"))
        if dt is not None:
            dated_all.append((dt, r))
    dated_all.sort(key=lambda x: x[0])
    # Topics and language tone need written text; the star rating uses every review.
    dated = [(dt, r) for dt, r in dated_all if has_text(r)]

    if len(dated) < 2 * MIN_REVIEWS_PER_WINDOW:
        return {
            "status": "insufficient_data",
            "message": (
                f"Trend detection needs at least {2 * MIN_REVIEWS_PER_WINDOW} dated reviews with text "
                f"(found {len(dated)}). Try a longer time window."
            ),
        }

    first, last = dated[0][0], dated[-1][0]
    span_days = (last - first).days
    if span_days < MIN_SPAN_DAYS:
        return {
            "status": "insufficient_data",
            "message": "These reviews span under 4 weeks, which is too short to compare periods. Try a longer time window.",
        }

    # Compare the most recent third of the span against everything before it.
    split = last - timedelta(days=max(14, span_days / 3))
    baseline = [r for dt, r in dated if dt < split]
    recent = [r for dt, r in dated if dt >= split]

    if len(baseline) < MIN_REVIEWS_PER_WINDOW or len(recent) < MIN_REVIEWS_PER_WINDOW:
        return {
            "status": "insufficient_data",
            "message": (
                f"Need at least {MIN_REVIEWS_PER_WINDOW} reviews in both the recent period "
                f"({len(recent)} found) and the earlier period ({len(baseline)} found). "
                "Try a longer time window."
            ),
        }

    n_r, n_b = len(recent), len(baseline)
    df_r, rating_r, sent_r, ex_r = _collect(recent)
    df_b, rating_b, sent_b, ex_b = _collect(baseline)

    rising_c, fading_c = [], []
    for term in set(df_r) | set(df_b):
        a, c = df_r.get(term, 0), df_b.get(term, 0)
        rate_r, rate_b = a / n_r, c / n_b
        if rate_r == rate_b:
            continue
        g2 = _g2(a, n_r - a, c, n_b - c)
        if g2 < G2_THRESHOLD:
            continue

        if rate_r > rate_b and a >= MIN_TERM_DOCS:
            avg_rating = rating_r[term] / a
            rising_c.append({
                "term": term, "score": round(g2, 1),
                "recent_pct": round(100 * rate_r, 1), "baseline_pct": round(100 * rate_b, 1),
                "recent_count": a, "baseline_count": c,
                "avg_rating": round(avg_rating, 2),
                "avg_sentiment": round(sent_r[term] / a, 3),
                "tone": _tone(avg_rating),
                "example": _example(ex_r[term]),
            })
        elif rate_b > rate_r and c >= MIN_TERM_DOCS:
            avg_rating = rating_b[term] / c
            fading_c.append({
                "term": term, "score": round(g2, 1),
                "recent_pct": round(100 * rate_r, 1), "baseline_pct": round(100 * rate_b, 1),
                "recent_count": a, "baseline_count": c,
                "avg_rating": round(avg_rating, 2),
                "avg_sentiment": round(sent_b[term] / c, 3),
                "tone": _tone(avg_rating),
                "example": _example(ex_b[term]),
            })

    rising, fading = _pick(rising_c), _pick(fading_c)

    rating_baseline = [r["rating"] for dt, r in dated_all if dt < split]
    rating_recent = [r["rating"] for dt, r in dated_all if dt >= split]
    rating_trend = _compare(rating_baseline, rating_recent)
    sentiment_trend = _compare(
        [score_sentiment(r["text"]) for r in baseline],
        [score_sentiment(r["text"]) for r in recent],
    )

    insights = []
    if (sentiment_trend["significant"] and sentiment_trend["delta"] < 0
            and (not rating_trend["significant"] or abs(rating_trend["delta"]) < 0.15)):
        insights.append({
            "type": "warning",
            "message": (
                "Review language is turning more negative while star ratings have barely moved. "
                "This is the early-warning pattern: the score may follow."
            ),
        })
    elif sentiment_trend["significant"] and sentiment_trend["delta"] > 0:
        insights.append({"type": "positive", "message": "Review language is getting more positive recently."})

    for item in [t for t in rising if t["tone"] == "negative"][:3]:
        insights.append({
            "type": "warning",
            "message": (
                f"\"{item['term']}\" appears in {item['recent_pct']}% of recent reviews vs "
                f"{item['baseline_pct']}% earlier, and reviews mentioning it average {item['avg_rating']}★."
            ),
        })
    for item in [t for t in fading if t["tone"] == "negative"][:2]:
        insights.append({
            "type": "positive",
            "message": (
                f"Complaints mentioning \"{item['term']}\" are fading "
                f"({item['baseline_pct']}% of reviews earlier, {item['recent_pct']}% recently)."
            ),
        })

    return {
        "status": "ok",
        "windows": {
            "baseline": {
                "start": dated[0][0].strftime("%Y-%m-%d"),
                "end": (split - timedelta(days=1)).strftime("%Y-%m-%d"),
                "reviews": n_b,
                "all_reviews": len(rating_baseline),
            },
            "recent": {
                "start": split.strftime("%Y-%m-%d"),
                "end": last.strftime("%Y-%m-%d"),
                "reviews": n_r,
                "all_reviews": len(rating_recent),
            },
        },
        "rating_trend": rating_trend,
        "sentiment_trend": sentiment_trend,
        "rising": rising,
        "fading": fading,
        "insights": insights,
    }


def terms_for_text(text: str) -> set:
    """The topic terms (words and two-word phrases) found in one review."""
    return set(_review_terms(text).keys())


def top_terms(texts: List[str], n: int = 6, min_docs: int = 2) -> List[dict]:
    """Most common topic terms across a set of reviews (counted once per review)."""
    df: Counter = Counter()
    for text in texts:
        df.update(terms_for_text(text))

    def order(c):
        return (-c["reviews"], c["term"])

    cands = sorted(
        ({"term": term, "reviews": count} for term, count in df.items() if count >= min_docs),
        key=order,
    )
    phrases = [c for c in cands if " " in c["term"]][:n]
    covered = {w for c in phrases for w in c["term"].split()}
    singles = [c for c in cands if " " not in c["term"] and c["term"] not in covered]
    return sorted(phrases + singles[:n], key=order)[:n]


def trim_for_preview(trends: dict, keep: int = 3) -> dict:
    """Free-tier taste of the trends panel: top few topics and headline
    insights, but no example quotes and a count of what's hidden."""
    if not trends or trends.get("status") != "ok":
        return trends

    def strip(items):
        return [{k: v for k, v in item.items() if k != "example"} for item in items[:keep]]

    preview = dict(trends)
    preview["hidden"] = {
        "rising": max(0, len(trends["rising"]) - keep),
        "fading": max(0, len(trends["fading"]) - keep),
    }
    preview["rising"] = strip(trends["rising"])
    preview["fading"] = strip(trends["fading"])
    preview["insights"] = trends["insights"][:2]
    preview["preview"] = True
    return preview


# Public alias: Welch t-test comparison, reused by the revenue-signals module.
compare_means = _compare
