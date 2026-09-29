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

URL = "https://www.inkle.ai/global-conferences-tracker"

# The site uses short city abbreviations in its location chip; expand the
# common ones so aggregate.py's region matcher (which expects full city names)
# routes these correctly instead of falling back to Virtual/Online.
LOCATION_EXPANSIONS = {
    "sf": "San Francisco",
    "nyc": "New York",
    "la": "Los Angeles",
}


def _expand_location(text):
    key = text.strip().lower()
    return LOCATION_EXPANSIONS.get(key, text.strip())


def fetch_events_from_api():
    try:
        resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Inkle] Failed to fetch {URL}: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    cards = soup.select('a.events_item-link')

    fetched_events = []
    raw_count = 0
    filtered_count = 0
    now = datetime.now()

    for card in cards:
        raw_count += 1
        h3 = card.find('h3')
        date_el = card.select_one('.events_date-wrapper .text-size-small')
        loc_el = card.select_one('.events_location-wrapper .text-size-small')
        link = card.get('href') or ''

        if not h3:
            filtered_count += 1
            continue
        name = h3.get_text(strip=True).replace('|', '\\|')

        date_text = date_el.get_text(strip=True) if date_el else ''
        try:
            dt = datetime.strptime(date_text, "%B %d, %Y")
        except Exception:
            filtered_count += 1
            continue

        if dt.date() < now.date():
            filtered_count += 1
            continue

        location = _expand_location(loc_el.get_text(strip=True)) if loc_el else "Unknown"
        location = location.replace('|', '\\|')

        # No keyword filter: this tracker is already curated for SaaS/fintech/AI
        # founders and operators, so its entries (Stripe Sessions, Money20/20,
        # etc.) are relevant even when the title has no literal "tech"/"startup".
        date_str = dt.strftime("%Y-%m-%d")
        register = f"[↗]({link})" if link else "N/A"

        fetched_events.append({
            "name": name,
            "date": date_str,
            "location": location,
            "register": register,
            "line": f"| {name} | {date_str} | {location} | {register} |"
        })

    print(f"[Inkle] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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

    out_file = "events_inkle.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
