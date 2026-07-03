import os
import re
import json
from datetime import datetime, timezone
import config
try:
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install required packages: pip install playwright beautifulsoup4")
    exit(1)

def fetch_bigevent():
    url = "https://bigevent.io/events/topic/developer/"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
            page.goto(url, wait_until='networkidle')
            import time
            time.sleep(3) # Give extra time for JS to load the JSON-LD
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            browser.close()
    except Exception as e:
        print(f"Failed to fetch data from 10times (bigevent.io) using Playwright: {e}")
        return []
    

    fetched_events = []
    current_time = datetime.now(timezone.utc)
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
                if not isinstance(item, dict):
                    continue
                event = item.get("item")
                if not isinstance(event, dict) or event.get("@type") != "Event":
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
                    if isinstance(addr, dict):
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
                if not config.is_event_relevant(event_text):
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
        iso_dates = re.findall(r'\d{4}-\d{2}-\d{2}', date_str)
        if iso_dates:
            max_date = max(iso_dates)
            today_iso = now.strftime("%Y-%m-%d")
            return max_date < today_iso
            
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        found_months = []
        lower_date = date_str.lower()
        for i, m in enumerate(months):
            if m in lower_date:
                found_months.append(i + 1)
        
        if found_months:
            max_month = max(found_months)
            if max_month < current_month:
                return True
                
    return False

def main():
    fetched_events = fetch_bigevent()


    # Map country/keyword to continent
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
    out_file = "events_bigevent.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")

if __name__ == "__main__":
    main()
