"""Shared helpers for the config-driven generic fetchers (JSON-LD, ICS, Tribe)."""
import html
import json
import re
import time
from datetime import datetime

import config

try:
    import requests
except ImportError:
    print("Please install requests")
    exit(1)

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; awesome-developer-conferences-bot)'}


def http_get(url, **kwargs):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, **kwargs)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"  ! fetch failed {url}: {e}")
        return None


def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(text or '')).strip().replace('|', '\\|')


def build_event(name, start, end, location, link):
    """start/end are datetime.date; returns the dict shape aggregate.py expects."""
    name = clean(name)
    location = clean(location) or "Unknown"
    if end and end != start:
        date_str = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    else:
        date_str = start.strftime('%Y-%m-%d')
    register = f"[↗]({link})" if link else "N/A"
    return {
        "name": name,
        "date": date_str,
        "location": location,
        "register": register,
        "line": f"| {name} | {date_str} | {location} | {register} |",
    }


def parse_iso_date(value):
    if not value:
        return None
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(value))
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
    except ValueError:
        return None


def finalize(events, tag, out_file, raw_count, relevance=True):
    """Drop past events, apply relevance filter, dedupe by name+date, save."""
    today = datetime.now().date()
    seen, kept = set(), []
    for ev, end in events:
        start = parse_iso_date(ev["date"])
        if not start or (end or start) < today:
            continue
        if relevance and not config.is_event_relevant(f"{ev['name']} {ev['location']}"):
            continue
        key = (re.sub(r'\W', '', ev["name"].lower()), ev["date"])
        if key in seen:
            continue
        seen.add(key)
        kept.append(ev)
    print(f"[{tag}] Total raw events: {raw_count} | Successfully fetched: {len(kept)}")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(kept, f, indent=2)
    print(f"Saved {len(kept)} events to {out_file}")
    return kept
