import os
import sys

# Add fetchers to path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "fetchers"))
import config

def main():
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_lines = f.read().splitlines()

    pre_events_lines = []
    post_events_lines = []
    all_events = []
    
    in_events_section = False
    
    for line in readme_lines:
        if line.startswith('## 📍 Event Schedule'):
            in_events_section = True
            pre_events_lines.append(line)
            continue
            
        if in_events_section:
            if line.startswith('---'):
                in_events_section = False
                post_events_lines.append(line)
                continue
                
            if line.startswith('|') and not line.startswith('| Event Name') and not line.startswith('|---') and not line.startswith('|------------'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    name = parts[1]
                    date_str = parts[2]
                    location = parts[3]
                    register = parts[4]
                    all_events.append({
                        "name": name,
                        "date": date_str,
                        "location": location,
                        "register": register,
                        "line": line
                    })
            continue
            
        if not in_events_section:
            pre_events_lines.append(line) if not post_events_lines else post_events_lines.append(line)

    # 2. Deduplicate
    deduped_events = config.deduplicate_events(all_events)
    
    # 3. Sort into continents
    # 1. Re-evaluate regions for all events using the newly robust config.determine_region
    for ev in deduped_events:
        cont = config.determine_region(ev['location'], ev.get('name', ''), ev.get('register', ''))
        ev['continent'] = cont

    continents_events = {
        'Africa': [],
        'Asia': [],
        'Australia': [],
        'Europe': [],
        'North America': [],
        'South America': [],
        'Virtual/Online': []
    }
    
    for ev in deduped_events:
        cont = ev['continent']
        if cont in continents_events:
            continents_events[cont].append(ev)
        else:
            continents_events['Virtual/Online'].append(ev)
            
    # 4. Sort by date
    for cont in continents_events:
        continents_events[cont].sort(key=lambda x: config.parse_date(x['date']))
        
    # 5. Reconstruct README
    new_readme_lines = pre_events_lines.copy()
    
    # Add tables
    for cont in sorted(continents_events.keys()):
        if not continents_events[cont]:
            continue
        new_readme_lines.append(f"### {cont}")
        new_readme_lines.append("| Event Name | Date | Location | Register |")
        new_readme_lines.append("|------------|------|----------|----------|")
        for ev in continents_events[cont]:
            new_readme_lines.append(ev['line'])

    new_readme_lines.extend(post_events_lines)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_readme_lines) + "\n")
        
    print(f"Cleaned up README.md! Total events went from {len(all_events)} to {len(deduped_events)}")

if __name__ == "__main__":
    main()
