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
    ctx = ssl.create_default_context()

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return []  
    try:
         with urllib.request.urlopen(req, context=ctx) as response:
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
        'Online': [],
        'South America': []
    }

    # Read existing README to extract current events
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_lines = f.read().splitlines()
    current_continent = None
    in_events_section = False
    pre_events_lines = []
    post_events_lines = []
    existing_events = []

    for line in readme_lines:
        if line.startswith('## 📍 Event Schedule'):
            in_events_section = True
            pre_events_lines.append(line)
            continue
        
        if in_events_section:
            if line.startswith('---'):
                in_events_section = False
                post_events_lines.append(line)
                continue
            
            if line.startswith('### '):
                current_continent = line.replace('### ', '').strip()
                continue
                
            if line.startswith('|') and not line.startswith('| Event Name') and not line.startswith('|---') and not line.startswith('|------------'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    name = parts[1]
                    date_str = parts[2]
                    location = parts[3]
                    register = parts[4]
                    existing_events.append({
                        "name": name,
                        "date": date_str,
                        "location": location,
                        "register": register,
                        "continent": current_continent,
                        "line": line
                    })
            continue
            
        if not in_events_section:
            if current_continent is None:
                pre_events_lines.append(line)
            else:
                post_events_lines.append(line)

    # Combine existing and fetched events
    # Prune existing events that have completely passed
    existing_events = [ev for ev in existing_events if not is_past_event(ev['date'])]

    all_events = existing_events.copy()


    existing_normalized = [normalize_name(e['name']) for e in existing_events]

    for fe in fetched_events:
        cont = get_continent(fe['location'])
        norm_name = normalize_name(fe['name'])
        
        # If the event with same name already exists, update it? Or if it's already there, just ignore.
        # Let's replace the existing one with the updated info from the script.
        if norm_name in existing_normalized:
            # Update existing
            for i, ev in enumerate(all_events):
                if normalize_name(ev['name']) == norm_name:
                    all_events[i] = {
                        "name": fe['name'],
                        "date": fe['date'],
                        "location": fe['location'],
                        "register": fe['register'],
                        "continent": cont,
                        "line": fe['line']
                    }
        else:
            all_events.append({
                "name": fe['name'],
                "date": fe['date'],
                "location": fe['location'],
                "register": fe['register'],
                "continent": cont,
                "line": fe['line']
            })

    # Deduplicate before distribution
    all_events = config.deduplicate_events(all_events)

    # Distribute by continent
    for ev in all_events:
        if ev['continent'] in continents_events:
            continents_events[ev['continent']].append(ev)
        else:
            print(f"Unknown continent {ev['continent']} for event {ev['name']}")


    # Sort events in each continent by date
    for cont in continents_events:
        continents_events[cont].sort(key=lambda x: parse_date(x['date']))

    # Generate new README lines
    new_readme_lines = pre_events_lines.copy()

    for cont in sorted(continents_events.keys()):
        new_readme_lines.append(f"### {cont}")
        new_readme_lines.append("| Event Name | Date | Location | Register |")
        new_readme_lines.append("|------------|------|----------|----------|")
        for ev in continents_events[cont]:
            new_readme_lines.append(ev['line'])

    new_readme_lines.extend(post_events_lines)

    # Write out the new README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_readme_lines) + "\n")

    print("README.md updated successfully!")


if __name__ == "__main__":
    main()
