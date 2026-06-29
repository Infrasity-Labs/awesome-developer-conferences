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
    now_ts = datetime.now().timestamp()
    
    page = 1
    while True:
        url = f"{base_api_url}?status=Published&page={page}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            break
            
        results = data.get('results', [])
        if not results:
            break
            
        for item in results:
            name = item.get('title') or 'N/A'
            event_url = item.get('url') or ''
            start_date_str = item.get('start_date') or ''
            
            if not start_date_str:
                continue
                
            try:
                # e.g., 2027-01-22T08:00:00-05:00
                if len(start_date_str) > 19:
                    start_date_str = start_date_str[:19] # Strip timezone offset for simple iso format
                dt = datetime.fromisoformat(start_date_str)
                if dt.timestamp() < now_ts:
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            except:
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
                
            # No keyword filter needed for CNCF / GDG if we want them all, 
            # but we can pass through config.is_event_relevant just to be safe.
            # CNCF events are always relevant.
            
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
            
        if not data.get('links', {}).get('next'):
            break
            
        page += 1
        time.sleep(1)
        
    return events

if __name__ == "__main__":
    print("Fetching events from CNCF...")
    events = fetch_bevy_events("https://community2.cncf.io/api/event/")
    print(f"Found {len(events)} events matching criteria.")
    
    if not events:
        exit(0)

    out_file = "events_cncf.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")
