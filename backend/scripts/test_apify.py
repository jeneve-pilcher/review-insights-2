"""One-command check of an OpenTable / DoorDash / Uber Eats / Grubhub connection (through Apify).
Run in the backend container, for example:

    docker compose exec backend python scripts/test_apify.py doordash "https://www.doordash.com/store/your-restaurant-city-123456/"
    docker compose exec backend python scripts/test_apify.py ubereats "https://www.ubereats.com/store/your-restaurant/abc123"
    docker compose exec backend python scripts/test_apify.py grubhub  "https://www.grubhub.com/restaurant/your-restaurant/123456/"
    docker compose exec backend python scripts/test_apify.py opentable "https://www.opentable.com/r/your-restaurant-city"

It makes ONE small Apify run (a fraction of a cent), prints the raw rows and how the app reads them, so you
can see at once whether it worked and which fields really came back.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from datetime import datetime, timedelta  # noqa: E402

from analysis import delivery_clients as dc  # noqa: E402
from analysis import opentable_client as otc  # noqa: E402

PLATFORMS = {
    "opentable": (otc.normalize_opentable_url, lambda u: otc.fetch_raw(u, 5), otc._normalize, otc.ACTOR),
    "doordash": (dc.normalize_doordash_url, dc.RAW["doordash"][0], dc._doordash_normalize, dc.DOORDASH_ACTOR),
    "ubereats": (dc.normalize_ubereats_url, dc.RAW["ubereats"][0], dc._ubereats_normalize, dc.UBEREATS_ACTOR),
    "grubhub": (dc.normalize_grubhub_url, dc.RAW["grubhub"][0], dc._grubhub_normalize, dc.GRUBHUB_ACTOR),
}


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in PLATFORMS:
        print(__doc__)
        sys.exit(1)
    platform, link = sys.argv[1], sys.argv[2]
    normalize, fetch_raw, read, actor = PLATFORMS[platform]
    try:
        url = normalize(link)
    except ValueError as exc:
        print(f"Bad link: {exc}")
        sys.exit(1)

    print(f"Platform: {platform}\nPage:     {url}\nActor:    {actor}\n")
    rows = fetch_raw(url)
    print(f"Rows returned by Apify: {len(rows)}")
    if not rows:
        print("Nothing came back. The actor may have been blocked, or the page has no reviews.")
        sys.exit(2)
    print("\nFIRST RAW ROW (these are the fields the actor really returns):")
    print(json.dumps(rows[0], indent=2, default=str)[:2500])

    reviews = read(rows, datetime.utcnow() - timedelta(days=3650))
    print(f"\nHOW THE APP READS IT: {len(reviews)} review(s)")
    for r in reviews[:8]:
        shown = (r["text"][:70] + "...") if len(r["text"]) > 70 else r["text"]
        stars = "no stars" if r["rating"] is None else f"{r['rating']} stars"
        print(f"  {stars} | {r['datetime_utc']} | {shown or '(no text)'}")
    if not reviews:
        print("WARNING: rows came back but no reviews could be read from them. Send me the raw row above.")


if __name__ == "__main__":
    main()
