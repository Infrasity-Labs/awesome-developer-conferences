import urllib.request
import ssl
import json
import re
from datetime import datetime
import config

def fetch_events_from_api():
    base_url = "https://lu.ma/explore"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch Luma: {e}")
        return []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
    except ImportError:
        print("Please install beautifulsoup4")
        return []

    events = []
    now_ts = datetime.now().timestamp()
    
    # Luma embeds state in __NEXT_DATA__
    script = soup.find('script', id='__NEXT_DATA__')
    if not script:
        return []
        
    try:
        data = json.loads(script.string)
    except:
        return []
        
    # Recursively search for 'event' objects in the json tree
    def find_events(obj):
        found = []
        if isinstance(obj, dict):
            if 'event' in obj and isinstance(obj['event'], dict) and 'name' in obj['event']:
                found.append(obj['event'])
            for v in obj.values():
                found.extend(find_events(v))
        elif isinstance(obj, list):
            for i in obj:
                found.extend(find_events(i))
        return found
        
    events = find_events(data)
    
    for item in events:
        name = item.get('name') or 'N/A'
        desc = item.get('description_short') or ''
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
        if not config.is_event_relevant(event_text):
            continue
            
        # Location logic
        location = "Unknown"
        if item.get('geo_latitude') and item.get('geo_longitude'):
            location = item.get('timezone', 'Unknown')
            if '/' in location:
                location = location.split('/')[-1].replace('_', ' ')
        elif item.get('is_online'):
            location = "Virtual/Online"
            
        register = f"[↗]({url})" if url else "N/A"
        name_clean = name.replace('|', '\\|')
        
        events.append({
            "name": name_clean,
            "date": date_str,
            "location": location,
            "register": register,
            "line": f"| {name_clean} | {date_str} | {location} | {register} |"
        })
            
    return events

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

