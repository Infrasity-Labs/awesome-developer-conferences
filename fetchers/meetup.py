import urllib.request
import ssl
import json
from datetime import datetime
import config
import re

def fetch_events_from_api():
    base_url = "https://www.meetup.com/find/?keywords=developer&source=EVENTS"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch Meetup: {e}")
        return []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
    except ImportError:
        print("Please install beautifulsoup4")
        return []

    fetched_events = []
    now_ts = datetime.now().timestamp()
    
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
                # e.g., 2026-07-15T18:00:00+05:30
                dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                if dt.timestamp() < now_ts:
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            except:
                continue
                
            event_text = name + " " + desc
            if not config.is_event_relevant(event_text):
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
            
            fetched_events.append({
                "name": name_clean,
                "date": date_str,
                "location": location,
                "register": register,
                "line": f"| {name_clean} | {date_str} | {location} | {register} |"
            })
            
    return fetched_events

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
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
        
    regions = {
        'Asia': [],
        'Australia': [],
        'Europe': [],
        'North America': [],
        'South America': [],
        'Virtual/Online': []
    }
    
    for event in events:
        region = determine_region(event['location'])
        if region in regions:
            regions[region].append(event)
            
    for region, region_events in regions.items():
        if not region_events:
            continue
            
        pattern = re.compile(rf"(### {region}\n.*?\| Event Name.*?\|\n\|---.*?\|\n)(.*?)(?=\n### |\Z)", re.DOTALL)
        match = pattern.search(readme_content)
        
        if match:
            header_and_table_header = match.group(1)
            existing_table_content = match.group(2)
            
            existing_rows = existing_table_content.strip().split('\n')
            if existing_rows == ['']:
                existing_rows = []
                
            existing_names = []
            for row in existing_rows:
                parts = row.split('|')
                if len(parts) >= 3:
                    name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', parts[1].strip()).lower()
                    existing_names.append(name_clean)
                    
            new_rows_added = 0
            for event in region_events:
                name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', event['name']).lower()
                is_duplicate = False
                for ex_name in existing_names:
                    if name_clean in ex_name or ex_name in name_clean:
                        is_duplicate = True
                        break
                        
                if not is_duplicate:
                    existing_rows.append(event['line'])
                    existing_names.append(name_clean)
                    new_rows_added += 1
                    
            if new_rows_added > 0:
                def extract_date(row):
                    parts = row.split('|')
                    if len(parts) >= 4:
                        date_str = parts[2].strip().split(' to ')[0].strip()
                        try:
                            return datetime.strptime(date_str, "%Y-%m-%d")
                        except:
                            pass
                    return datetime.max
                
                existing_rows.sort(key=extract_date)
                new_table_content = '\n'.join(existing_rows) + '\n'
                readme_content = readme_content[:match.start()] + header_and_table_header + new_table_content + readme_content[match.end():]
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("Done integrating Meetup events.")
