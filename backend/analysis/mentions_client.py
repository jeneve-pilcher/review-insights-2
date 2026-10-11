"""Web mentions of a business, found through Outscraper's Google Search endpoint
(/google-search). Review platforms we already analyze (Google, Yelp) are excluded.

The response layout wasn't verifiable ahead of time, so parsing is defensive, and
scripts/test_mentions.py prints the raw response so a first live run shows whether
anything needs adjusting.
"""
import os
import time
from datetime import timedelta
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from fastapi import HTTPException

import config
from analysis import outscraper_client as oc

BASE_URL = os.environ.get("OUTSCRAPER_BASE_URL", "https://api.app.outscraper.com").rstrip("/")
PAGES_PER_QUERY = int(os.environ.get("MENTIONS_PAGES_PER_QUERY", "2"))   # 1 page = about 10 results per query
MAX_PAGES = 5
REQUEST_TIMEOUT = 60
POLL_INTERVAL = 2.0
POLL_TIMEOUT = 120.0

# We already analyze these as review platforms, so they aren't "mentions".
EXCLUDED_DOMAINS = ("google.", "yelp.", "gstatic.", "googleusercontent.")


def build_queries(terms: str) -> List[str]:
    base = terms.strip()
    return [
        f"{base} -site:google.com -site:yelp.com",   # the open web: news, blogs, forums, social
        f"site:reddit.com {base}",                    # Reddit threads specifically
    ]


def effective_pages(pages: Optional[int] = None) -> int:
    return max(1, min(MAX_PAGES, int(pages or PAGES_PER_QUERY)))


def searches_for(terms: str, pages: Optional[int] = None) -> int:
    """How many billable web searches one pull makes (queries x pages)."""
    return len(build_queries(terms)) * effective_pages(pages)


def tbs_for_months(months: int) -> Optional[str]:
    """Google's time filter. Only coarse buckets exist, so results are also date-filtered below."""
    if months <= 1:
        return "qdr:m"
    return "qdr:y" if months <= 12 else None


def _headers() -> dict:
    return {"X-API-KEY": config.require(config.OUTSCRAPER_API_KEY, "OUTSCRAPER_API_KEY")}


def _get(url: str, params: Optional[dict] = None):
    try:
        return requests.get(url, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Outscraper for web mentions: {exc}")


def _json_or_error(resp, what: str):
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Outscraper returned {resp.status_code} for {what}: {(resp.text or '')[:200]}")
    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"Outscraper sent a response for {what} that wasn't valid JSON.")


def _wait_for_results(payload: dict) -> dict:
    location = payload.get("results_location")
    if not location:
        raise HTTPException(status_code=502, detail="Outscraper accepted the web search but gave no results link.")
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        data = _json_or_error(_get(location), "web mentions (waiting for results)")
        status = str(data.get("status", "")).lower()
        if status == "success":
            return data
        if status in ("error", "failed"):
            raise HTTPException(status_code=502, detail=f"Outscraper could not run the web search: {data.get('error') or status}")
    raise HTTPException(status_code=504, detail="Outscraper took too long to return the web search.")


def _search(query: str, tbs: Optional[str], pages: Optional[int] = None) -> dict:
    n = effective_pages(pages)
    params = {"query": query, "pagesPerQuery": n, "pages_per_query": n, "async": "false"}
    if tbs:
        params["tbs"] = tbs
    resp = _get(f"{BASE_URL}/google-search", params)
    payload = _json_or_error(resp, "web mentions")
    if resp.status_code == 202 or str(payload.get("status", "")).lower() == "pending":
        payload = _wait_for_results(payload)
    return payload


def extract_results(node) -> List[dict]:
    """Finds the individual search results however they're nested."""
    out: List[dict] = []
    if isinstance(node, list):
        for item in node:
            out.extend(extract_results(item))
    elif isinstance(node, dict):
        has_url = any(isinstance(node.get(k), str) and node[k].startswith("http") for k in ("link", "url"))
        has_body = any(k in node for k in ("title", "description", "snippet", "text"))
        if has_url and has_body:
            out.append(node)
        else:
            for key in ("data", "organic_results", "organic", "results"):
                if key in node:
                    out.extend(extract_results(node[key]))
    return out


def _normalize(raw: dict) -> Optional[dict]:
    url = next((raw[k] for k in ("link", "url") if isinstance(raw.get(k), str) and raw[k].startswith("http")), None)
    if not url:
        return None
    domain = (urlparse(url).netloc or "").lower()
    domain = domain[4:] if domain.startswith("www.") else domain
    when = next((str(raw[k]) for k in ("date", "datetime", "published", "date_published") if raw.get(k)), None)
    return {
        "title": str(raw.get("title") or "").strip(),
        "url": url,
        "snippet": str(raw.get("description") or raw.get("snippet") or raw.get("text") or "").strip(),
        "date": when,
        "domain": domain,
    }


def fetch_mentions_with_meta(terms: str, months: int, pages: Optional[int] = None) -> Tuple[List[dict], bool, List[str]]:
    """Returns (items, served_from_cache, notes). Raises HTTPException only if EVERY search failed."""
    pages = effective_pages(pages)
    key = ("mentions", terms.strip().lower(), months, pages)
    hit = oc.cache_lookup(key)
    if hit is not None:
        items, notes = hit
        return [dict(i) for i in items], True, list(notes)

    window_start = oc._now_utc() - timedelta(days=months * 30.44)
    tbs = tbs_for_months(months)
    items, notes, seen, errors, ok = [], [], set(), [], 0

    for query in build_queries(terms):
        try:
            payload = _search(query, tbs, pages)
        except HTTPException as exc:
            errors.append(exc)
            continue
        ok += 1
        for raw in extract_results(payload.get("data", payload) if isinstance(payload, dict) else payload):
            item = _normalize(raw)
            if not item or any(d in item["domain"] for d in EXCLUDED_DOMAINS):
                continue
            dedupe = item["url"].split("#")[0].rstrip("/")
            if dedupe in seen:
                continue
            dt = oc._parse_dt(item["date"])
            if dt is not None and dt < window_start:
                continue                                        # older than the window
            seen.add(dedupe)
            items.append(item)

    if not ok:
        raise errors[0]
    if errors:
        notes.append(f"One of the web searches failed, so mentions may be incomplete. ({errors[0].detail})")
    oc.cache_store(key, (items, notes))
    return [dict(i) for i in items], False, list(notes)


def fetch_raw(terms: str, months: int = 12) -> dict:
    """For scripts/test_mentions.py: the untouched response to the first search."""
    return _search(build_queries(terms)[0], tbs_for_months(months))
