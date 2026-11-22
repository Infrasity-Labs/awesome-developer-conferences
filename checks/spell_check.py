import argparse
import os
import re
import sys
from spellchecker import SpellChecker
from parse_readme import event_files


def check_lines(lines, spell, safe_targets):
    """Return (issues, corrected_lines) for the rows of one event file."""
    issues = []
    new_lines = []
    for i, line in enumerate(lines):
        line_num = i + 1
        if line.strip().startswith('|') and 'Event Name' not in line and not line.strip().startswith('|-'):
            parts = re.split(r'(?<!\\)\|', line)
            if len(parts) >= 5:
                event_name = parts[1].strip()

                def correct_match(match):
                    word = match.group(0)

                    if not word.isalpha() or word.isupper():
                        return word
                    if not word.islower() and not word.istitle() and not word.isupper():
                        return word

                    lower_word = word.lower()
                    if not spell.unknown([lower_word]):
                        return word

                    correction = spell.correction(lower_word)
                    if correction and correction != lower_word and correction in safe_targets:
                        issues.append(f"Line {line_num} | {event_name} | Typo '{word}' -> '{correction}'")
                        return correction.title() if word.istitle() else correction
                    return word

                parts[1] = re.sub(r'[a-zA-Z]+', correct_match, parts[1])
                parts[3] = re.sub(r'[a-zA-Z]+', correct_match, parts[3])
                line = '|'.join(parts)

        new_lines.append(line)
    return issues, new_lines

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--fix', action='store_true')
    args = parser.parse_args()
    
    if not args.report and not args.fix:
        parser.error("Must specify --report or --fix")
        
    spell = SpellChecker()
    spell.word_frequency.load_words(['unconference', 'intelligenza', 'artificiale'])
    
    safe_targets = {
        "open", "source", "summit", "conference", "developer", "engineering",
        "security", "world", "congress", "virtual", "online", "europe", "america",
        "asia", "africa", "tech", "technology", "data", "cloud", "native", 
        "artificial", "intelligence", "machine", "learning", "global", "annual",
        "event", "forum", "symposium", "expo", "festival", "workshop", "bootcamp"
    }
    
    all_issues = []
    for path in event_files():
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
        issues, new_lines = check_lines(lines, spell, safe_targets)
        if issues:
            all_issues.extend(f"{os.path.basename(path)}: {i}" for i in issues)
            if args.fix:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

    if all_issues:
        print(f"Found {len(all_issues)} typos:")
        for iss in all_issues:
            print(iss)
        if args.fix:
            print(f"Successfully fixed {len(all_issues)} typos!")
        if args.report:
            sys.exit(1)
    else:
        print("No typos found.")
        sys.exit(0)

if __name__ == '__main__':
    main()
