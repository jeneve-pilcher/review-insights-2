"""Competitor rows as typed. People paste a Google Maps link into whichever box is nearest, so a row with only one box
filled uses that box as the location, and a link in the name box is the location (the name is read from the link)."""
import re
from typing import List

from analysis.mentions import default_terms

_LABEL = re.compile(r"^competitor \d+$", re.I)
_URL = re.compile(r"^https?://", re.I)


def clean_competitors(rows: List[dict]) -> List[dict]:
    out = []
    for i, row in enumerate(rows or []):
        name = (row.get("name") or "").strip()
        query = (row.get("search_query") or "").strip()
        label_only = bool(_LABEL.match(name))
        if not query and name and not label_only:
            query = name
        if not query:
            continue
        if not name or label_only or _URL.match(name) or name == query:
            guess = default_terms(query) if _URL.match(query) else query.split(",")[0].strip()
            name = guess or f"Competitor {i + 1}"
        out.append({"name": name, "search_query": query})
    return out
