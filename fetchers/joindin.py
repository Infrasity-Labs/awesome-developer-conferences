import os
import re
import json
import requests
from datetime import datetime
import config

def fetch_events_from_api():
    url = "https://api.joind.in/v2.1/events"
    
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
        if not config.is_event_relevant(event_text):
            continue
            
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
        
    with open('README.md', 'r', encoding='utf-8') as f:
        readme_content = f.read()
        
    regions = {
        'Asia': [],
        'Australia': [],
        'Europe': [],
        'North America': [],
        'South America': [],
        'Virtual/Online': []
    }
    
    for event in fetched_events:
        region = config.determine_region(event['location'])
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
                 if name_clean in existing_names:
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
                        parsed = config.parse_date(date_str)
                        try:
                            return datetime.strptime(parsed, '%Y-%m-%d')
                        except:
                            pass
                    return datetime.max
                
                existing_rows.sort(key=extract_date)
                new_table_content = '\n'.join(existing_rows) + '\n'
                readme_content = readme_content[:match.start()] + header_and_table_header + new_table_content + readme_content[match.end():]
                
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
        
    print("Done integrating joind.in events.")

if __name__ == "__main__":
    main()
