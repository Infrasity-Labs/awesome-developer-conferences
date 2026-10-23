"""Builds the "Browse by Country" index.

Writes countries/<slug>.md for every country with upcoming events and refreshes
the index table in README.md between the COUNTRY-INDEX markers. Run after
aggregate.py so it reflects the merged event list.
"""
import os
import re
from datetime import datetime

from fetchers.countries import BIG_COUNTRIES, determine_country

START, END = '<!-- COUNTRY-INDEX:START -->', '<!-- COUNTRY-INDEX:END -->'
ROW_SPLIT = re.compile(r'(?<!\\)\|')
REGION_HEADING = re.compile(r'^### (.+)$')


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def parse_events(readme):
    """Yield (region, row_line, name, date, location) for each table row."""
    region = None
    for line in readme.split('\n'):
        m = REGION_HEADING.match(line)
        if m:
            region = m.group(1).strip()
            continue
        if not line.startswith('|') or line.startswith('| Event Name') or line.startswith('|--'):
            continue
        parts = ROW_SPLIT.split(line)
        if len(parts) >= 5:
            yield region, line, parts[1].strip(), parts[2].strip(), parts[3].strip()


def is_upcoming(date_str, today):
    last = date_str.split(' to ')[-1].strip()
    try:
        return datetime.strptime(last, '%Y-%m-%d').date() >= today
    except ValueError:
        return False


def main():
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    today = datetime.now().date()
    by_country = {}
    for region, line, _name, date, location in parse_events(readme):
        if region == 'Virtual/Online' or not is_upcoming(date, today):
            continue
        country = determine_country(location)
        if country:
            by_country.setdefault(country, []).append((date.split(' to ')[0].strip(), line))

    os.makedirs('countries', exist_ok=True)
    for stale in os.listdir('countries'):
        if stale.endswith('.md'):
            os.remove(os.path.join('countries', stale))

    for country, rows in by_country.items():
        rows.sort(key=lambda r: r[0])
        with open(os.path.join('countries', f'{slugify(country)}.md'), 'w', encoding='utf-8') as f:
            f.write(f'# Developer Events in {country}\n\n')
            f.write(f'{len(rows)} upcoming events. [Back to the full directory](../README.md)\n\n')
            f.write('| Event Name | Date | Location | Register |\n|------------|------|----------|----------|\n')
            f.write('\n'.join(r[1] for r in rows) + '\n')

    big = [c for c in BIG_COUNTRIES if c in by_country]
    others = sorted((c for c in by_country if c not in BIG_COUNTRIES), key=lambda c: (-len(by_country[c]), c))
    ordered = sorted(big, key=lambda c: (-len(by_country[c]), c)) + others

    lines = [START, '## 🌍 Browse by Country', '',
             'Jump straight to upcoming events in a country. Pages refresh daily with the main list.', '',
             '| Country | Upcoming events |', '|---------|-----------------|']
    for c in ordered:
        lines.append(f'| [{c}](countries/{slugify(c)}.md) | {len(by_country[c])} |')
    lines += ['', END]
    block = '\n'.join(lines)

    if START in readme and END in readme:
        readme = re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: block, readme, flags=re.DOTALL)
    else:
        marker = '<!-- THE TABULAR DATA -->'
        readme = readme.replace(marker, block + '\n\n' + marker, 1)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f'Country index built: {len(by_country)} countries.')


if __name__ == '__main__':
    main()
