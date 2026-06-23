import urllib.request
import json
import ssl
from datetime import datetime

def fetch_events():
    url = "https://developers.events/all-events.json"

    # Bypass SSL verification if there are local cert issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req, context=ctx)
        data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return

    print("| Event Name | Date | Location | Register |")
    print("|---|---|---|---|")

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

    for event in data:
        dates = event.get('date', [])
        if not dates:
            continue
        
        # Dates are in milliseconds, convert to seconds
        start_timestamp = dates[0] / 1000.0
        start_date = datetime.fromtimestamp(start_timestamp)
        end_timestamp = dates[-1] / 1000.0 if len(dates) > 0 else start_timestamp
        
        # Filter past events
        now_timestamp = datetime.now().timestamp()
        if end_timestamp < now_timestamp:
            continue
            
        # Match keywords against name and tags
        event_text = event.get('name', '').lower()
        tags = [tag.get('value', '').lower() for tag in event.get('tags', [])]
        event_text += ' ' + ' '.join(tags)
        
        if not any(kw.lower() in event_text for kw in keywords):
            continue

        name = event.get('name', 'N/A').replace('|', '\\|')
        location = event.get('location', 'N/A').replace('|', '\\|')
        link = event.get('hyperlink', '')
        
        if link:
            register_md = f"[Link]({link})"
        else:
            register_md = "N/A"
        
        if len(dates) > 1:
            end_date = datetime.fromtimestamp(end_timestamp)
            date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            date_str = start_date.strftime('%Y-%m-%d')
            
        print(f"| {name} | {date_str} | {location} | {register_md} |")

if __name__ == '__main__':
    fetch_events()
