import json
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from generic_common import http_get, build_event, finalize, clean

# Server-rendered event listing pages without structured data. Each card is
# detected heuristically: the smallest element holding exactly one date, one
# link and a heading/link text. Add a URL here to add a source.
SOURCES = [
    "https://www.python.org/events/",
    "https://www.php.net/conferences/",
    "https://www.infoq.com/events/",
    "https://tech.eu/events",
    "https://www.docker.com/events/",
    "https://aws.amazon.com/events/community-day/",
    "https://www.sanity.io/events",
    "https://www.atlassian.com/company/events",
    "https://www.cockroachlabs.com/events/",
    "https://www.pagerduty.com/events/",
    "https://www.fastly.com/events",
    "https://www.tigera.io/events/",
    "https://www.itnews.com.au/events",
    "https://www.startupticker.ch/en/events",
    "https://www.nextevent.ai/united-arab-emirates/dubai",
    "https://exposignal.com/",
    "https://about.gitlab.com/events/",
    "https://lablab.ai/event",
    "https://qconferences.com/",
    "https://go.dev/wiki/Conferences",
    "https://vercel.com/events",
    "https://www.cio.com/events/",
    "https://www.csoonline.com/events/",
    "https://www.dataversity.net/events/",
    "https://www.openstack.org/events/",
    "https://www.sans.org/cyber-security-training-events/",
    "https://www.terrapinn.com/exhibition/",
    "https://inc42.com/events/",
    "https://redis.io/events/",
    "https://snyk.io/events/",
    "https://www.canonical.com/events",
    "https://www.nasscom.in/events",
    "https://www.netlify.com/events/",
    "https://www.techcentral.co.za/events",
    "https://aliens.zone/events",
    "https://eventstopten.com/",
    "https://dubaicon.app/en/events",
    "https://eventify.io/",
    "https://www.opensesame.com/events",
]

# Sites that only list developer/tech events: skip the keyword filter.
DEV_ONLY = ("python.org", "php.net", "infoq.com", "docker.com", "aws.amazon.com",
            "sanity.io", "atlassian.com", "cockroachlabs.com", "pagerduty.com",
            "fastly.com", "tigera.io", "go.dev", "gitlab.com", "lablab.ai",
            "qconferences.com", "vercel.com", "openstack.org", "sans.org", "netlify.com",
            "snyk.io", "redis.io", "canonical.com")

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
MON = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?'
# "Oct 22, 2026", "22 October 2026", "Oct 22 2026"
DATE_PATTERNS = [
    re.compile(rf'\b{MON}\s+(\d{{1,2}})(?:\s*[-–]\s*\d{{1,2}})?,?\s+(20\d{{2}})\b', re.I),
    re.compile(rf'\b(\d{{1,2}})(?:\s*[-–]\s*\d{{1,2}})?\s+{MON},?\s+(20\d{{2}})\b', re.I),
]
ISO = re.compile(r'\b(20\d{2})-(\d{2})-(\d{2})\b')


def find_dates(text):
    found = []
    for m in ISO.finditer(text):
        found.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    m = DATE_PATTERNS[0].search(text)
    if m:
        found.append((int(m.group(3)), MONTHS[m.group(1).lower()[:3]], int(m.group(2))))
    m = DATE_PATTERNS[1].search(text)
    if m:
        found.append((int(m.group(3)), MONTHS[m.group(2).lower()[:3]], int(m.group(1))))
    out = set()
    for y, mo, d in found:
        try:
            out.add(datetime(y, mo, d).date())
        except ValueError:
            pass
    return out


def card_name(el):
    for tag in ('h1', 'h2', 'h3', 'h4', 'h5'):
        h = el.find(tag)
        if h and h.get_text(strip=True):
            return clean(h.get_text(' ', strip=True))
    a = el.find('a', href=True)
    return clean(a.get_text(' ', strip=True)) if a else ''


def fetch_page(url):
    resp = http_get(url)
    if not resp:
        return [], 0
    soup = BeautifulSoup(resp.text, 'html.parser')
    for t in soup(['script', 'style', 'nav', 'footer', 'header']):
        t.decompose()
    out, raw, seen = [], 0, set()
    for el in soup.find_all(['article', 'li', 'div', 'tr', 'section']):
        text = el.get_text(' ', strip=True)
        if not (25 <= len(text) <= 500):
            continue
        dates = find_dates(text)
        if len(dates) != 1 or not el.find('a', href=True):
            continue
        # keep only the smallest matching element
        if any(len(c.get_text(' ', strip=True)) >= 25 and find_dates(c.get_text(' ', strip=True))
               and c.find('a', href=True) for c in el.find_all(['article', 'li', 'div', 'tr'], recursive=True)):
            continue
        name = card_name(el)
        if name.startswith('http'):
            name = urlparse(name).netloc.replace('www.', '')
        if not (6 <= len(name) <= 150):
            continue
        raw += 1
        start = next(iter(dates))
        link = urljoin(url, el.find('a', href=True)['href'])
        key = (name.lower(), start)
        if key in seen:
            continue
        seen.add(key)
        out.append((build_event(name, start, start, '', link), start))
    return out, raw


def main():
    scoped, filtered, raw_total = [], [], 0
    for url in SOURCES:
        evs, raw = fetch_page(url)
        print(f"[Cards] {url} -> {len(evs)} cards")
        (scoped if any(d in url for d in DEV_ONLY) else filtered).extend(evs)
        raw_total += raw
        time.sleep(0.5)
    kept = finalize(filtered, "Cards", "events_cards_generic.json", raw_total)
    kept_scoped = finalize(scoped, "Cards-dev", "events_cards_generic.json", 0, relevance=False)
    merged = kept + kept_scoped
    with open("events_cards_generic.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    print(f"Saved {len(merged)} events to events_cards_generic.json")


if __name__ == "__main__":
    main()
