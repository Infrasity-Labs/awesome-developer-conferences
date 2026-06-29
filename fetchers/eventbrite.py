import urllib.request
import ssl
import json
import re
from datetime import datetime
import config

def fetch_events_from_api():
    KEYWORDS = ["developer", "kubernetes", "devops", "python", "ai", "software-engineering", "backend", "cloud-native"]
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    all_events_data = []
    
    import time
    for kw in KEYWORDS:
        kw_enc = urllib.parse.quote(kw)
        base_url = f"https://www.eventbrite.com/d/online/{kw_enc}/"
        req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                html = response.read().decode('utf-8')
                all_events_data.append(html)
            time.sleep(1)
        except Exception as e:
            print(f"Failed to fetch Eventbrite for {kw}: {e}")
            continue

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
    except ImportError:
        print("Please install beautifulsoup4")
        return []

    fetched_events = []
    now_ts = datetime.now().timestamp()
    
    for html in all_events_data:
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except:
            continue
            
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
            except:
                continue
                
            if not isinstance(data, list):
                data = [data]
                
            for item in data:
                if not isinstance(item, dict) or item.get('@type') != 'Event':
                    continue
                    
                name = item.get('name') or 'N/A'
                desc = item.get('description') or ''
                url = item.get('url') or ''
                start_date_str = item.get('startDate') or ''
                
                if not start_date_str:
                    continue
                    
                try:
                    dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    if dt.timestamp() < now_ts:
                        continue
                    date_str = dt.strftime("%Y-%m-%d")
                except:
                    continue
                    
                event_text = name + " " + desc
                if not config.is_event_relevant(event_text):
                    continue
                    
                location = "Online" # Based on the /d/online URL
                
                register = f"[↗]({url})" if url else "N/A"
                name_clean = name.replace('|', '\\|')
                
                fetched_events.append({
                    "name": name_clean,
                    "date": date_str,
                    "location": location,
                    "url": url,
                    "register": register,
                    "line": f"| {name_clean} | {date_str} | {location} | {register} |"
                })
                
    # Deduplicate by URL
    unique_events = []
    seen_urls = set()
    for ev in fetched_events:
        if ev['url'] not in seen_urls:
            unique_events.append(ev)
            seen_urls.add(ev['url'])
            
    return unique_events

def determine_region(location):
    loc_lower = location.lower()
    if 'online' in loc_lower or 'virtual' in loc_lower:
        return 'Virtual/Online'
    return 'Virtual/Online'

if __name__ == "__main__":
    print("Fetching events from Eventbrite...")
    events = fetch_events_from_api()
    print(f"Found {len(events)} events matching criteria.")
    
    if not events:
        exit(0)

    import json
    out_file = "events_eventbrite.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")

