import argparse
import sys
from datetime import date, timedelta
from parse_readme import parse_readme
import re

def is_year_typo(d):
    # Year shouldn't be crazy far in the future or past
    if d:
        current_year = date.today().year
        if d.year > current_year + 5 or d.year < 2020:
            return True
    return False

def check_dates(events, grace_days=7):
    today = date.today()
    grace_period = timedelta(days=grace_days)
    
    issues = []
    lines_to_remove = set()
    
    for ev in events:
        line_num = ev['line_number']
        
        if ev['date_raw'].lower() == 'tba' or ev['date_raw'].lower() == 'tbd':
            continue # Allow TBA
            
        # 1. Invalid date format
        if not ev['date_start']:
            issues.append(f"Line {line_num} | {ev['name']} | Invalid start date format: {ev['date_raw']}")
            lines_to_remove.add(line_num)
            continue
            
        # 2. Year typo
        if is_year_typo(ev['date_start']) or is_year_typo(ev['date_end']):
            issues.append(f"Line {line_num} | {ev['name']} | Year typo in date: {ev['date_raw']}")
            lines_to_remove.add(line_num)
            continue
            
        # 3. End date before start date
        if ev['date_end'] and ev['date_end'] < ev['date_start']:
            issues.append(f"Line {line_num} | {ev['name']} | End date before start date: {ev['date_raw']}")
            lines_to_remove.add(line_num)
            continue
            
        # 4. Past events
        compare_date = ev['date_end'] if ev['date_end'] else ev['date_start']
        if compare_date + grace_period < today:
            issues.append(f"Line {line_num} | {ev['name']} | Event is in the past: {ev['date_raw']}")
            lines_to_remove.add(line_num)
            continue
            
    return issues, lines_to_remove

def main():
    parser = argparse.ArgumentParser(description="Check dates in README.md")
    parser.add_argument('--report', action='store_true', help="Print issues and exit 1 if any")
    parser.add_argument('--fix', action='store_true', help="Remove invalid/past events from README.md")
    args = parser.parse_args()
    
    if not args.report and not args.fix:
        parser.error("Must specify --report or --fix")
        
    events = parse_readme("../README.md" if __name__ != "__main__" else "README.md")
    issues, lines_to_remove = check_dates(events)
    
    if issues:
        print(f"Found {len(issues)} date issues:")
        for iss in issues:
            print(iss)
            
        if args.fix:
            print(f"Removing {len(lines_to_remove)} rows from README.md...")
            with open("README.md", "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # 1-indexed to 0-indexed
            remove_indices = {num - 1 for num in lines_to_remove}
            
            with open("README.md", "w", encoding="utf-8") as f:
                for i, line in enumerate(lines):
                    if i not in remove_indices:
                        f.write(line)
            print("Done fixing README.md.")
            
        if args.report:
            sys.exit(1)
    else:
        print("All dates look good!")
        sys.exit(0)

if __name__ == "__main__":
    main()
