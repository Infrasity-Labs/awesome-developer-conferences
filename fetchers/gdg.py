import urllib.request
import urllib.parse
import ssl
import json
from datetime import datetime
import config
import time

def fetch_bevy_events(base_api_url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    events = []
    raw_count = 0
    filtered_count = 0
    now_ts = datetime.now().timestamp()
    
    page = 1
    max_pages = 200 # Safety limit
    while page <= max_pages:
        url = f"{base_api_url}?status=Published&page={page}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            break
            
        if not isinstance(data, dict):
            break
        results = data.get('results', [])
        if not results:
            break
            
        past_events_count = 0
        for item in results:
            raw_count += 1
            name = item.get('title') or 'N/A'
            event_url = item.get('url') or ''
            start_date_str = item.get('start_date') or ''
            
            if not start_date_str:
                filtered_count += 1
                continue
                
            try:
                # e.g., 2027-01-22T08:00:00-05:00
                if len(start_date_str) > 19:
                    start_date_str = start_date_str[:19] # Strip timezone offset for simple iso format
                dt = datetime.fromisoformat(start_date_str)
                if dt.date() < datetime.fromtimestamp(now_ts, dt.tzinfo).date():
                    past_events_count += 1
                    filtered_count += 1
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            except:
                filtered_count += 1
                continue
                
            chapter = item.get('chapter') or {}
            city = chapter.get('city') or ''
            country = chapter.get('country_name') or ''
            
            location = "Online"
            if city and country:
                location = f"{city}, {country}"
            elif country:
                location = country
            elif city:
                location = city
            else:
                location = "Unknown"
                
            register = f"[↗]({event_url})" if event_url else "N/A"
            name_clean = name.replace('|', '\\|')
            
            events.append({
                "name": name_clean,
                "date": date_str,
                "location": location,
                "url": event_url,
                "register": register,
                "line": f"| {name_clean} | {date_str} | {location} | {register} |"
            })
            
        # If the entire page was past events, we can stop fetching further pages!
        future_events_count = 0
        for item in results:
            start_date_str = item.get('start_date') or ''
            if not start_date_str:
                continue
            try:
                if len(start_date_str) > 19:
                    start_date_str = start_date_str[:19]
                dt = datetime.fromisoformat(start_date_str)
                if dt.timestamp() >= now_ts:
                    future_events_count += 1
            except:
                continue
        if future_events_count == 0:
            print(f'Reached past events on page {page}. Stopping.')
            break
            
        if not data.get('links', {}).get('next'):
            break
            
        page += 1
        time.sleep(1)
        
    print(f"[GDG] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(events)}")
    return events

if __name__ == "__main__":
    print("Fetching events from GDG...")
    events = fetch_bevy_events("https://gdg.community.dev/api/event/")
    print(f"Found {len(events)} events matching criteria.")
    
    if not events:
        exit(0)

    out_file = "events_gdg.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")
