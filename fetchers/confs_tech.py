import urllib.request
import json
import re
import ssl
from datetime import datetime
import config

# Confs.tech (https://confs.tech) is a React SPA with no data of its own in the
# raw HTML - its event data actually lives in a public GitHub repo as per-topic
# JSON files (conferences/<year>/<topic>.json). We fetch that raw JSON directly
# instead of scraping the site.
CONTENTS_API = "https://api.github.com/repos/tech-conferences/conference-data/contents/conferences/{year}"
RAW_BASE = "https://raw.githubusercontent.com/tech-conferences/conference-data/master/conferences/{year}/{topic}"


def _fetch_json(url, ctx):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))


def fetch_events_from_api():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    now = datetime.now()
    years = [now.year, now.year + 1]

    fetched_events = []
    raw_count = 0
    filtered_count = 0
    seen_urls = set()

    for year in years:
        try:
            topics = _fetch_json(CONTENTS_API.format(year=year), ctx)
        except Exception as e:
            print(f"[ConfsTech] Failed to list topics for {year}: {e}")
            continue

        for topic_entry in topics:
            topic_name = topic_entry.get('name')
            if not topic_name or not topic_name.endswith('.json'):
                continue

            try:
                events = _fetch_json(RAW_BASE.format(year=year, topic=topic_name), ctx)
            except Exception as e:
                print(f"[ConfsTech] Failed to fetch {topic_name} ({year}): {e}")
                continue

            for event in events:
                raw_count += 1
                if not isinstance(event, dict):
                    filtered_count += 1
                    continue

                url = event.get('url') or ''
                if url in seen_urls:
                    continue

                name = (event.get('name') or 'N/A').replace('|', '\\|')
                start_date_str = event.get('startDate')
                end_date_str = event.get('endDate') or start_date_str

                if not start_date_str:
                    filtered_count += 1
                    continue

                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                except Exception:
                    filtered_count += 1
                    continue

                if end_date.date() < now.date():
                    filtered_count += 1
                    continue

                if event.get('online'):
                    location = "Online"
                else:
                    city = event.get('city') or ''
                    country = event.get('country') or ''
                    if city and country:
                        location = f"{city}, {country}"
                    elif country:
                        location = country
                    elif city:
                        location = city
                    else:
                        location = "Unknown"
                location = location.replace('|', '\\|')

                if start_date.date() != end_date.date():
                    date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                else:
                    date_str = start_date.strftime('%Y-%m-%d')

                register = f"[↗]({url})" if url else "N/A"

                seen_urls.add(url)
                fetched_events.append({
                    "name": name,
                    "date": date_str,
                    "location": location,
                    "register": register,
                    "line": f"| {name} | {date_str} | {location} | {register} |"
                })

    print(f"[ConfsTech] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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

    out_file = "events_confs_tech.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")


if __name__ == "__main__":
    main()
