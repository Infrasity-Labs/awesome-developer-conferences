import re
import json
from datetime import datetime
import config
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install requests and beautifulsoup4")
    exit(1)

URL = "https://platformengineering.org/events"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
DATE_RE = re.compile(
    r'(' + '|'.join(MONTHS) + r')\s+(\d{1,2}),\s+(\d{4})'
)


def fetch_events_from_api():
    try:
        resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[PlatformEngineering] Failed to fetch {URL}: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    items = soup.select('.w-dyn-item')

    fetched_events = []
    raw_count = 0
    filtered_count = 0
    now = datetime.now()

    for item in items:
        raw_count += 1
        heading = item.select_one('.heading-style-h6') or item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not heading:
            filtered_count += 1
            continue
        name = heading.get_text(strip=True).replace('|', '\\|')

        text = item.get_text(' ', strip=True)
        m = DATE_RE.search(text)
        if not m:
            filtered_count += 1
            continue

        month, day, year = m.groups()
        try:
            dt = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
        except Exception:
            filtered_count += 1
            continue

        if dt.date() < now.date():
            filtered_count += 1
            continue

        a = item.find('a', href=True)
        link = a['href'] if a else ''
        if link and link.startswith('/'):
            link = "https://platformengineering.org" + link

        # No keyword filter needed: every event on platformengineering.org/events
        # is platform-engineering content by definition (same reasoning bigevent.py
        # uses for its already-topic-scoped source URL).
        date_str = dt.strftime("%Y-%m-%d")
        location = "Online"
        register = f"[↗]({link})" if link else "N/A"

        fetched_events.append({
            "name": name,
            "date": date_str,
            "location": location,
            "register": register,
            "line": f"| {name} | {date_str} | {location} | {register} |"
        })

    print(f"[PlatformEngineering] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
    return fetched_events


def get_continent(location):
    return config.determine_region(location)


def normalize_name(name):
    return name.lower().replace(' ', '').replace('-', '').replace('+', '')


def parse_date(date_str):
    match = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
    if match:
        return match.group(0)
    return "9999-99-99"


def main():
    fetched_events = fetch_events_from_api()

    out_file = "events_platform_engineering.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
