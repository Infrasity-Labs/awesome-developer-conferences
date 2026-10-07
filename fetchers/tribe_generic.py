import re
import time
from datetime import datetime

import config
from generic_common import http_get, build_event, parse_iso_date, finalize, clean

# WordPress sites running "The Events Calendar" plugin (public REST API).
SOURCES = [
    "https://myconnectivity.lu",
]
MAX_PAGES = 5


def strip_tags(text):
    return clean(re.sub(r'<[^>]+>', ' ', text or ''))


def venue_location(ev):
    venue = ev.get('venue')
    if isinstance(venue, list):
        venue = venue[0] if venue else None
    if not isinstance(venue, dict):
        return ''
    parts = [venue.get('city'), venue.get('state') or venue.get('province'), venue.get('country')]
    text = ', '.join(p for p in parts if p)
    return text or venue.get('venue') or ''


def fetch_site(base):
    out, raw = [], 0
    today = datetime.now().strftime('%Y-%m-%d')
    for page in range(1, MAX_PAGES + 1):
        resp = http_get(f"{base}/wp-json/tribe/events/v1/events",
                        params={'per_page': 50, 'page': page, 'start_date': today})
        if not resp:
            break
        try:
            data = resp.json()
        except Exception:
            break
        events = data.get('events', [])
        for ev in events:
            raw += 1
            start = parse_iso_date(ev.get('start_date'))
            end = parse_iso_date(ev.get('end_date')) or start
            name = strip_tags(ev.get('title'))
            if not name or not start:
                continue
            location = venue_location(ev)
            if not location and ev.get('is_virtual'):
                location = 'Online'
            out.append((build_event(name, start, end, location, ev.get('url') or base), end))
        if page >= int(data.get('total_pages') or 1):
            break
        time.sleep(0.5)
    return out, raw


def main():
    events, raw_total = [], 0
    for base in SOURCES:
        evs, raw = fetch_site(base)
        print(f"[Tribe] {base} -> {raw} events")
        events.extend(evs)
        raw_total += raw
    finalize(events, "Tribe", "events_tribe_generic.json", raw_total)


if __name__ == "__main__":
    main()
