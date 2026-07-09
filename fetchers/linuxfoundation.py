import urllib.request
import ssl
import json
from datetime import datetime
import config

def get_countries():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    countries = {}
    try:
        url = "https://events.linuxfoundation.org/wp-json/wp/v2/lfevent-country?per_page=100"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            for item in data:
                countries[item['id']] = item['name']
    except Exception as e:
        print(f"Failed to fetch LF countries: {e}")
    return countries

def fetch_lf_events():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    countries_map = get_countries()
    
    events = []
    raw_count = 0
    filtered_count = 0
    now_ts = datetime.now().timestamp()
    
    current_year = datetime.now().year
    years_to_check = [current_year, current_year + 1]
    
    for year in years_to_check:
        url = f"https://events.linuxfoundation.org/wp-json/wp/v2/lfevent{year}?parent=0&per_page=100"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue
            
        if not isinstance(data, list):
            continue
        for item in data:
            raw_count += 1
            name = item.get('title', {}).get('rendered', '')
            name = name.replace('&#038;', '&').replace('&#8211;', '-').replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
            
            meta = item.get('meta', {})
            start_date_str = meta.get('lfes_date_start', '')
            if not start_date_str:
                filtered_count += 1
                continue
                
            try:
                # Format is often "YYYY/MM/DD"
                start_date_str = start_date_str.replace('/', '-')
                dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                if dt.date() < datetime.fromtimestamp(now_ts, dt.tzinfo).date():
                    filtered_count += 1
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            except Exception as e:
                filtered_count += 1
                continue
                
            city = meta.get('lfes_city', '')
            region = meta.get('lfes_region', '')
            
            country_ids = item.get('lfevent-country', [])
            country = ""
            if country_ids and len(country_ids) > 0:
                country = countries_map.get(country_ids[0], "")
                
            loc_parts = []
            if city: loc_parts.append(city)
            if region: loc_parts.append(region)
            if country: loc_parts.append(country)
            
            location = ", ".join(loc_parts)
            if not location:
                if meta.get('lfes_virtual'):
                    location = "Online"
                else:
                    location = "Unknown"
                    
            event_url = item.get('link', '')
            register = f"[↗]({event_url})" if event_url else "N/A"
            name_clean = name.replace('|', '\\|')
            
            events.append({
                "name": name_clean,
                "date": date_str,
                "location": location,
                "url": event_url,
                "register": register,
                "line": f"| {name_clean} | {date_str} | {location} | {register} |"
            })
            
    print(f"[LinuxFoundation] Total raw events: {raw_count} | Filtered out: {filtered_count} | Successfully fetched: {len(events)}")
    return events

if __name__ == "__main__":
    print("Fetching events from Linux Foundation...")
    events = fetch_lf_events()
    print(f"Found {len(events)} LF events.")
    
    if not events:
        exit(0)

    out_file = "events_linuxfoundation.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")
