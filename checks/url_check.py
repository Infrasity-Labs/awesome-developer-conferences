import argparse
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from parse_readme import parse_readme
import re

def check_url(url):
    """
    Returns (status, code) where status is True if alive, False if dead.
    """
    cmd = [
        "curl", "-L", "--max-time", "10", "--retry", "2", "--silent",
        "--output", "/dev/null", "--write-out", "%{http_code}",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        url
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        code_str = result.stdout.strip()
        code = int(code_str) if code_str.isdigit() else 0
        
        # 200, 301, 302, 403 (WAF), 415 (CDN block), 429 (Rate Limit), 0 (Timeout/Drop) -> Alive
        # 5xx -> Warn but don't remove (Alive)
        if code in [0, 200, 301, 302, 403, 415, 429] or (500 <= code <= 599):
            return True, code
        return False, code
    except Exception as e:
        return True, 0

def get_newly_added_urls():
    """
    Parses git diff for added URLs. Checks unstaged changes first.
    If none, checks the last commit (useful for PRs).
    """
    try:
        # Check unstaged (daily pipeline)
        result = subprocess.run(["git", "diff", "HEAD", "--", "README.md"], stdout=subprocess.PIPE, text=True)
        diff_out = result.stdout
        
        # If empty, check against last commit (PR pipeline)
        if not diff_out.strip():
            result = subprocess.run(["git", "diff", "HEAD^1", "HEAD", "--", "README.md"], stdout=subprocess.PIPE, text=True)
            diff_out = result.stdout
            
        added_urls = set()
        
        for line in diff_out.split('\n'):
            if line.startswith('+') and not line.startswith('+++') and '|' in line:
                url_match = re.search(r'\[.*?\]\((.*?)\)', line)
                if url_match:
                    added_urls.add(url_match.group(1).strip())
        return added_urls
    except Exception as e:
        print(f"Warning: Failed to retrieve git diff ({e}). If running in CI, ensure fetch-depth is at least 2.", file=sys.stderr)
        return set()

def main():
    parser = argparse.ArgumentParser(description="Check URLs in README.md")
    parser.add_argument('--report', action='store_true', help="Print dead URLs and exit 1 if any")
    parser.add_argument('--fix', action='store_true', help="Remove dead URL rows from README.md")
    parser.add_argument('--diff-only', action='store_true', help="Only check URLs added in current git diff")
    parser.add_argument('--all', action='store_true', help="Check all URLs")
    args = parser.parse_args()
    
    if not args.report and not args.fix:
        parser.error("Must specify --report or --fix")
    if not args.diff_only and not args.all:
        parser.error("Must specify --diff-only or --all")
        
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.join(script_dir, "..", "README.md")
    events = parse_readme(readme_path)
    
    urls_to_check = []
    if args.diff_only:
        added_urls = get_newly_added_urls()
        for ev in events:
            if ev['url'] in added_urls:
                urls_to_check.append(ev)
    else:
        urls_to_check = events
        
    print(f"Checking {len(urls_to_check)} URLs...")
    
    dead_events = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_event = {executor.submit(check_url, ev['url']): ev for ev in urls_to_check}
        for future in as_completed(future_to_event):
            ev = future_to_event[future]
            alive, code = future.result()
            
            if not alive:
                dead_events.append((ev, code))
                
    if dead_events:
        print(f"Found {len(dead_events)} dead URLs:")
        lines_to_remove = set()
        for ev, code in dead_events:
            print(f"Line {ev['line_number']} | Code: {code} | {ev['name']} | {ev['url']}")
            lines_to_remove.add(ev['line_number'])
            
        if args.fix:
            print(f"Removing {len(lines_to_remove)} rows from README.md...")
            with open(readme_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            remove_indices = {num - 1 for num in lines_to_remove}
            
            with open(readme_path, "w", encoding="utf-8") as f:
                for i, line in enumerate(lines):
                    if i not in remove_indices:
                        f.write(line)
            print("Done fixing README.md.")
            
        if args.report:
            sys.exit(1)
    else:
        print("All tested URLs are alive!")
        sys.exit(0)

if __name__ == "__main__":
    main()
