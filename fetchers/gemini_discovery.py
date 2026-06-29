import os
import json
import urllib.request
import ssl
from datetime import datetime
import config

def query_gemini(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "tools": [{
            "googleSearch": {}
        }],
        "systemInstruction": {
            "parts": [{"text": "You are a web scraper. You must ONLY output a valid JSON array of event objects. No markdown blocks like ```json. Just raw JSON."}]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text']
            return text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "[]"

def fetch_events_from_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found in environment. Skipping Gemini discovery.")
        return []
        
    queries = [
        ("Search for upcoming software developer conferences and meetups in Africa happening in 2026. Give me exactly 15 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", False),
        ("Search for upcoming software engineering conferences in South America in 2026. Give me exactly 15 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", False),
        ("Search Google for 'call for speakers developer site:sessionize.com' for upcoming 2026 events. Give me exactly 15 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", False),
        ("Search for upcoming 'Apache Software Foundation' or 'Community Over Code' conferences in 2026. Give me up to 10 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", True),
        ("Search for upcoming 'OWASP Global AppSec' or OWASP chapter events in 2026. Give me up to 10 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", True),
        ("Search for upcoming regional 'PyCon' conferences globally in 2026. Give me up to 10 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", True),
        ("Search for upcoming 'AWS Community Day' events in 2026 globally. Give me up to 10 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", True),
        ("Search for upcoming HashiCorp or Terraform community events in 2026 globally. Give me up to 10 events. Output a JSON array with keys: 'name', 'date' (YYYY-MM-DD), 'location', 'url'.", True)
    ]
    
    events = []
    now_ts = datetime.now().timestamp()
    
    for query, skip_relevance in queries:
        print(f"Running Gemini search: {query}")
        result_text = query_gemini(api_key, query)
        try:
            # Strip potential markdown formatting if model disobeys
            clean_text = result_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            ai_events = json.loads(clean_text.strip())
            
            if not isinstance(ai_events, list):
                continue
                
            for item in ai_events:
                if not isinstance(item, dict):
                    continue
                name = item.get('name', 'N/A').replace('|', '\\|')
                date_str = item.get('date', '9999-99-99')
                location = item.get('location', 'Unknown')
                url = item.get('url', '')
                
                # Filter out bad dates
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    if dt.timestamp() < now_ts:
                        continue
                except:
                    continue
                    
                # Relevance filter
                if not skip_relevance:
                    event_text = name + " " + location
                    if not config.is_event_relevant(event_text):
                        continue
                    
                register = f"[↗]({url})" if url else "N/A"
                
                events.append({
                    "name": name,
                    "date": date_str,
                    "location": location,
                    "url": url,
                    "register": register,
                    "line": f"| {name} | {date_str} | {location} | {register} |"
                })
        except Exception as e:
            print(f"Failed to parse Gemini output: {e}")
            continue
            
    # Deduplicate by URL
    unique_events = []
    seen_urls = set()
    for ev in events:
        if ev['url'] not in seen_urls:
            unique_events.append(ev)
            seen_urls.add(ev['url'])
            
    return unique_events

if __name__ == "__main__":
    print("Fetching events from Gemini AI Discovery...")
    # For local testing, ensure GEMINI_API_KEY is exported
    events = fetch_events_from_gemini()
    print(f"Found {len(events)} AI-discovered events.")
    
    if not events:
        exit(0)

    out_file = "events_gemini.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {out_file}")
