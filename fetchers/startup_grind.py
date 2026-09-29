import urllib.request
import ssl
import json
import re
from datetime import datetime
import config
import time

# Startup Grind runs on the Bevy platform (same engine as the existing CNCF/GDG
# fetchers), so we reuse that API pagination pattern rather than scraping HTML.
API_URL = "https://www.startupgrind.com/api/event/"


def fetch_events_from_api():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    fetched_events = []
    raw_count = 0
    filtered_count = 0
    now_ts = datetime.now().timestamp()

    page = 1
    while True:
        url = f"{API_URL}?status=Published&page={page}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"[StartupGrind] Failed to fetch {url}: {e}")
            break

        results = data.get('results', [])
        if not results:
            break

        for item in results:
            raw_count += 1
            name = (item.get('title') or 'N/A').replace('|', '\\|')
            event_url = item.get('url') or ''
            start_date_str = item.get('start_date') or ''

            if not start_date_str:
                filtered_count += 1
                continue

            try:
                if len(start_date_str) > 19:
                    start_date_str = start_date_str[:19]
                dt = datetime.fromisoformat(start_date_str)
                if dt.date() < datetime.fromtimestamp(now_ts, dt.tzinfo).date():
                    filtered_count += 1
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                filtered_count += 1
                continue

            chapter = item.get('chapter') or {}
            city = chapter.get('city') or ''
            country = chapter.get('country_name') or ''

            if city and country:
                location = f"{city}, {country}"
            elif country:
                location = country
            elif city:
                location = city
            else:
                location = "Unknown"
            location = location.replace('|', '\\|')

            if not config.is_event_relevant(f"{name} {location}"):
                filtered_count += 1
                continue

            register = f"[↗]({event_url})" if event_url else "N/A"

            fetched_events.append({
                "name": name,
                "date": date_str,
                "location": location,
                "register": register,
                "line": f"| {name} | {date_str} | {location} | {register} |"
            })

        if not data.get('links', {}).get('next'):
            break

        page += 1
        time.sleep(0.5)

    print(f"[StartupGrind] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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

    out_file = "events_startup_grind.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
