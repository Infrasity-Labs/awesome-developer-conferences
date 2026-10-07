import re
from datetime import datetime, timedelta

from generic_common import http_get, build_event, finalize, clean

# Public ICS calendar feeds. Add a URL here to add a source.
SOURCES = [
    "https://central.wordcamp.org/calendar.ics",
]


def unfold(text):
    return re.sub(r'\r?\n[ \t]', '', text)


def unescape(value):
    return value.replace('\\n', ' ').replace('\\,', ',').replace('\;', ';').replace('\\\\', '\\')


def parse_ics_date(value):
    m = re.search(r'(\d{4})(\d{2})(\d{2})', value or '')
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
    except ValueError:
        return None


def parse_ics(text):
    for block in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', unfold(text), re.S):
        props = {}
        for line in block.splitlines():
            if ':' not in line:
                continue
            key, _, val = line.partition(':')
            props.setdefault(key.split(';')[0].upper(), val.strip())
        yield props


def fetch_feed(url):
    resp = http_get(url)
    if not resp:
        return [], 0
    out, raw = [], 0
    for p in parse_ics(resp.text):
        raw += 1
        start = parse_ics_date(p.get('DTSTART'))
        if not start or not p.get('SUMMARY'):
            continue
        end = parse_ics_date(p.get('DTEND')) or start
        # all-day DTEND is exclusive
        if len(p.get('DTEND', '')) == 8 and end > start:
            end -= timedelta(days=1)
        link = p.get('URL') or url
        out.append((build_event(unescape(p['SUMMARY']), start, end, unescape(p.get('LOCATION', '')), link), end))
    return out, raw


def main():
    events, raw_total = [], 0
    for url in SOURCES:
        evs, raw = fetch_feed(url)
        print(f"[ICS] {url[:70]} -> {raw} events")
        events.extend(evs)
        raw_total += raw
    finalize(events, "ICS", "events_ics_generic.json", raw_total)


if __name__ == "__main__":
    main()
