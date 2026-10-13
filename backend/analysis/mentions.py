"""Turns raw web-search results into a mentions summary and a couple of signals."""
import re
from collections import Counter
from typing import List, Optional
from urllib.parse import unquote_plus

from dateutil import parser as date_parser

from analysis.sentiment import score_sentiment

_SOCIAL = ("facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com", "youtube.com", "nextdoor.com",
           "threads.net", "pinterest.com", "linkedin.com")
_REVIEW_SITES = ("tripadvisor.", "trustpilot.com", "bbb.org", "foursquare.com", "opentable.com", "yellowpages.com",
                 "mapquest.com", "restaurantji.com", "zomato.com", "doordash.com", "ubereats.com", "grubhub.com",
                 "menupix.com", "allmenus.com")
_NEWS_HINTS = ("news", "times", "post", "tribune", "herald", "gazette", "patch.com", "eater.com", "thrillist.com",
               "journal", "press", "chronicle", "magazine", "blog", "paper")
CATEGORY_LABELS = {"reddit": "Reddit", "social": "Social media", "review_site": "Other review/listing sites",
                   "news_blog": "News & blogs", "web": "Other web"}

_GENERIC = {"the", "and", "of", "restaurant", "cafe", "coffee", "bar", "grill", "pizza", "kitchen", "house", "shop",
            "store", "inc", "llc", "co", "company", "bistro", "diner", "tavern", "bakery", "pub", "taproom"}


def default_terms(query: str) -> str:
    """'Acme Grill, 123 Main St, Austin TX' -> 'Acme Grill Austin TX' (name + city, no street address).
    A Google Maps link ('.../maps/place/Starbucks/@40.04,...') gives the business name from the link."""
    q = (query or "").strip()
    if q.lower().startswith(("http://", "https://")):
        m = re.search(r"/maps/place/([^/@?]+)", q)
        if m:
            name = unquote_plus(m.group(1)).strip()
            if name:
                return name
        return ""  # a link with no readable name: better to search nothing than the whole link
    parts = [p.strip() for p in (query or "").split(",") if p.strip()]
    if len(parts) > 2:
        return f"{parts[0]} {parts[-1]}"
    return " ".join(parts)


_STATES = {"al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks","ky","la","me","md","ma","mi","mn","ms",
           "mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa",
           "wv","wi","wy","dc"}


