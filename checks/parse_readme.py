import os
import re
import sys
from datetime import datetime, date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
import events_store  # noqa: E402


def event_files():
    """Region files that hold the event tables."""
    return events_store.event_files(ROOT)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Support common human-readable formats like "MMM DD, YYYY" or "MMM DD-DD, YYYY"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "June", "July", "Sept"]
    clean_str = date_str.strip()
    if any(m in clean_str for m in months):
        year_match = re.search(r'\d{4}', clean_str)
        year = int(year_match.group(0)) if year_match else date.today().year
        for i, m in enumerate(months):
            if m in clean_str:
                month = (i % 12) + 1
                return date(year, month, 1)
    return None

def parse_readme(filepath):
    """
    Parses one event file (events/<region>.md) into structured event objects.
    """
    events = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_region = None
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check if it's a region header
        region_match = re.match(r"^###\s+(.+)$", line.strip())
        if region_match:
            current_region = region_match.group(1).strip()
            continue
            
        # Check if it's a table row
        if line.startswith("|") and not line.startswith("|---") and not line.startswith("| Event Name"):
            safe_line = line.replace('\\|', '{{PIPE}}')
            parts = [p.strip().replace('{{PIPE}}', '|') for p in safe_line.split('|')]
            if len(parts) >= 5: # ['', 'Name', 'Date', 'Location', 'Register', '']
                name_col = parts[1]
                date_col = parts[2]
                location_col = parts[3]
                register_col = parts[4]
                
                # Extract URL
                url_match = re.search(r'\[.*?\]\((.*?)\)', register_col)
                url = url_match.group(1) if url_match else register_col
                
                # Extract clean name
                name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', name_col).strip()
                
                # Extract dates
                date_start = None
                date_end = None
                
                if ' to ' in date_col:
                    dparts = date_col.split(' to ')
                    date_start = parse_date(dparts[0])
                    date_end = parse_date(dparts[1]) if len(dparts) > 1 else None
                else:
                    date_start = parse_date(date_col)
                    date_end = date_start
                
                events.append({
                    "line_number": line_num,
                    "region": current_region or "Unknown",
                    "name": name_clean,
                    "date_raw": date_col,
                    "date_start": date_start,
                    "date_end": date_end,
                    "location": location_col,
                    "url": url
                })
                
    return events

if __name__ == "__main__":
    events = [e for path in event_files() for e in parse_readme(path)]
    print(f"Parsed {len(events)} events.")
    if events:
        print(events[0])
