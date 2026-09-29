import re
import json
import time
from datetime import datetime
import config
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install requests and beautifulsoup4")
    exit(1)

BASE_URL = "https://www.sesamers.com/events/"
MONTHS_AHEAD = 6


def _month_url(dt):
    return f"{BASE_URL}?month={dt.strftime('%Y-%m')}"


def _add_months(dt, n):
    month = dt.month - 1 + n
    year = dt.year + month // 12
    month = month % 12 + 1
    return dt.replace(year=year, month=month, day=1)


def fetch_events_from_api():
    now = datetime.now()
    fetched_events = []
    raw_count = 0
    filtered_count = 0
    seen_urls = set()

    for i in range(MONTHS_AHEAD):
        month_dt = _add_months(now.replace(day=1), i)
        url = _month_url(month_dt)
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Sesamers] Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.select('article.evl')

        for card in cards:
            raw_count += 1
            h3 = card.find('h3')
            if not h3 or not h3.find('a'):
                filtered_count += 1
                continue
            name = h3.get_text(strip=True).replace('|', '\\|')

            dt_el = card.select_one('.dt')
            if not dt_el:
                filtered_count += 1
                continue
            day_part = dt_el.find('b')
            month_part = dt_el.find('span')
            if not day_part or not month_part:
                filtered_count += 1
                continue
            day_text = day_part.get_text(strip=True)
            month_text = month_part.get_text(strip=True)

            day_match = re.findall(r'\d+', day_text)
            if not day_match:
                filtered_count += 1
                continue
            start_day = int(day_match[0])
            end_day = int(day_match[-1])

            try:
                start_date = datetime.strptime(f"{start_day} {month_text} {month_dt.year}", "%d %b %Y")
                end_date = datetime.strptime(f"{end_day} {month_text} {month_dt.year}", "%d %b %Y")
            except Exception:
                filtered_count += 1
                continue

            if end_date.date() < now.date():
                filtered_count += 1
                continue

            loc_el = card.select_one('.wm2')
            location = loc_el.get_text(strip=True).replace('|', '\\|') if loc_el else "Unknown"

            reg_a = card.select_one('a.reg')
            internal_a = h3.find('a', href=True)
            link = reg_a['href'] if reg_a and reg_a.get('href') else (internal_a['href'] if internal_a else '')

            if link in seen_urls:
                continue

            desc_el = card.find('p')
            desc = desc_el.get_text(strip=True) if desc_el else ''

            if not config.is_event_relevant(f"{name} {desc}"):
                filtered_count += 1
                continue

            if start_date.date() != end_date.date():
                date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            else:
                date_str = start_date.strftime('%Y-%m-%d')

            register = f"[↗]({link})" if link else "N/A"
            seen_urls.add(link)

            fetched_events.append({
                "name": name,
                "date": date_str,
                "location": location,
                "register": register,
                "line": f"| {name} | {date_str} | {location} | {register} |"
            })

        time.sleep(0.5)

    print(f"[Sesamers] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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

    out_file = "events_sesamers.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
