"""Discover big conferences from X/Twitter announcements.

Uses the official X API v2 (needs X_BEARER_TOKEN). Two signals are read:
  1. The timelines of official organizer accounts in ORGANIZER_HANDLES
     (e.g. Black Hat, DEF CON, RSAC) - high signal, so no relevance filter.
  2. Recent-search queries in SEARCH_QUERIES - noisy, so relevance-filtered.

Tweets are free text, so Gemini (GEMINI_API_KEY) turns them into structured
events. Without either key the fetcher logs and exits cleanly, like
gemini_discovery.py.
"""
import json
import os
import re
import time
from datetime import datetime

import config
from generic_common import build_event, finalize, parse_iso_date

try:
    import requests
except ImportError:
    print("Please install requests")
    exit(1)

X_API = "https://api.x.com/2"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

# Official accounts of flagship event series. Add a handle (no @) to track more.
ORGANIZER_HANDLES = [
    "BlackHatEvents",   # Black Hat USA / Europe / Asia / MEA
    "defcon",
    "RSAConference",
    "KubeCon_",
    "CloudNativeFdn",
    "linuxfoundation",
    "AWSreInvent",
    "WeAreDevs",
    "SaaStr",
]

SEARCH_QUERIES = [
    '("registration is open" OR "early bird" OR "call for papers" OR "CFP is open") '
    '(conference OR summit) (developer OR devops OR security OR kubernetes OR "open source") '
    '-is:retweet -is:reply lang:en',
]

TWEETS_PER_HANDLE = 20
TWEETS_PER_QUERY = 50


def x_get(path, token, params):
    """GET an X API v2 endpoint; returns parsed JSON or None (logged) on failure."""
    try:
        resp = requests.get(
            f"{X_API}{path}",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=25,
        )
    except requests.RequestException as e:
        print(f"  ! X API request failed {path}: {e}")
        return None
    if resp.status_code != 200:
        # 401 bad token, 402/403 plan lacks access, 429 rate limited
        print(f"  ! X API {resp.status_code} for {path}: {resp.text[:200]}")
        return None
    return resp.json()


def tweet_to_record(tweet):
    """Flatten a tweet to the text + expanded links the extractor needs."""
    urls = [
        u.get("expanded_url") for u in (tweet.get("entities") or {}).get("urls", [])
        if u.get("expanded_url") and "twitter.com" not in u["expanded_url"] and "x.com" not in u["expanded_url"]
    ]
    return {
        "text": tweet.get("text", ""),
        "posted": (tweet.get("created_at") or "")[:10],
        "links": urls,
    }


def fetch_handle_tweets(token, handles):
    users = x_get("/users/by", token, {"usernames": ",".join(handles)}) or {}
    records = []
    for user in users.get("data", []):
        data = x_get(f"/users/{user['id']}/tweets", token, {
            "max_results": TWEETS_PER_HANDLE,
            "exclude": "retweets,replies",
            "tweet.fields": "created_at,entities",
        }) or {}
        for t in data.get("data", []):
            rec = tweet_to_record(t)
            rec["source"] = f"@{user['username']}"
            records.append(rec)
        time.sleep(1)
    missing = {e.get("value") for e in users.get("errors", [])}
    if missing:
        print(f"  ! handles not found: {sorted(m for m in missing if m)}")
    return records


def fetch_search_tweets(token, queries):
    records = []
    for q in queries:
        data = x_get("/tweets/search/recent", token, {
            "query": q,
            "max_results": TWEETS_PER_QUERY,
            "tweet.fields": "created_at,entities",
        }) or {}
        for t in data.get("data", []):
            rec = tweet_to_record(t)
            rec["source"] = "search"
            records.append(rec)
        time.sleep(1)
    return records


def extract_events_with_gemini(records, api_key):
    """Ask Gemini to pull concrete upcoming events out of tweet text."""
    if not records:
        return []
    today = datetime.now().strftime("%Y-%m-%d")
    tweets = "\n".join(
        f"- [{r['posted']}] {r['text']} {' '.join(r['links'])}".replace("\n", " ")
        for r in records
    )
    prompt = (
        f"Today is {today}. Below are tweets. Extract every distinct upcoming conference/summit/"
        "event that a tweet announces with a specific start date. Ignore past events, webinars, "
        "job posts and tweets without a concrete date. Resolve missing years from the tweet's "
        "posted date. Output a JSON array of objects with keys: 'name' (include the edition, e.g. "
        "'Black Hat Asia 2027'), 'start' (YYYY-MM-DD), 'end' (YYYY-MM-DD or null), 'location' "
        "('City, Country'), 'url' (official event site from the tweet links, or null).\n\n" + tweets
    )
    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key.strip()},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        events = json.loads(text)
    except Exception as e:
        print(f"  ! Gemini extraction failed: {e}")
        return []
    return events if isinstance(events, list) else []


def to_event_tuples(extracted):
    """Validate extractor output into (event, end_date) tuples for finalize()."""
    out = []
    for item in extracted:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        start = parse_iso_date(item.get("start"))
        if not start:
            continue
        end = parse_iso_date(item.get("end"))
        if end and end < start:
            end = None
        url = item.get("url") or ""
        if not url.startswith("http"):
            url = ""
        ev = build_event(item["name"], start, end, item.get("location") or "Unknown", url)
        if config.is_multi_event_promo_post(ev["name"]):
            continue
        out.append((ev, end))
    return out


def main():
    token = os.environ.get("X_BEARER_TOKEN")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not token:
        print("No X_BEARER_TOKEN found in environment. Skipping X/Twitter discovery.")
        return []
    if not gemini_key:
        print("No GEMINI_API_KEY found in environment. Skipping X/Twitter discovery.")
        return []

    print("Fetching organizer timelines from X...")
    organizer = fetch_handle_tweets(token, ORGANIZER_HANDLES)
    print("Running X search queries...")
    searched = fetch_search_tweets(token, SEARCH_QUERIES)
    print(f"Fetched {len(organizer)} organizer tweets and {len(searched)} search tweets.")

    # Separate passes so the trusted organizer events skip the relevance filter.
    organizer_events = to_event_tuples(extract_events_with_gemini(organizer, gemini_key))
    search_events = to_event_tuples(extract_events_with_gemini(searched, gemini_key))
    raw = len(organizer_events) + len(search_events)

    # Organizer accounts are trusted; only noisy search hits go through the relevance filter.
    search_events = [
        (e, end) for e, end in search_events
        if config.is_event_relevant(f"{e['name']} {e['location']}")
    ]
    return finalize(organizer_events + search_events, "Twitter", "events_twitter.json", raw, relevance=False)


if __name__ == "__main__":
    main()
