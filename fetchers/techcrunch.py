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

URL = "https://techcrunch.com/events/"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTH_RE = '|'.join(MONTHS)
# "October 13 – 15, 2026" or "November 4, 2026"
RANGE_RE = re.compile(rf'({MONTH_RE})\s+(\d{{1,2}})\s*[–\-]\s*(\d{{1,2}}),\s*(\d{{4}})')
SINGLE_RE = re.compile(rf'({MONTH_RE})\s+(\d{{1,2}}),\s*(\d{{4}})')


def fetch_events_from_api():
    try:
        resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[TechCrunch] Failed to fetch {URL}: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    # Only TechCrunch's own "Upcoming Events" section (li.tc_event) - the rest
    # of the page is a filterable "Past Events" archive, not useful here.
    items = soup.select('li.tc_event')

    fetched_events = []
    raw_count = 0
    filtered_count = 0
    now = datetime.now()

    for item in items:
        raw_count += 1
        title_el = item.select_one('.loop-card__title')
        date_el = item.select_one('.loop-card__date')
        loc_el = item.select_one('.loop-card__location')
        a = item.find('a', href=True)

        if not title_el or not date_el or not a:
            filtered_count += 1
            continue

        name = title_el.get_text(strip=True).replace('|', '\\|')
        date_text = date_el.get_text(strip=True)
        location = (loc_el.get_text(strip=True) if loc_el else 'Unknown').replace('|', '\\|')
        link = a['href']

        m = RANGE_RE.search(date_text)
        if m:
            month, start_day, end_day, year = m.groups()
            try:
                start_date = datetime.strptime(f"{month} {start_day} {year}", "%B %d %Y")
                end_date = datetime.strptime(f"{month} {end_day} {year}", "%B %d %Y")
            except Exception:
                filtered_count += 1
                continue
        else:
            m = SINGLE_RE.search(date_text)
            if not m:
                filtered_count += 1
                continue
            month, day, year = m.groups()
            try:
                start_date = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
                end_date = start_date
            except Exception:
                filtered_count += 1
                continue

        if end_date.date() < now.date():
            filtered_count += 1
            continue

        if start_date.date() != end_date.date():
            date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            date_str = start_date.strftime('%Y-%m-%d')

        register = f"[↗]({link})" if link else "N/A"

        fetched_events.append({
            "name": name,
            "date": date_str,
            "location": location,
            "register": register,
            "line": f"| {name} | {date_str} | {location} | {register} |"
        })

    print(f"[TechCrunch] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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

    out_file = "events_techcrunch.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
