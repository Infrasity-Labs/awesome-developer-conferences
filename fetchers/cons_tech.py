import json
import os
import re
from datetime import datetime

# Define the keywords
keywords = [
    "developer relations", "devrel", "developer advocacy", "developer experience", 
    "developer marketing", "developer ecosystem", "go-to-market", "gtm", "b2b saas", 
    "product-led growth", "plg", "revenue operations", "revops", "api economy", 
    "api management", "api monetization", "developer tools", "devtools", "sdk", 
    "platform engineering", "observability", "cloud-native", "ai agents", "agentic ai", 
    "llm", "ai developer tools", "developer-first", "technical audience", 
    "call for papers", "cfp", "open source", "community-led growth", "saas scaling", 
    "developer portal", "api-first", "developer platform", "yc startup"
]

conferences_dir = "temp_confs_data/conferences"
fetched_events = []
today_str = datetime.now().strftime("%Y-%m-%d")

# Parse JSON files
for year_folder in os.listdir(conferences_dir):
    year_path = os.path.join(conferences_dir, year_folder)
    if os.path.isdir(year_path) and year_folder.isdigit() and int(year_folder) >= 2026:
        for topic_file in os.listdir(year_path):
            if topic_file.endswith(".json"):
                topic = topic_file.replace(".json", "")
                with open(os.path.join(year_path, topic_file), "r", encoding="utf-8") as f:
                    try:
                        events = json.load(f)
                    except json.JSONDecodeError:
                        continue
                    
                    for event in events:
                        start_date = event.get("startDate", "")
                        end_date = event.get("endDate", start_date)
                        
                        if not end_date or end_date < today_str:
                            continue
                            
                        # Keywords in name, topic, tags/city
                        event_text = (event.get("name", "") + " " + topic + " " + event.get("city", "")).lower()
                        if not any(kw.lower() in event_text for kw in keywords):
                            continue
                            
                        name = event.get("name", "N/A").replace('|', '\\|')
                        city = event.get("city", "").replace('|', '\\|')
                        country = event.get("country", "").replace('|', '\\|')
                        online = event.get("online", False)
                        
                        if city and country:
                            location = f"{city} ({country})"
                            if online:
                                location += " & Online"
                        elif online:
                            location = "Online"
                        else:
                            location = "N/A"
                            
                        url = event.get("url", "")
                        if url:
                            register_md = f"[↗]({url})"
                        else:
                            register_md = "N/A"
                            
                        if start_date != end_date and start_date and end_date:
                            date_str = f"{start_date} to {end_date}"
                        elif start_date:
                            date_str = start_date
                        else:
                            date_str = "TBA"
                            
                        line = f"| {name} | {date_str} | {location} | {register_md} |"
                        fetched_events.append({
                            "name": name,
                            "date": date_str,
                            "location": location,
                            "register": register_md,
                            "line": line
                        })

# Mapping location to continent
def get_continent(location):
    loc_lower = location.lower()
    if 'online' in loc_lower:
        if ' & online' not in loc_lower:
            return 'Online'
    if any(x in loc_lower for x in ['usa', 'canada', 'united states', 'mexico']):
        return 'North America'
    if any(x in loc_lower for x in ['uk', 'germany', 'austria', 'france', 'portugal', 'czechia', 'luxembourg', 'netherlands', 'poland', 'denmark', 'switzerland', 'belgium', 'ireland', 'italy', 'spain', 'sweden', 'norway', 'finland', 'united kingdom', 'romania']):
        return 'Europe'
    if any(x in loc_lower for x in ['brazil', 'peru', 'argentina', 'colombia', 'chile']):
        return 'South America'
    if any(x in loc_lower for x in ['vietnam', 'korea', 'china', 'japan', 'indonesia', 'india', 'qatar', 'singapore', 'taiwan', 'thailand', 'malaysia', 'philippines', 'uae', 'united arab emirates']):
        return 'Asia'
    if any(x in loc_lower for x in ['nigeria', 'south africa', 'kenya', 'egypt']):
        return 'Africa'
    if any(x in loc_lower for x in ['australia', 'new zealand']):
        return 'Australia'
    
    # Fallbacks
    if 'london' in loc_lower or 'munich' in loc_lower or 'berlin' in loc_lower or 'paris' in loc_lower or 'amsterdam' in loc_lower or 'prague' in loc_lower or 'vienna' in loc_lower:
        return 'Europe'
    if 'san francisco' in loc_lower or 'new york' in loc_lower or 'orlando' in loc_lower or 'los angeles' in loc_lower or 'salt lake city' in loc_lower or 'indianapolis' in loc_lower or 'california' in loc_lower or 'chicago' in loc_lower or 'boston' in loc_lower or 'vancouver' in loc_lower:
        return 'North America'
    if 'são paulo' in loc_lower:
        return 'South America'
    if 'hanoi' in loc_lower or 'tokyo' in loc_lower or 'seoul' in loc_lower or 'mumbai' in loc_lower or 'bengaluru' in loc_lower:
        return 'Asia'
    if 'lagos' in loc_lower:
        return 'Africa'
    if 'melbourne' in loc_lower or 'sydney' in loc_lower:
        return 'Australia'
    
    print(f"Warning: could not map location '{location}' to continent. Defaulting to 'Online'")
    return 'Online'

continents_events = {
    'Africa': [],
    'Asia': [],
    'Australia': [],
    'Europe': [],
    'North America': [],
    'Online': [],
    'South America': []
}

# Past events filter logic
def is_past(date_str, today_iso):
    matches = re.findall(r'\d{4}-\d{2}-\d{2}', date_str)
    if matches:
        return matches[-1] < today_iso
        
    year_match = re.search(r'\d{4}', date_str)
    if not year_match:
        return False
        
    year = int(year_match.group(0))
    today_year = int(today_iso[:4])
    if year < today_year:
        return True
    if year > today_year:
        return False
        
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "June", "July", "Sept"]
    for i, m in enumerate(months):
        if m in date_str:
            month = (i % 12) + 1
            today_month = int(today_iso[5:7])
            if month < today_month:
                return True
            return False
    return False

# Read existing README
with open("/Users/himishgoel/Desktop/dev events/awersome-developer-conferences/README.md", "r") as f:
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
                existing_events.append({
                    "name": parts[1],
                    "date": parts[2],
                    "location": parts[3],
                    "register": parts[4],
                    "continent": current_continent,
                    "line": line
                })
        continue
        
    if not in_events_section:
        if current_continent is None:
            pre_events_lines.append(line)
        else:
            post_events_lines.append(line)

# Filter out past events from existing
filtered_existing = [ev for ev in existing_events if not is_past(ev['date'], today_str)]

all_events = filtered_existing.copy()

def normalize_name(name):
    return name.lower().replace(' ', '').replace('-', '').replace('+', '')

existing_normalized = [normalize_name(e['name']) for e in filtered_existing]

for fe in fetched_events:
    cont = get_continent(fe['location'])
    norm_name = normalize_name(fe['name'])
    
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

# Distribute by continent
for ev in all_events:
    if ev['continent'] in continents_events:
        continents_events[ev['continent']].append(ev)
    else:
        continents_events['Online'].append(ev)

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
with open("/Users/himishgoel/Desktop/dev events/awersome-developer-conferences/README.md", "w") as f:
    f.write("\n".join(new_readme_lines) + "\n")

print("README.md updated with confs.tech and past events filtered!")
