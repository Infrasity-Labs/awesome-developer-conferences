"""Builds the per-country event pages.

Writes countries/<slug>.md for every country with upcoming events. The README
overview (including the country table) is rebuilt by build_readme.py, which
imports collect_by_country() from here. Run after aggregate.py.
"""
import os
from datetime import datetime

import events_store
from fetchers.countries import BIG_COUNTRIES, determine_country


def slugify(name):
    return events_store.slug(name)


def is_upcoming(date_str, today):
    last = date_str.split(' to ')[-1].strip()
    try:
        return datetime.strptime(last, '%Y-%m-%d').date() >= today
    except ValueError:
        return False


def read_events(root='.'):
    """Yield (region, row_line, name, date, location, register) for every event row."""
    for region in events_store.REGIONS:
        path = events_store.region_file(region, root)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            for line, name, date, location, register in events_store.parse_rows(f.read()):
                yield region, line, name, date, location, register


def collect_by_country(today, root='.'):
    """{country: [(start_date_str, row_line), ...]} for upcoming in-person events."""
    by_country = {}
    for region, line, _name, date, location, _reg in read_events(root):
        if region == 'Virtual/Online' or not is_upcoming(date, today):
            continue
        country = determine_country(location)
        if country:
            by_country.setdefault(country, []).append((date.split(' to ')[0].strip(), line))
    return by_country


def ordered_countries(by_country):
    big = [c for c in BIG_COUNTRIES if c in by_country]
    others = sorted((c for c in by_country if c not in BIG_COUNTRIES), key=lambda c: (-len(by_country[c]), c))
    return sorted(big, key=lambda c: (-len(by_country[c]), c)) + others


def write_country_pages(by_country, root='.'):
    out_dir = os.path.join(root, 'countries')
    os.makedirs(out_dir, exist_ok=True)
    for stale in os.listdir(out_dir):
        if stale.endswith('.md'):
            os.remove(os.path.join(out_dir, stale))

    for country, rows in by_country.items():
        rows.sort(key=lambda r: r[0])
        with open(os.path.join(out_dir, f'{slugify(country)}.md'), 'w', encoding='utf-8') as f:
            f.write(f'# Developer Events in {country}\n\n')
            f.write(f'{len(rows)} upcoming events. [Back to the full directory](../README.md)\n\n')
            f.write(events_store.TABLE_HEAD)
            f.write('\n'.join(r[1] for r in rows) + '\n')


def main():
    by_country = collect_by_country(datetime.now().date())
    write_country_pages(by_country)
    print(f'Country pages built: {len(by_country)} countries.')


if __name__ == '__main__':
    main()
