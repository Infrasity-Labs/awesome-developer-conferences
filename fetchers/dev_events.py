import os
import re
import urllib.request
import json
import ssl
from datetime import datetime
import config
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  

BROWSERLESS_TOKEN = os.environ.get("BROWSERLESS_TOKEN")  
BROWSERLESS_WS = f"wss://production-sfo.browserless.io/chromium/playwright?token={BROWSERLESS_TOKEN}"

def fetch_events_from_api():
    url = "https://dev.events/"

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            html = None
            if BROWSERLESS_TOKEN:
                try:
                    browser = p.chromium.connect(BROWSERLESS_WS)
                    page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
                    page.goto(url, wait_until='domcontentloaded')
                    html = page.content()
                    browser.close()
                except Exception as e:
                    print(f"Browserless run failed ({e}). Falling back to local Playwright...")
            
            if not html:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                html = page.content()
                browser.close()
    except Exception as e:
        print(f"Failed to fetch data using Playwright: {e}")
        return []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
    except ImportError:
        print("Please install beautifulsoup4")
        return []

    scripts = soup.find_all('script', type='application/ld+json')

    


    fetched_events = []
    raw_count = 0
    filtered_count = 0
    for script in scripts:
        raw_count += 1
        try:
            event = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            filtered_count += 1
            continue
            
        if event.get('@type') not in ['EducationEvent', 'Event']:
            filtered_count += 1
            continue
            
        start_date_str = event.get('startDate')
        end_date_str = event.get('endDate')
        
        if not start_date_str:
            filtered_count += 1
            continue
            
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_date = start_date
        except Exception as e:
            filtered_count += 1
            continue
            
        # Filter past events
        from datetime import timezone
        if end_date < datetime.now(timezone.utc):
            filtered_count += 1
            continue
            
        name = (event.get('name') or 'N/A').replace('|', '\\|')
        desc = (event.get('description') or '').lower()
        
        event_text = name.lower() + ' ' + desc

        link = event.get('url', '')
        if link:
            register = f"[↗]({link})"
        else:
            register = "N/A"
            
        # Determine location
        attendance = event.get('eventAttendanceMode', '')
        if 'Online' in attendance:
            location = 'Online'
        else:
            loc_data = event.get('location', {})
            if isinstance(loc_data, dict):
                address = loc_data.get('address', {})
                if isinstance(address, dict):
                    city = address.get('addressLocality', '')
                    country = address.get('addressCountry', '')
                    location = f"{city}, {country}".strip(', ')
                else:
                    location = str(address)
            else:
                location = str(loc_data)
                
            if not location or location == '{}':
                location = 'Unknown'
                
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
    
    print(f"[DevEvents] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(fetched_events)}")
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
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    today_str = now.strftime('%Y-%m-%d')
    
    # Try to find ISO dates (YYYY-MM-DD)
    iso_dates = re.findall(r'\d{4}-\d{2}-\d{2}', date_str)
    if iso_dates:
        return max(iso_dates) < today_str
        
    # Fallback for non-ISO dates (approximate check by year and month)
    years = re.findall(r'\d{4}', date_str)
    if not years:
        return False
        
    current_year = now.year
    current_month = now.month
    
    max_year = max(int(y) for y in years)
    if max_year < current_year:
        return True
        
    if max_year == current_year:
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
    out_file = "events_dev_events.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_events, f, indent=2)
    print(f"Saved {len(fetched_events)} events to {out_file}")

if __name__ == "__main__":
    main()