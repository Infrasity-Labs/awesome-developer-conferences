import urllib.request
import ssl
from bs4 import BeautifulSoup
from datetime import datetime
import config
import re
import json

def fetch_events_from_api():
    base_url = "https://devopsdays.org/events"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch DevOpsDays: {e}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    
    events = []
    now_ts = datetime.now().timestamp()
    
    for ev in soup.select('a.events-page-event'):
        href = ev.get('href', '')
        if not href.startswith('/events/2026') and not href.startswith('/events/2027'):
            continue # Only grab current/next year
            
        url = "https://devopsdays.org" + href
        
        text = ev.text.strip().replace('\n', ' ')
        # text is like "Jul 4: Kraków"
        parts = text.split(':')
        if len(parts) < 2:
            continue
            
        date_raw = parts[0].strip()
        location_raw = parts[1].strip()
        
        # Extract year from URL
        year_match = re.search(r'/events/(\d{4})', href)
        year = year_match.group(1) if year_match else str(datetime.now().year)
        
        full_date_str = f"{date_raw} {year}"
        date_str = config.parse_date(full_date_str)
        
        if date_str != "9999-99-99":
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                if dt.timestamp() < now_ts:
                    continue
            except:
                pass
                
        name_clean = f"DevOpsDays {location_raw} {year}"
        
        location = f"{location_raw}"
        
        register = f"[↗]({url})"
        
        events.append({
            "name": name_clean,
            "date": date_str,
            "location": location,
            "url": url,
            "register": register,
            "line": f"| {name_clean} | {date_str} | {location} | {register} |"
        })
        
    return events

if __name__ == "__main__":
    print("Fetching events from DevOpsDays...")
    events = fetch_events_from_api()
    print(f"Found {len(events)} events matching criteria.")
    
    if not events:
        exit(0)

    out_file = "events_devopsdays.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")
