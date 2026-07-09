import urllib.request
import ssl
import json
from datetime import datetime
import config
import re
from bs4 import BeautifulSoup

def fetch_events_from_api():
    KEYWORDS = ["developer", "kubernetes", "devops", "python", "ai developer", "software engineering", "backend", "cloud native"]
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    all_events_data = []
    
    import time
    for kw in KEYWORDS:
        kw_enc = urllib.parse.quote(kw)
        base_url = f"https://www.meetup.com/find/?keywords={kw_enc}&source=EVENTS"
        req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                html = response.read().decode('utf-8')
                all_events_data.append(html)
            time.sleep(1) # delay to avoid rate limiting
        except Exception as e:
            print(f"Failed to fetch Meetup for {kw}: {e}")
            continue

    events = []
    raw_count = 0
    filtered_count = 0
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
                raw_count += 1
                if not isinstance(item, dict) or item.get('@type') != 'Event':
                    filtered_count += 1
                    continue
                    
                name = item.get('name') or 'N/A'
                desc = item.get('description') or ''
                url = item.get('url') or ''
                start_date_str = item.get('startDate') or ''
                
                if not start_date_str:
                    filtered_count += 1
                    continue
                    
                try:
                    # e.g., 2026-07-15T18:00:00+05:30
                    dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    if dt.date() < datetime.fromtimestamp(now_ts, dt.tzinfo).date():
                        filtered_count += 1
                        continue
                    date_str = dt.strftime("%Y-%m-%d")
                except:
                    filtered_count += 1
                    continue
                    
                event_text = name + " " + desc
                if not config.is_event_relevant(event_text):
                    filtered_count += 1
                    continue
                    
                location_data = item.get('location')
                location = "Online"
                if isinstance(location_data, dict):
                    if location_data.get('@type') == 'Place':
                        address = location_data.get('address')
                        if isinstance(address, dict):
                            city = address.get('addressLocality', '')
                            country = address.get('addressCountry', '')
                            location = f"{city}, {country}".strip(', ')
                        else:
                            location = location_data.get('name', 'Unknown')
                    elif location_data.get('@type') == 'VirtualLocation':
                        location = "Virtual/Online"
                        
                if not location:
                    location = "Unknown"
                    
                register = f"[↗]({url})" if url else "N/A"
                name_clean = name.replace('|', '\\|')
                
                events.append({
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
    for ev in events:
        if ev['url'] not in seen_urls:
            unique_events.append(ev)
            seen_urls.add(ev['url'])
            
    print(f"[Meetup] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(unique_events)}")
    return unique_events

def determine_region(location):
    loc_lower = location.lower()
    if 'online' in loc_lower or 'virtual' in loc_lower:
        return 'Virtual/Online'
    if any(x in loc_lower for x in ['usa', 'canada', 'united states', 'us']):
        return 'North America'
    if any(x in loc_lower for x in ['uk', 'germany', 'austria', 'france', 'portugal', 'czechia', 'czech republic', 'spain', 'belgium', 'netherlands']):
        return 'Europe'
    if any(x in loc_lower for x in ['india', 'japan', 'china', 'uae', 'singapore']):
        return 'Asia'
    if any(x in loc_lower for x in ['australia', 'new zealand']):
        return 'Australia'
    if any(x in loc_lower for x in ['brazil', 'peru', 'argentina', 'colombia', 'chile']):
        return 'South America'
    return 'Virtual/Online'

if __name__ == "__main__":
    print("Fetching events from Meetup...")
    events = fetch_events_from_api()
    print(f"Found {len(events)} events matching criteria.")
    import os

    import json
    out_file = "events_meetup.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")

