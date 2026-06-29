import os
import re
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import config

def fetch_events():
    url = "https://adatosystems.com/cfp"
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        html = response.text

    except Exception as e:
        print(f"Failed to fetch data from adatosystems: {e}")
        raise
        
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        return []
        
    table = tables[0]
    fetched_events = []
    
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if len(tds) < 8:
            continue
            
        name = tds[0].text.strip().replace('|', '\\|')
        city = tds[1].text.strip()
        state = tds[2].text.strip()
        start_date_str = tds[3].text.strip()
        end_date_str = tds[4].text.strip()
        
        event_link_elem = tds[6].find('a')
        cfp_link_elem = tds[7].find('a')
        
        url = ''
        if event_link_elem and event_link_elem.has_attr('href'):
            url = event_link_elem['href']
        elif cfp_link_elem and cfp_link_elem.has_attr('href'):
            url = cfp_link_elem['href']
            
        if not start_date_str:
            continue
            
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            else:
                end_date = start_date
        except Exception:
            continue
            
        if end_date < datetime.now():
            continue
            
        event_text = name.lower()
        if not config.is_event_relevant(event_text):
            continue
            
        register = f"[↗]({url})" if url else "N/A"
        
        location_parts = [p for p in [city, state] if p]
        location = ", ".join(location_parts) if location_parts else 'Unknown'
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
    print("Fetching events from adatosystems...")
    fetched_events = fetch_events()
    print(f"Found {len(fetched_events)} upcoming relevant events on adatosystems.")
    
    if not fetched_events:
        print("No new events to add from adatosystems.")
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
        
    print("Done integrating adatosystems events.")

if __name__ == "__main__":
    main()
