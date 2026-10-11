"""Runs an Apify actor (a community-built scraper) and returns the rows it produced.

Used for OpenTable, DoorDash, Uber Eats and Grubhub reviews. Flow: start the run -> wait for it to finish ->
read its dataset. Failures become HTTPExceptions with a plain explanation, so the caller can
turn them into a note instead of breaking the whole analysis.
"""
import os
import time
from typing import List, Optional

import requests
from fastapi import HTTPException

BASE_URL = os.environ.get("APIFY_BASE_URL", "https://api.apify.com").rstrip("/")
# A hard ceiling on what ONE run may cost (Apify stops the run when it's reached).
MAX_CHARGE_USD = float(os.environ.get("APIFY_MAX_CHARGE_USD", "0.50"))
RUN_TIMEOUT_SECS = int(os.environ.get("APIFY_RUN_TIMEOUT_SECS", "240"))
WAIT_SLICE_SECS = 25         # each status check waits up to this long for the run to finish
POLL_INTERVAL = 1.0          # pause between checks if the server answers immediately
POLL_TIMEOUT = float(os.environ.get("APIFY_POLL_TIMEOUT_SECS", "270"))
REQUEST_TIMEOUT = 60

TERMINAL = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}


def _token() -> str:
    token = os.environ.get("APIFY_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(status_code=502, detail="Apify isn't set up yet: add APIFY_API_TOKEN to backend/.env.")
    return token


def _call(method: str, url: str, what: str, **kwargs):
    headers = {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}
    try:
        resp = requests.request(method, url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Apify while {what}: {exc}")
    if resp.status_code == 401:
        raise HTTPException(status_code=502, detail="Apify rejected the API token. Check APIFY_API_TOKEN.")
    if resp.status_code == 402:
        raise HTTPException(status_code=502, detail="Apify says this account is out of credit or usage (402). Top it up in Apify.")
    if resp.status_code == 403:
        raise HTTPException(status_code=502, detail=f"Apify refused the request while {what} (403).")
    if resp.status_code == 404:
        raise HTTPException(status_code=502, detail=f"Apify couldn't find what it needed while {what} (404). Check the actor name.")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Apify returned {resp.status_code} while {what}: {(resp.text or '')[:200]}")
    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"Apify sent a response while {what} that wasn't valid JSON.")


def run_actor(actor: str, run_input: dict, max_items: Optional[int] = None) -> List[dict]:
    """Runs `actor` (e.g. "parsebird/opentable-reviews-scraper") with `run_input`; returns its dataset rows."""
    actor_id = actor.replace("/", "~")
    params = {"timeout": RUN_TIMEOUT_SECS, "maxTotalChargeUsd": MAX_CHARGE_USD}
    if max_items:
        params["maxItems"] = max_items

    run = _call("POST", f"{BASE_URL}/v2/acts/{actor_id}/runs", "starting the scraper", params=params, json=run_input).get("data") or {}
    run_id = run.get("id")
    if not run_id:
        raise HTTPException(status_code=502, detail="Apify started the scraper but gave no run id.")

    deadline = time.time() + POLL_TIMEOUT
    status = run.get("status")
    while status not in TERMINAL:
        if time.time() >= deadline:
            try:
                _call("POST", f"{BASE_URL}/v2/actor-runs/{run_id}/abort", "stopping a slow run")
            except HTTPException:
                pass
            raise HTTPException(status_code=504, detail="The scraper took too long to finish. Try again, or use a shorter window.")
        time.sleep(POLL_INTERVAL)
        run = _call("GET", f"{BASE_URL}/v2/actor-runs/{run_id}", "checking the scraper", params={"waitForFinish": WAIT_SLICE_SECS}).get("data") or {}
        status = run.get("status")

    if status != "SUCCEEDED":
        raise HTTPException(status_code=502, detail=f"The scraper ended as {status}. The site may have changed or blocked it.")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise HTTPException(status_code=502, detail="The scraper finished but produced no dataset.")
    items = _call("GET", f"{BASE_URL}/v2/datasets/{dataset_id}/items", "reading the scraper's results",
                  params={"format": "json", "clean": "true"})
    if not isinstance(items, list):
        raise HTTPException(status_code=502, detail="The scraper's results weren't in the expected form.")
    return items
