"""One-command check of the Yelp connection. Run it inside the backend container:

    docker compose exec backend python scripts/test_yelp.py "https://www.yelp.com/biz/your-business" 5

It makes ONE small pull (default 5 reviews, a few cents at most), then prints the
raw response and what the app made of it, so you can see right away whether the
request worked and which fields Outscraper really returns.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from analysis import yelp_client  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    try:
        url = yelp_client.normalize_yelp_url(sys.argv[1])
    except ValueError as exc:
        print(f"Bad Yelp link: {exc}")
        sys.exit(1)
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"Yelp page: {url}")
    print(f"Endpoint:  {yelp_client.BASE_URL}/yelp-reviews  (limit {limit}, sort={yelp_client.YELP_SORT!r})\n")

    payload, raw = yelp_client.fetch_raw(url, limit)

    print(f"Top-level keys in the response: {list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__}")
    print(f"Review objects found: {len(raw)}\n")
    if not raw:
        print("No reviews were found in that response. Raw response follows:")
        print(json.dumps(payload, indent=2, default=str)[:3000])
        sys.exit(2)

    print("FIRST RAW REVIEW (these are the fields Outscraper really returns):")
    print(json.dumps(raw[0], indent=2, default=str)[:2500])

    from datetime import datetime, timedelta
    normalized = yelp_client._normalize(raw, datetime.utcnow() - timedelta(days=3650))
    print("\nHOW THE APP READS IT:")
    for r in normalized:
        shown = (r["text"][:70] + "...") if len(r["text"]) > 70 else r["text"]
        print(f"  {r['rating']} stars | {r['datetime_utc']} | {shown or '(no text)'}")
    if len(normalized) != len(raw):
        print(f"\nWARNING: {len(raw) - len(normalized)} of {len(raw)} reviews were dropped (missing or invalid rating).")
    dates = [r["datetime_utc"] for r in normalized if r["datetime_utc"]]
    print(f"\nDates found on {len(dates)} of {len(normalized)} reviews. "
          f"Newest-first? {'yes' if dates == sorted(dates, reverse=True) else 'NO - the sort value may be wrong'}")


if __name__ == "__main__":
    main()
