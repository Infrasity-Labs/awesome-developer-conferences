import urllib.request
import ssl
import re
from datetime import datetime
import config
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install beautifulsoup4")
    exit(1)

def fetch_events_from_api():
    base_url = "https://www.papercall.io/events?open-cfps=false&page={}"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    


    fetched_events = []
    
    # PaperCall has pages. We'll scrape up to 10 pages for upcoming events
    for page in range(1, 11):
        url = base_url.format(page)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                html = response.read().decode('utf-8')
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            break
            
        soup = BeautifulSoup(html, 'html.parser')
        event_blocks = soup.find_all('div', class_='event-list-detail')
        
        if not event_blocks:
            break
            
        for item in event_blocks:
            title_node = item.find('var', class_='atc_title')
            start_node = item.find('var', class_='atc_date_start')
            end_node = item.find('var', class_='atc_date_end')
            loc_node = item.find('var', class_='atc_location')
            desc_node = item.find('var', class_='atc_description')
            
            if not title_node or not start_node:
                continue
                
            name = title_node.text.strip().replace('|', '\\|')
            start_date_str = start_node.text.strip()
            end_date_str = end_node.text.strip() if end_node else start_date_str
            location = loc_node.text.strip().replace('|', '\\|') if loc_node else 'N/A'
            desc = desc_node.text.strip().lower() if desc_node else ''
            
            # Find the actual link to the event
            link_node = item.find('h4', class_='hidden-xs')
            if link_node and link_node.find('a'):
                link = link_node.find('a')['href']
            else:
                # Fallback to papercall internal link
                title_h3 = item.find('h3', class_='event__title')
                if title_h3:
                    a_tags = title_h3.find_all('a')
                    for a in a_tags:
                        if 'pricing' not in a['href']:
                            link = 'https://www.papercall.io' + a['href'] if a['href'].startswith('/') else a['href']
                            break
                else:
                    link = ''
            
            try:
                # Format: "January 14, 2025"
                start_dt = datetime.strptime(start_date_str, "%B %d, %Y")
                end_dt = datetime.strptime(end_date_str, "%B %d, %Y")
            except Exception as e:
                # Fallback parse logic if format is weird
                continue
                
            # Filter past events
            if end_dt.timestamp() < datetime.now().timestamp():
                continue
                
            # Keywords matching
            event_text = name.lower() + ' ' + desc
            tag_nodes = item.find_all('a', href=re.compile("keywords=tags"))
            for t in tag_nodes:
                event_text += ' ' + t.text.strip().lower()
                
            if not config.is_event_relevant(event_text):
                continue
                
            if link:
                register = f"[↗]({link})"
            else:
                register = "N/A"
                
            if 'online' in location.lower() or 'virtual' in location.lower():
                location = 'Online'
                
            if start_dt.date() != end_dt.date():
                date_str = f"{start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"
            else:
                date_str = start_dt.strftime('%Y-%m-%d')
                
            fetched_events.append({
                "name": name,
                "date": date_str,
                "location": location,
                "register": register,
                "line": f"| {name} | {date_str} | {location} | {register} |"
            })
            
        # Check if next page exists
        next_btn = soup.find('li', class_='next')
        if not next_btn or 'disabled' in next_btn.get('class', []):
            break
            
    return fetched_events

def determine_region(location):
    loc_lower = location.lower()
    if 'online' in loc_lower or 'virtual' in loc_lower:
        return 'Virtual/Online'
    if any(x in loc_lower for x in ['usa', 'canada', 'united states', 'us', 'california', 'texas', 'new york', 'florida', 'illinois']):
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
    
    # Fallbacks based on city
    if any(city in loc_lower for city in ['london', 'munich', 'berlin', 'paris', 'amsterdam', 'barcelona', 'madrid', 'dublin']):
        return 'Europe'
    if any(city in loc_lower for city in ['san francisco', 'new york', 'orlando', 'los angeles', 'salt lake city', 'indianapolis', 'seattle', 'boston', 'austin', 'chicago']):
        return 'North America'
    if 'são paulo' in loc_lower:
        return 'South America'
    if any(city in loc_lower for city in ['hanoi', 'tokyo', 'seoul', 'mumbai', 'bengaluru', 'singapore']):
        return 'Asia'
    if 'melbourne' in loc_lower or 'sydney' in loc_lower:
        return 'Australia'
        
    return 'Virtual/Online'

if __name__ == "__main__":
    print("Fetching events from papercall.io...")
    events = fetch_events_from_api()
    print(f"Found {len(events)} events matching criteria.")
    
    # Read existing README
    with open('README.md', 'r', encoding='utf-8') as f:
        readme_content = f.read()
        
    # Standard replacement logic matching the other fetchers...
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
            
        # Sort events by date
        region_events.sort(key=lambda x: x['date'])
        
        # Regex to find the section and its table
        pattern = re.compile(rf"(## {region}\n.*?\| Event Name.*?\|\n\|---.*?\|\n)(.*?)(?=\n## |\Z)", re.DOTALL)
        match = pattern.search(readme_content)
        
        if match:
            header_and_table_header = match.group(1)
            existing_table_content = match.group(2)
            
            existing_rows = existing_table_content.strip().split('\n')
            if existing_rows == ['']:
                existing_rows = []
                
            # Parse existing rows to avoid duplicates
            existing_names = []
            for row in existing_rows:
                parts = row.split('|')
                if len(parts) >= 3:
                    name_part = parts[1].strip()
                    # Remove markdown link if present
                    name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', name_part)
                    existing_names.append(name_clean.lower())
                    
            # Add new events
            new_rows_added = 0
            for event in region_events:
                name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', event['name']).lower()
                
                # Check for duplicates
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
                # We need to sort the combined rows
                def extract_date(row):
                    parts = row.split('|')
                    if len(parts) >= 4:
                        date_str = parts[2].strip()
                        # Extract first date if it's a range
                        date_str = date_str.split(' to ')[0].strip()
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
    
    print("Done integrating papercall events into README.md")
