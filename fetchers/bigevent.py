import os
import re
import json
from datetime import datetime
try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install required packages: pip install cloudscraper beautifulsoup4")
    exit(1)

def fetch_10times_events():
    url = "https://bigevent.io/events/topic/developer/"
    
    try:
        scraper = cloudscraper.create_scraper()
        with scraper.get(url, timeout=15) as response:
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Failed to fetch data from 10times: {e}")
        return []
    
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

    fetched_events = []
    current_time = datetime.utcnow()
    current_year = current_time.year
    
    # Parse JSON-LD script from BigEvent
    schema_script = soup.find('script', class_='rank-math-schema')
    if schema_script:
        try:
            schema_data = json.loads(schema_script.text)
            event_items = []
            
            if "@graph" in schema_data:
                for graph_item in schema_data["@graph"]:
                    if graph_item.get("@type") == "ItemList" and "itemListElement" in graph_item:
                        event_items = graph_item["itemListElement"]
                        break
            
            for item in event_items:
                event = item.get("item", {})
                if event.get("@type") != "Event":
                    continue
                    
                name = event.get("name") or 'N/A'
                link = event.get("url") or ''
                if link and not link.startswith('http'):
                    link = "https://bigevent.io" + link
                    
                date_str = event.get("startDate") or "TBA"
                
                # Check year to skip past events
                year_match = re.search(r'\d{4}', date_str)
                event_year = int(year_match.group()) if year_match else current_year
                if event_year < current_year:
                    continue
                    
                location = "Unknown"
                loc_data = event.get("location", {})
                if isinstance(loc_data, dict) and "address" in loc_data:
                    addr = loc_data["address"]
                    locality = addr.get("addressLocality", "")
                    country = addr.get("addressCountry", "")
                    if country.lower() == "czech republic":
                        country = "Czechia"
                    if locality and country:
                        location = f"{locality}, {country}"
                    elif locality:
                        location = locality
                    elif country:
                        location = country
                elif event.get("eventAttendanceMode") == "https://schema.org/OnlineEventAttendanceMode":
                    location = "Online"
                    
                location = location or 'N/A'
                
                # Keyword matching against name and description (if available)
                event_text = (name + " " + event.get("description", "")).lower()
                if not any(kw.lower() in event_text for kw in keywords):
                    continue

                register = f"[↗]({link})" if link else "N/A"
                
                fetched_events.append({
                    "name": name.replace('|', '\\|'),
                    "date": date_str,
                    "location": location.replace('|', '\\|'),
                    "register": register,
                    "line": f"| {name.replace('|', '\\|')} | {date_str} | {location.replace('|', '\\|')} | {register} |"
                })
        except json.JSONDecodeError:
            print("Failed to parse JSON-LD from BigEvent.")

    return fetched_events

fetched_events = fetch_10times_events()

# Map country/keyword to continent
def get_continent(location):
    loc_lower = location.lower()
    if 'online' in loc_lower:
        if ' & online' not in loc_lower:
            return 'Online'
    if any(x in loc_lower for x in ['usa', 'canada', 'united states']):
        return 'North America'
    if any(x in loc_lower for x in ['uk', 'germany', 'austria', 'france', 'portugal', 'czechia', 'czech republic', 'luxembourg', 'netherlands', 'poland', 'denmark', 'switzerland', 'belgium', 'ireland', 'italy', 'spain', 'sweden', 'norway', 'finland', 'united kingdom']):
        return 'Europe'
    if any(x in loc_lower for x in ['brazil', 'peru', 'argentina', 'colombia', 'chile']):
        return 'South America'
    if any(x in loc_lower for x in ['vietnam', 'korea', 'china', 'japan', 'indonesia', 'india', 'qatar', 'singapore', 'taiwan', 'thailand', 'malaysia', 'philippines']):
        return 'Asia'
    if any(x in loc_lower for x in ['nigeria', 'south africa', 'kenya', 'egypt']):
        return 'Africa'
    if any(x in loc_lower for x in ['australia', 'new zealand']):
        return 'Australia'
    # Fallbacks based on city if no country is present
    if 'london' in loc_lower or 'munich' in loc_lower or 'berlin' in loc_lower or 'paris' in loc_lower or 'amsterdam' in loc_lower:
        return 'Europe'
    if 'san francisco' in loc_lower or 'new york' in loc_lower or 'orlando' in loc_lower or 'los angeles' in loc_lower or 'salt lake city' in loc_lower or 'indianapolis' in loc_lower or 'california' in loc_lower:
        return 'North America'
    if 'são paulo' in loc_lower:
        return 'South America'
    if 'hanoi' in loc_lower or 'tokyo' in loc_lower or 'seoul' in loc_lower or 'mumbai' in loc_lower or 'bengaluru' in loc_lower:
        return 'Asia'
    if 'lagos' in loc_lower:
        return 'Africa'
    if 'melbourne' in loc_lower or 'sydney' in loc_lower:
        return 'Australia'
    
    # default to online if we can't figure it out
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

# Read existing README to extract current events
readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
with open(readme_path, "r") as f:
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
all_events = existing_events.copy()

def normalize_name(name):
    return name.lower().replace(' ', '').replace('-', '').replace('+', '')

existing_normalized = [normalize_name(e['name']) for e in existing_events]

for fe in fetched_events:
    cont = get_continent(fe['location'])
    norm_name = normalize_name(fe['name'])
    
    if norm_name in existing_normalized:
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

# Helper to parse date for sorting
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
with open(readme_path, "w") as f:
    f.write("\n".join(new_readme_lines) + "\n")

print("bigevent.io events fetched and README.md updated successfully!")
