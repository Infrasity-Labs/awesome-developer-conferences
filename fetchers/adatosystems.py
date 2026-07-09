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
    raw_count = 0
    filtered_count = 0
    
    for tr in table.find_all('tr')[1:]:
        raw_count += 1
        tds = tr.find_all('td')
        if len(tds) < 8:
            filtered_count += 1
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
            filtered_count += 1
            continue
            
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            else:
                end_date = start_date
        except Exception:
            filtered_count += 1
            continue
            
        if end_date.date() < datetime.now().date():
            filtered_count += 1
            continue
            
        event_text = name.lower()
        if not config.is_event_relevant(event_text):
            filtered_count += 1
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
        
    print(f"[AdatoSystems] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
    return fetched_events

def main():
    print("Fetching events from adatosystems...")
    fetched_events = fetch_events()
    print(f"Found {len(fetched_events)} upcoming relevant events on adatosystems.")
    
    if not fetched_events:
        print("No new events to add from adatosystems.")
        return

    import json
    out_file = "events_adatosystems.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")

if __name__ == "__main__":
    main()
