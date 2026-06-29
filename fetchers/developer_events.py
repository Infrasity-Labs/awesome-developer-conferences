import os
import re
import urllib.request
import json
import ssl
from datetime import datetime
import config

def fetch_events_from_api():
    url = "https://developers.events/all-events.json"

    # Bypass SSL verification if there are local cert issues
    ctx = ssl._create_unverified_context()

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return []

    fetched_events = []
    for event in data:
        dates = event.get('date', [])
        if not dates:
            continue
        
        # Dates are in milliseconds, convert to seconds
        start_timestamp = dates[0] / 1000.0
        start_date = datetime.utcfromtimestamp(start_timestamp)
        end_timestamp = dates[-1] / 1000.0
        
        # Filter past events
        now_timestamp = datetime.now().timestamp()
        if end_timestamp < now_timestamp:
            continue
            
        # Match keywords against name and tags
        event_text = event.get('name', '').lower()
        tags = [tag.get('value', '').lower() for tag in (event.get('tags') or []) if isinstance(tag, dict)]
        event_text += ' ' + ' '.join(tags)
        
        if not config.is_event_relevant(event_text):
            continue

        name = (event.get('name') or 'N/A').replace('|', '\\|')
        location = (event.get('location') or 'N/A').replace('|', '\\|')
        link = event.get('hyperlink', '')
        
        if link:
            register = f"[↗]({link})"
        else:
            register = "N/A"
        
        if len(dates) > 1:
            end_date = datetime.utcfromtimestamp(end_timestamp)
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



def get_continent(location):
    return config.determine_region(location)

def normalize_name(name):
    return name.lower().replace(' ', '').replace('-', '').replace('+', '')

def parse_date(date_str):
    match = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
    if match:
        return match.group(0)
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "June", "July", "Sept"]
    if any(m in date_str for m in months):
        year_match = re.search(r'\d{4}', date_str)
        year = year_match.group(0) if year_match else "9999"
        
        for i, m in enumerate(months):
            if m in date_str:
                month = (i % 12) + 1
                return f"{year}-{month:02d}-01"
    
    return "9999-99-99"





def is_past_event(date_str):
    years = re.findall(r'\d{4}', date_str)
    if not years:
        return False
        
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month
    
    max_year = max(int(y) for y in years)
    if max_year < current_year:
        return True
        
    if max_year == current_year:
        iso_dates = re.findall(r'\d{4}-(\d{2})-\d{2}', date_str)
        if iso_dates:
            max_month = max(int(m) for m in iso_dates)
            if max_month < current_month:
                return True
            return False
            
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        found_months = []
        lower_date = date_str.lower()
        for i, m in enumerate(months):
            if m in lower_date:
                found_months.append(i + 1)
        if "june" in lower_date: found_months.append(6)
        if "july" in lower_date: found_months.append(7)
        if "sept" in lower_date: found_months.append(9)
        
        if found_months:
            max_month = max(found_months)
            if max_month < current_month:
                return True
                
    return False

def main():
    fetched_events = fetch_events_from_api()


    continents_events = {
        'Africa': [],
        'Asia': [],
        'Australia': [],
        'Europe': [],
        'North America': [],
        'Virtual/Online': [],
        'South America': []
    }

    import json
    out_file = "events_developer_events.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")

if __name__ == "__main__":
    main()
