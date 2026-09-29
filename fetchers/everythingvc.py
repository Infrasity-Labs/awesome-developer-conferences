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

URL = "https://everythingvc.eu/events"
MONTH_NUM = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
MONTH_RE = '|'.join(MONTH_NUM.keys())
# aria-label formats: "28 Sept" or "28 to 29 Sept" or "30 Sept to 1 Oct"
SAME_MONTH_RE = re.compile(rf'(\d{{1,2}})(?:\s+to\s+(\d{{1,2}}))?\s+({MONTH_RE})$')
CROSS_MONTH_RE = re.compile(rf'(\d{{1,2}})\s+({MONTH_RE})\s+to\s+(\d{{1,2}})\s+({MONTH_RE})$')


def _month_num(name):
    return MONTH_NUM.get(name)


def _parse_date_range(aria_label, year):
    aria_label = aria_label.strip()
    m = CROSS_MONTH_RE.match(aria_label)
    if m:
        d1, mo1, d2, mo2 = m.groups()
        month1 = _month_num(mo1)
        month2 = _month_num(mo2)
        if not month1 or not month2:
            return None, None
        end_year = year + 1 if month2 < month1 else year
        try:
            start = datetime(year, month1, int(d1))
            end = datetime(end_year, month2, int(d2))
        except ValueError:
            return None, None
        return start, end

    m = SAME_MONTH_RE.match(aria_label)
    if m:
        d1, d2, mo = m.groups()
        month = _month_num(mo)
        if not month:
            return None, None
        try:
            start = datetime(year, month, int(d1))
            end = datetime(year, month, int(d2)) if d2 else start
        except ValueError:
            return None, None
        return start, end

    return None, None


def fetch_events_from_api():
    try:
        resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[EverythingVC] Failed to fetch {URL}: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    items = soup.select('article.event-list-item')

    fetched_events = []
    raw_count = 0
    filtered_count = 0
    now = datetime.now()

    for item in items:
        raw_count += 1
        h3 = item.find('h3')
        date_el = item.select_one('.event-list-date')
        meta_spans = item.select('.event-list-meta span')
        a = item.select_one('a.event-list-link')

        if not h3 or not date_el or not a:
            filtered_count += 1
            continue

        name = h3.get_text(strip=True).replace('|', '\\|')
        aria_label = date_el.get('aria-label') or date_el.get_text(strip=True)

        year_match = re.search(r'\b(20\d{2})\b', name)
        year = int(year_match.group(1)) if year_match else now.year

        start_date, end_date = _parse_date_range(aria_label, year)
        if not start_date:
            filtered_count += 1
            continue

        if end_date.date() < now.date():
            filtered_count += 1
            continue

        if meta_spans:
            location = re.sub(r'\s*,\s*', ', ', meta_spans[0].get_text(' ', strip=True)).replace('|', '\\|')
        else:
            location = "Unknown"
        link = a.get('href') or ''

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

    print(f"[EverythingVC] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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

    out_file = "events_everythingvc.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
