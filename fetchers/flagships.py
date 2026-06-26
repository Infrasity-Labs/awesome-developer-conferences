import re
from datetime import datetime

# Hardcoded flagship events that do not appear on aggregator sites
flagship_events = [
    {
        "name": "WeAreDevelopers World Congress",
        "date": "2026-07-08 to 2026-07-10",
        "location": "Berlin, Germany",
        "register": "[↗](https://www.wearedevelopers.com/world-congress)"
    },
    {
        "name": "WeAreDevelopers North America",
        "date": "2026-09-01",
        "location": "San Jose, USA",
        "register": "[↗](https://www.wearedevelopers.com/world-congress-north-america)"
    },
    {
        "name": "WeAreDevelopers India",
        "date": "2026-10-01",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.wearedevelopers.com/conference-india)"
    },
    {
        "name": "DevRelCon NYC",
        "date": "2026-07-22 to 2026-07-23",
        "location": "New York, USA",
        "register": "[↗](https://nyc.devrelcon.dev)"
    },
    {
        "name": "SaaStr Annual",
        "date": "2026-09-09 to 2026-09-11",
        "location": "San Mateo, USA",
        "register": "[↗](https://saastr.com/events)"
    },
    {
        "name": "KubeCon + CloudNativeCon North America",
        "date": "2026-11-09 to 2026-11-12",
        "location": "Salt Lake City, USA",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america)"
    },
    {
        "name": "KubeCon + CloudNativeCon Europe",
        "date": "TBA",
        "location": "Barcelona, Spain",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-europe)"
    },
    {
        "name": "KubeCon + CloudNativeCon India",
        "date": "2026-06-18 to 2026-06-19",
        "location": "Mumbai, India",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-india)"
    },
    {
        "name": "KubeCon + CloudNativeCon Japan",
        "date": "2026-07-28 to 2026-07-30",
        "location": "Yokohama, Japan",
        "register": "[↗](https://events.linuxfoundation.org/kubecon-cloudnativecon-japan)"
    },
    {
        "name": "Open Source Summit North America",
        "date": "TBA",
        "location": "Minneapolis, USA",
        "register": "[↗](https://events.linuxfoundation.org/open-source-summit-north-america)"
    },
    {
        "name": "Open Source Summit Japan",
        "date": "2026-12-01",
        "location": "Tokyo, Japan",
        "register": "[↗](https://events.linuxfoundation.org/open-source-summit-japan)"
    },
    {
        "name": "All Things Open",
        "date": "2026-10-25",
        "location": "Raleigh, USA",
        "register": "[↗](https://allthingsopen.org)"
    },
    {
        "name": "PlatformCon",
        "date": "2026-06-08 to 2026-06-12",
        "location": "Online",
        "register": "[↗](https://platformcon.com)"
    },
    {
        "name": "AWS re:Invent",
        "date": "2026-11-30 to 2026-12-04",
        "location": "Las Vegas, USA",
        "register": "[↗](https://aws.amazon.com/events/reinvent)"
    },
    {
        "name": "Devoxx Belgium",
        "date": "2026-10-05 to 2026-10-09",
        "location": "Antwerp, Belgium",
        "register": "[↗](https://devoxx.be)"
    },
    {
        "name": "Web Summit",
        "date": "2026-11-10",
        "location": "Lisbon, Portugal",
        "register": "[↗](https://websummit.com)"
    },
    {
        "name": "GITEX Global",
        "date": "2026-12-01",
        "location": "Dubai, UAE",
        "register": "[↗](https://www.gitex.com)"
    },
    {
        "name": "GITEX AI Europe",
        "date": "2026-06-30 to 2026-07-01",
        "location": "Berlin, Germany",
        "register": "[↗](https://www.gitex.com/gitex-ai-europe)"
    },
    {
        "name": "AIBoomi Events",
        "date": "TBA",
        "location": "Bengaluru, India",
        "register": "[↗](https://saasboomi.org/events)"
    },
    {
        "name": "AIBoomi Annual",
        "date": "TBA",
        "location": "Chennai, India",
        "register": "[↗](https://annual.aiboomi.org)"
    },
    {
        "name": "Cypher AI Conference",
        "date": "2026-10-01 to 2026-10-03",
        "location": "Bengaluru, India",
        "register": "[↗](https://cypher.analyticsindiamag.com)"
    },
    {
        "name": "NASSCOM Tech Events",
        "date": "TBA",
        "location": "India",
        "register": "[↗](https://nasscom.in/events)"
    },
    {
        "name": "DevConf.IN",
        "date": "2026-08-01 to 2026-08-02",
        "location": "Bengaluru, India",
        "register": "[↗](https://www.devconf.info/in)"
    },
    {
        "name": "India SaaS & Marketing Tech Summit",
        "date": "2026-07-15",
        "location": "Bengaluru, India",
        "register": "[↗](https://whysummits.com/india-saas-marketing-tech-summit-2026)"
    },
    {
        "name": "Tech in Asia Events",
        "date": "TBA",
        "location": "Singapore",
        "register": "[↗](https://www.techinasia.com/events)"
    },
    {
        "name": "IDC Asia Pacific Summits",
        "date": "TBA",
        "location": "Singapore",
        "register": "[↗](https://www.idc.com/ap/events)"
    }
]

def determine_region(location):
    loc_lower = location.lower()
    if 'online' in loc_lower or 'virtual' in loc_lower:
        return 'Virtual/Online'
    if any(x in loc_lower for x in ['usa', 'canada', 'united states', 'us']):
        return 'North America'
    if any(x in loc_lower for x in ['uk', 'germany', 'austria', 'france', 'portugal', 'czechia', 'czech republic', 'spain', 'belgium', 'netherlands']):
        return 'Europe'
    if any(x in loc_lower for x in ['india', 'japan', 'china', 'uae', 'singapore']):
        return 'Asia'
    return 'Virtual/Online'

if __name__ == "__main__":
    print(f"Injecting {len(flagship_events)} flagship events into README.md...")
    
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
    
    # Filter past events
    valid_events = []
    now_ts = datetime.now().timestamp()
    for e in flagship_events:
        if e["date"] == "TBA":
            e["line"] = f"| {e['name']} | {e['date']} | {e['location']} | {e['register']} |"
            valid_events.append(e)
            continue
            
        date_str = e["date"].split(" to ")[-1]
        try:
            end_dt = datetime.strptime(date_str, "%Y-%m-%d")
            if end_dt.timestamp() >= now_ts:
                e["line"] = f"| {e['name']} | {e['date']} | {e['location']} | {e['register']} |"
                valid_events.append(e)
        except Exception as err:
            pass
            
    for event in valid_events:
        region = determine_region(event['location'])
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
                name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', event['name']).lower()
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
                def extract_date(row):
                    parts = row.split('|')
                    if len(parts) >= 4:
                        date_str = parts[2].strip().split(' to ')[0].strip()
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
    
    print("Done integrating flagship events.")