def _strip_state_zip(text: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z.'-]*|\d+", text or "")]
    while words and (words[-1].isdigit() or words[-1].lower().strip(".") in _STATES or words[-1].lower() in ("usa", "us", "united", "states")):
        words.pop()
    return " ".join(w for w in words if not w.isdigit())


_DIRECTIONS = {"n", "s", "e", "w", "ne", "nw", "se", "sw", "north", "south", "east", "west"}
_STREET_WORDS = {"st", "street", "ave", "avenue", "rd", "road", "blvd", "boulevard", "dr", "drive", "ln", "lane", "way", "hwy",
                 "highway", "pkwy", "parkway", "ct", "court", "pl", "place", "cir", "circle", "ste", "suite", "unit"}


def _street_parts(street: str):
    """'1234 E Main St' -> ('1234', 'main'). The street's own name, without direction or 'St'/'Ave'."""
    street = re.split(r"\b(?:ste|suite|unit|#)\b", street or "", flags=re.I)[0]
    words = re.findall(r"[A-Za-z0-9'-]+", street)
    number = words[0] if words and words[0].isdigit() else ""
    rest = [w.lower().replace("'", "") for w in (words[1:] if number else words)]
    core = [w for w in rest if w not in _DIRECTIONS and w not in _STREET_WORDS]
    return number, " ".join(core or rest)


def mention_target(query: str, place: Optional[dict] = None):
    """(search words, location) for one STORE, so internet mentions are about this store and not the whole company or
    every store of the brand in the city. `location` is {"number", "street", "city"} (pieces may be empty), or None if
    nothing but the name is known. The street and city come from what was saved ("Name, street, city") or else from the
    address Google gave for the place."""
    place = place or {}
    q = (query or "").strip()
    is_link = q.lower().startswith(("http://", "https://"))
    name = (place.get("name") or "").strip() or default_terms(q if is_link else "")
    parts = [] if is_link else [p.strip() for p in q.split(",") if p.strip()]
    if not name and parts:
        name = parts[0]
    address_parts = parts[1:]
    if not any(re.match(r"\d", p) for p in address_parts):
        full = place.get("full_address") or place.get("address") or ""
        address_parts = [p.strip() for p in full.split(",") if p.strip()] or address_parts
    street_text = next((p for p in address_parts if re.match(r"\d", p)), "")
    city = ""
    for part in reversed(address_parts):                  # the last part that is a place name, not a street, state/zip or country
        cand = _strip_state_zip(part)
        if cand and not re.match(r"\d", part):
            city = cand
            break
    if not city and place.get("city"):
        city = place["city"].strip()
    number, core = _street_parts(street_text)
    words = " ".join(x for x in (name, number, core, city) if x).strip()
    where = {"number": number, "street": core, "city": city.lower()}
    return words, (where if (core or city) else None)


def category_for(domain: str) -> str:
    d = (domain or "").lower()
    if d.endswith("reddit.com"):
        return "reddit"
    if any(d == s or d.endswith("." + s) for s in _SOCIAL):
        return "social"
    if any(s in d for s in _REVIEW_SITES):
        return "review_site"
    if any(h in d for h in _NEWS_HINTS):
        return "news_blog"
    return "web"


def distinct_tokens(terms: str) -> List[str]:
    """The distinctive word(s) of the business name, used to drop unrelated results."""
    words = [w.replace("'", "") for w in re.findall(r"[a-z0-9']+", (terms or "").lower())]
    return [w for w in words if len(w) >= 3 and w not in _GENERIC][:1]


def is_relevant(item: dict, tokens: List[str], area: Optional[dict] = None) -> bool:
    hay = f"{item['title']} {item['snippet']} {item['url']}".lower().replace("'", "")
    if tokens and not any(t in hay for t in tokens):
        return False
    if not area:
        return True
    street, number, city = area.get("street") or "", area.get("number") or "", area.get("city") or ""
    on_street = bool(street) and street in hay
    if on_street and (number and number in hay):
        return True                                        # the street address itself
    if on_street and (not city or city in hay):
        return True                                        # "the Starbucks on Main St" in the right city
    return bool(city) and not street and city in hay       # only a city is known


def _date(value):
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def build_mentions(items: List[dict], terms: str, negative_topics: Optional[List[str]] = None, failed: bool = False,
                   area: Optional[dict] = None) -> dict:
    if failed:
        return {"status": "unavailable", "terms": terms, "items": [], "summary": None, "topic_overlap": [], "dropped": 0}

    tokens = distinct_tokens(terms)
    kept = []
    for position, it in enumerate(items):
        if not is_relevant(it, tokens, area):
            continue
        text = f"{it['title']}. {it['snippet']}".strip(". ")
        kept.append({**it, "category": category_for(it["domain"]), "sentiment": round(score_sentiment(text), 2),
                     "_dt": _date(it.get("date")), "_pos": position})
    dropped = len(items) - len(kept)

    # dated results newest first, then undated ones in the order Google ranked them
    kept.sort(key=lambda m: (m["_dt"] is None, -(m["_dt"].timestamp()) if m["_dt"] else 0, m["_pos"]))
    for m in kept:
        del m["_dt"], m["_pos"]

    if not kept:
        return {"status": "no_results", "terms": terms, "items": [], "summary": None, "topic_overlap": [], "dropped": dropped}

    sentiments = [m["sentiment"] for m in kept]
    summary = {
        "count": len(kept),
        "avg_sentiment": round(sum(sentiments) / len(sentiments), 3),
        "negative_count": sum(1 for s in sentiments if s <= -0.25),
        "positive_count": sum(1 for s in sentiments if s >= 0.25),
        "by_category": dict(Counter(m["category"] for m in kept)),
        "top_domains": [{"domain": d, "count": c} for d, c in Counter(m["domain"] for m in kept).most_common(5)],
    }
    overlap = []
    for term in negative_topics or []:
        n = sum(1 for m in kept if term.lower() in f"{m['title']} {m['snippet']}".lower())
        if n:
            overlap.append({"term": term, "mentions": n})
    overlap.sort(key=lambda o: -o["mentions"])
    return {"status": "ok", "terms": terms, "items": kept, "summary": summary, "topic_overlap": overlap, "dropped": dropped}


def mention_signals(mentions: Optional[dict]) -> List[dict]:
    """Signals in the same shape as the review-based ones."""
    if not mentions or mentions.get("status") != "ok":
        return []
    s, out = mentions["summary"], []
    if s["count"] >= 3 and s["avg_sentiment"] <= -0.2:
        out.append({
            "type": "warning",
            "title": f"Online chatter about you reads negative (tone {s['avg_sentiment']:+.2f} across {s['count']} mentions)",
            "detail": f"{s['negative_count']} of {s['count']} web mentions (news, blogs, forums, social) lean negative. "
                      "This is based on short search-result snippets, so read the actual pages before reacting.",
            "action": "Open Internet Mentions below and read the most recent ones.",
            "basis": "web",
        })
    elif s["count"] >= 3 and s["avg_sentiment"] >= 0.3:
        out.append({
            "type": "positive",
            "title": f"Online chatter about you reads positive (tone {s['avg_sentiment']:+.2f} across {s['count']} mentions)",
            "detail": f"{s['positive_count']} of {s['count']} web mentions lean positive.",
            "action": "Open Internet Mentions below to see where people are talking about you.",
            "basis": "web",
        })
    for o in mentions["topic_overlap"][:2]:
        if o["mentions"] >= 2:
            out.append({
                "type": "warning",
                "title": f"\"{o['term']}\" is also showing up in web mentions",
                "detail": f"{o['mentions']} web mentions use the same wording as a complaint that's rising in your reviews, "
                          "which suggests it isn't only on review sites.",
                "action": "Check the Internet Mentions list for where it's being discussed.",
                "basis": "web",
            })
    return out
