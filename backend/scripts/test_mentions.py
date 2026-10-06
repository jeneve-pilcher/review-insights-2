"""One-command check of the web-mentions connection. Run inside the backend container:

    docker compose exec backend python scripts/test_mentions.py "Your Business City ST" 12

It makes ONE web search, then prints the raw response and how the app reads it, so you
can see right away whether the request worked and which fields Outscraper returns.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from analysis import mentions_client  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    terms = sys.argv[1]
    months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    query = mentions_client.build_queries(terms)[0]
    print(f"Search:   {query}")
    print(f"Endpoint: {mentions_client.BASE_URL}/google-search  (time filter: {mentions_client.tbs_for_months(months)})\n")

    payload = mentions_client.fetch_raw(terms, months)
    print(f"Top-level keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__}")
    raw = mentions_client.extract_results(payload.get("data", payload) if isinstance(payload, dict) else payload)
    print(f"Search results found: {len(raw)}\n")
    if not raw:
        print("No results were found in that response. Raw response follows:")
        print(json.dumps(payload, indent=2, default=str)[:3000])
        sys.exit(2)

    print("FIRST RAW RESULT (these are the fields Outscraper really returns):")
    print(json.dumps(raw[0], indent=2, default=str)[:2000])
    print("\nHOW THE APP READS THEM:")
    for r in raw[:10]:
        n = mentions_client._normalize(r)
        if n:
            print(f"  {n['domain']:<28} {str(n['date'] or 'no date'):<14} {n['title'][:60]}")


if __name__ == "__main__":
    main()
