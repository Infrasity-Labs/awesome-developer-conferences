import os
import glob
import json
import re
from datetime import datetime
from fetchers import config

def main():
    print("Starting aggregation...")
    with open('README.md', 'r', encoding='utf-8') as f:
        readme_content = f.read()

    # Load all json files
    all_new_events = []
    source_counts = {}
    for json_file in glob.glob('events_*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                events = json.load(f)
                all_new_events.extend(events)
                source_counts[json_file] = len(events)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

    print(f"Loaded {len(all_new_events)} total events from {len(source_counts)} fetchers.")
    
    regions = {
        'Africa': [],
        'Asia': [],
        'Australia': [],
        'Europe': [],
        'North America': [],
        'South America': [],
        'Virtual/Online': []
    }
    
    # Categorize events by region
    for event in all_new_events:
        loc = event.get('location') or 'Unknown'
        region = config.determine_region(loc)
        if region in regions:
            regions[region].append(event)
            
    total_added = 0
    # Now integrate into README.md
    for region, region_events in regions.items():
        if not region_events:
            continue
            
        pattern = re.compile(rf"(### {region}\n.*?\| Event Name.*?\|\n\|---.*?\|\n)(.*?)(?=\n</details>|\n### |\n## |\n---|\Z)", re.DOTALL)
        match = pattern.search(readme_content)
        
        if match:
            header_and_table_header = match.group(1)
            existing_table_content = match.group(2)
            
            existing_rows = existing_table_content.strip().split('\n')
            if existing_rows == ['']:
                existing_rows = []
                
            existing_names = []
            for row in existing_rows:
                # Use regex to split by unescaped pipes
                parts = re.split(r'(?<!\\)\|', row)
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
                    line = event.get('line')
                    if not line:
                        line = f"| {event['name']} | {event['date']} | {event['location']} | {event['register']} |"
                        
                    # Skip if event is already in the past
                    date_str = event.get('date', '').split(' to ')[-1].strip()
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        if dt.timestamp() < datetime.now().timestamp():
                            continue
                    except:
                        pass
                        
                    existing_rows.append(line)
                    existing_names.append(name_clean)
                    new_rows_added += 1
                    total_added += 1
            def extract_date(row):
                parts = re.split(r'(?<!\\)\|', row)
                if len(parts) >= 4:
                    date_str = parts[2].strip().split(' to ')[0].strip()
                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d")
                    except:
                        pass
                return datetime.max
            
            upcoming = []
            past = []
            invalid = []
            today_dt = datetime.now()
            for r in existing_rows:
                if not r.strip(): continue
                dt = extract_date(r)
                if dt == datetime.max:
                    invalid.append(r)
                elif dt >= today_dt:
                    upcoming.append((dt, r))
                else:
                    past.append((dt, r))
                    
            upcoming.sort(key=lambda x: x[0])
            past.sort(key=lambda x: x[0], reverse=True)
            sorted_rows = [x[1] for x in upcoming] + [x[1] for x in past] + invalid
            
            new_table_content = '\n'.join(sorted_rows) + '\n'
            readme_content = readme_content[:match.start()] + header_and_table_header + new_table_content + readme_content[match.end():]
                
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
        
    print(f"Aggregate step finished! {total_added} new unique events added.")

    # Write summary for GitHub Actions
    summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_path:
        with open(summary_path, 'a') as f:
            f.write("### Event Update Summary\n")
            f.write(f"- Processed {len(all_new_events)} events across all sources.\n")
            f.write(f"- Added {total_added} new unique events to README.\n\n")
            f.write("#### Source Breakdown:\n")
            for source, count in source_counts.items():
                f.write(f"- **{source.replace('events_', '').replace('.json', '')}**: {count} events fetched\n")
                
    # Also save the total added for dynamic commit messages
    with open('events_added_count.txt', 'w') as f:
        f.write(str(total_added))

if __name__ == "__main__":
    main()
