import json
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import config
from generic_common import http_get, build_event, parse_iso_date, finalize

# Pages that embed schema.org Event objects as JSON-LD. Add a URL here to add a source.
SOURCES = [
    # allevents.in city pages
    *[f"https://allevents.in/{c}/technology" for c in [
        "bangalore", "london", "new%20york", "sydney",
        "berlin", "delhi", "hyderabad", "mumbai", "san%20francisco", "sao%20paulo",
        "toronto",
    ]],
    # eventbrite.com listing pages
    "https://www.eventbrite.com/d/online/technology--events/",
    "https://www.eventbrite.com/d/united-kingdom--london/tech--events/",
    "https://www.eventbrite.com/d/united-states/developer-conference/",
    "https://www.eventbrite.com/d/australia--sydney/tech--events/",
    "https://www.eventbrite.com/d/canada--toronto/tech--events/",
    "https://www.eventbrite.com/d/germany--berlin/tech--events/",
    "https://www.eventbrite.com/d/india--bengaluru/tech--events/",
    "https://www.eventbrite.com/d/singapore--singapore/tech--events/",
    # single-vendor / community pages
    "https://www.postman.com/events/",
    # Dubai / MENA directories
    "https://roboosh.ae/events",
]


def iter_ld_nodes(node):
    if isinstance(node, list):
        for n in node:
            yield from iter_ld_nodes(n)
    elif isinstance(node, dict):
        t = node.get('@type')
        types = t if isinstance(t, list) else [t]
        if any(isinstance(x, str) and x.endswith('Event') for x in types):
            yield node
        for key in ('@graph', 'itemListElement', 'item', 'subEvent'):
            if key in node:
                yield from iter_ld_nodes(node[key])


def location_of(node):
    loc = node.get('location')
    if isinstance(loc, list):
        loc = loc[0] if loc else None
    if isinstance(loc, str):
        return loc
    if not isinstance(loc, dict):
        return ''
    addr = loc.get('address')
    parts = []
    if isinstance(addr, dict):
        parts = [addr.get('addressLocality'), addr.get('addressRegion'), addr.get('addressCountry')]
        parts = [p.get('name') if isinstance(p, dict) else p for p in parts]
    elif isinstance(addr, str):
        parts = [addr]
    parts = [p for p in parts if p]
    if not parts and loc.get('name'):
        parts = [loc['name']]
    text = ', '.join(parts)
    if 'online' in (node.get('eventAttendanceMode') or '').lower() and not text:
        text = 'Online'
    return text or ('Online' if 'VirtualLocation' in str(loc.get('@type')) else '')


def fetch_page(url):
    resp = http_get(url)
    if not resp:
        return [], 0
    soup = BeautifulSoup(resp.text, 'html.parser')
    out, raw = [], 0
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or tag.get_text() or '')
        except Exception:
            continue
        for node in iter_ld_nodes(data):
            raw += 1
            name = node.get('name')
            start = parse_iso_date(node.get('startDate'))
            if not name or not start:
                continue
            end = parse_iso_date(node.get('endDate')) or start
            link = node.get('url') or ''
            link = urljoin(url, link) if link else url
            out.append((build_event(name, start, end, location_of(node), link), end))
    return out, raw


def main():
    events, raw_total = [], 0
    for url in SOURCES:
        evs, raw = fetch_page(url)
        print(f"[JSON-LD] {url} -> {raw} events")
        events.extend(evs)
        raw_total += raw
        time.sleep(0.5)
    finalize(events, "JSON-LD", "events_jsonld_generic.json", raw_total)


if __name__ == "__main__":
    main()
