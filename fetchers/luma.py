import urllib.request
import ssl
import json
import re
from datetime import datetime
import config

def fetch_events_from_api():
    KEYWORDS = ["developer", "kubernetes", "devops", "python", "ai", "software engineering", "backend", "cloud native"]
    LOCATIONS = [
        ("San Francisco", 37.7749, -122.4194),
        ("New York", 40.7128, -74.0060),
        ("London", 51.5074, -0.1278),
        ("Berlin", 52.5200, 13.4050),
        ("Bangalore", 12.9716, 77.5946),
        ("Singapore", 1.3521, 103.8198),
        ("Tokyo", 35.6895, 139.6917),
        ("Sydney", -33.8688, 151.2093),
        ("Paris", 48.8566, 2.3522),
        ("Toronto", 43.6510, -79.3470)
    ]
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    events = []
    seen_api_ids = set()
    import time
    for kw in KEYWORDS:
        kw_enc = urllib.parse.quote(kw)
        for loc_name, lat, lon in LOCATIONS:
            api_url = f"https://api.luma.com/discover/get-paginated-events?keyword={kw_enc}&latitude={lat}&longitude={lon}&pagination_limit=50"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if 'entries' in data:
                        for entry in data['entries']:
                            event = entry.get('event')
                            if event and event.get('api_id') not in seen_api_ids:
                                seen_api_ids.add(event['api_id'])
                                events.append(entry)
                time.sleep(0.5)
            except Exception as e:
                print(f"Failed to fetch Luma API for {kw} at {loc_name}: {e}")
                continue

    now_ts = datetime.now().timestamp()
    
    fetched_events = []
    for entry in events:
        item = entry.get('event') or {}
        calendar = entry.get('calendar') or {}
        
        name = item.get('name') or 'N/A'
        desc = calendar.get('description_short') or ''
        url_id = item.get('url')
        url = f"https://lu.ma/{url_id}" if url_id else ''
        start_date_str = item.get('start_at') or ''
        
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
            
        # Location logic
        location = "Unknown"
        if item.get('location_type') == 'online' or (item.get('virtual_info') or {}).get('has_access'):
            location = "Virtual/Online"
        elif item.get('geo_address_info') and item['geo_address_info'].get('city'):
            location = item['geo_address_info'].get('city')
            if item['geo_address_info'].get('country_code'):
                location += f", {item['geo_address_info'].get('country_code')}"
        elif item.get('timezone'):
            location = item.get('timezone', 'Unknown')
            if '/' in location:
                location = location.split('/')[-1].replace('_', ' ')
            
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
    if any(x in loc_lower for x in ['usa', 'canada', 'united states', 'us', 'new york', 'san francisco']):
        return 'North America'
    if any(x in loc_lower for x in ['uk', 'germany', 'austria', 'france', 'portugal', 'czechia', 'czech republic', 'spain', 'belgium', 'netherlands', 'london', 'berlin', 'paris']):
        return 'Europe'
    if any(x in loc_lower for x in ['india', 'japan', 'china', 'uae', 'singapore', 'bangalore', 'tokyo']):
        return 'Asia'
    if any(x in loc_lower for x in ['australia', 'new zealand', 'sydney', 'melbourne']):
        return 'Australia'
    if any(x in loc_lower for x in ['brazil', 'peru', 'argentina', 'colombia', 'chile', 'são paulo', 'lima', 'buenos aires']):
        return 'South America'
    return 'Virtual/Online'
if __name__ == "__main__":
    print("Fetching events from Luma...")
    events = fetch_events_from_api()
    print(f"Found {len(events)} events matching criteria.")
    
    if not events:
        exit(0)

    import json
    out_file = "events_luma.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")

