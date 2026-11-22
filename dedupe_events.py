import re

import events_store


def clean_file(path):
    """Drop duplicate rows (same URL or same name) inside one region file."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    
    seen_urls = set()
    seen_names = []
    
    new_lines = []
    removed_count = 0
    
    for line in lines:
        if line.strip().startswith('| Event Name'):
            seen_urls.clear()
            seen_names.clear()
            new_lines.append(line)
            continue
        elif line.strip().startswith('|-'):
            new_lines.append(line)
            continue
        elif line.strip().startswith('|'):
            parts = re.split(r'(?<!\\)\|', line)
            if len(parts) >= 5:
                name_raw = parts[1].strip()
                name_clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', name_raw).lower()
                
                url_match = re.search(r'\[.*?\]\((.*?)\)', parts[4])
                url = url_match.group(1).strip() if url_match else None
                
                # Ignore generic N/A or empty urls for deduplication
                if url == 'N/A' or not url:
                    url = None
                
                is_dup = False
                
                # 1. Dedupe by Exact URL
                if url and url in seen_urls:
                    is_dup = True
                
                # 2. Dedupe by Substring Name
                if not is_dup:
                    if name_clean in seen_names:
                        is_dup = True
                            
                if not is_dup:
                    if url:
                        seen_urls.add(url)
                    seen_names.append(name_clean)
                    new_lines.append(line)
                else:
                    removed_count += 1
                    print(f"Removed duplicate: {name_raw} -> {url}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    return removed_count


def clean_events():
    removed = sum(clean_file(path) for path in events_store.event_files())
    print(f"\nTotal duplicates removed: {removed}")


if __name__ == '__main__':
    clean_events()
