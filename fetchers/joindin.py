import os
import re
import json
import requests
from datetime import datetime
import config

def fetch_events_from_api():
    url = "https://api.joind.in/v2.1/events?filter=upcoming"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch data from joind.in: {e}")
        raise
        
    events = data.get('events', [])
    fetched_events = []
    
    for event in events:
        name = (event.get('name') or 'N/A').replace('|', '\\|')
        start_date_str = event.get('start_date')
        end_date_str = event.get('end_date')
        
        if not start_date_str:
            continue
            
        try:
            start_date = datetime.fromisoformat(start_date_str)
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str)
            else:
                end_date = start_date
        except Exception:
            continue
            
        if end_date.replace(tzinfo=None) < datetime.now():
            continue
            
        desc = (event.get('description') or '').lower()
        event_text = name.lower() + ' ' + desc
            
        link = event.get('website_uri') or event.get('href') or ''
        register = f"[↗]({link})" if link else "N/A"
        
        location = event.get('location') or event.get('tz_place') or 'Unknown'
        location = location.replace('|', '\\|')
        
        if start_date.date() != end_date.date():
            date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            date_str = start_date.strftime('%Y-%m-%d')
            
        fetched_events.append({
            "name": name,
            "date": date_str,
            "location": location,
            "register": register,
            "line": f"| {name} | {date_str} | {location} | {register} |"
        })
        
    return fetched_events

def main():
    print("Fetching events from joind.in...")
    fetched_events = fetch_events_from_api()
    print(f"Found {len(fetched_events)} upcoming relevant events on joind.in.")
    
    if not fetched_events:
        print("No new events to add from joind.in.")
        return

    import json
    out_file = "events_joindin.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")

if __name__ == "__main__":
    main()
