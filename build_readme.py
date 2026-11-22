"""Rebuild README.md and its graphics from events/*.md.

Runs last in the nightly workflow (after aggregate.py, the checks, the dedupe
step and build_country_index.py). The README is a short overview: stats, a
region table, the next conferences, a country index and charts. The event
tables themselves live in events/<region>.md and countries/<country>.md.

    python build_readme.py                    # normal nightly run
    python build_readme.py --previous-ref REF # diff against README.md at git REF
                                              # (one-off, for repos not yet split)
"""
import argparse
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

import events_store as es
import readme_assets
from build_country_index import collect_by_country, ordered_countries, read_events, slugify

REPO = "Infrasity-Labs/awesome-developer-conferences"
BRANCH = "master"
ASSETS = "./.github/assets"
TOP_COUNTRIES_SHOWN = 12
NEXT_CONFERENCES = 10
WORKFLOW = os.path.join(".github", "workflows", "update-all-events.yml")

# Community meetup platforms: kept in the regional lists, left out of "Next conferences"
MEETUP_HOSTS = ("lu.ma", "luma.com", "meetup.com", "gdg.community.dev", "ocgroups.dev", "eventbrite.com",
                "allevents.in", "eventbrite.co.uk", "10times.com", "startupgrind.com")
MAX_CONFERENCE_DAYS = 7

# --------------------------------------------------------------------------- data


def parse_start_end(date_str):
    """Return (start, end) dates for 'YYYY-MM-DD' or 'YYYY-MM-DD to YYYY-MM-DD', else (None, None)."""
    try:
        parts = [datetime.strptime(p.strip(), "%Y-%m-%d").date() for p in date_str.split(" to ")]
    except ValueError:
        return None, None
    return parts[0], parts[-1]


def source_count(root="."):
    """Number of fetchers in the nightly workflow matrix."""
    try:
        with open(os.path.join(root, WORKFLOW), encoding="utf-8") as f:
            text = f.read()
        block = text.split("script:", 1)[1].split("steps:", 1)[0]
        return len(re.findall(r"^\s*-\s+[a-z_]+\s*$", block, re.M))
    except (OSError, IndexError):
        return 27


def _git_show(ref_path):
    try:
        return subprocess.run(["git", "show", ref_path], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def previous_lines(root=".", previous_ref=None):
    """Set of table rows from the previous run, or None when unknown.

    Normally that is events/<region>.md at HEAD (the last nightly commit). With
    previous_ref it is the tables of an old monolithic README.md at that ref.
    """
    rows = set()
    if previous_ref:
        text = _git_show(f"{previous_ref}:README.md")
        if text is None:
            return None
        rows.update(line for line, *_ in es.parse_rows(text))
        return rows
    found = False
    for region in es.REGIONS:
        text = _git_show(f"HEAD:{es.EVENTS_DIR}/{es.slug(region)}.md")
        if text is not None:
            found = True
            rows.update(line for line, *_ in es.parse_rows(text))
    return rows if found else None


def compute_stats(today, root=".", previous=None, when=None):
    when = when or datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    per_region = {r: [0, 0] for r in es.REGIONS}
    months = Counter()
    upcoming_events = []
    for region, line, name, date, location, register in read_events(root):
        start, end = parse_start_end(date)
        if not end or end < today:
            continue
        is_new = previous is not None and line not in previous
        per_region[region][0] += 1
        per_region[region][1] += is_new
        m = max(start, today)
        months[(m.year, m.month)] += 1
        upcoming_events.append(dict(region=region, line=line, name=name, date=date, start=start,
                                    location=location, url=es.link_of(register), new=is_new))

    by_country = collect_by_country(today, root)
    total = sum(c for c, _ in per_region.values())
    added = sum(n for _, n in per_region.values())

    month_rows = []
    y, mth = today.year, today.month
    for _ in range(12):
        month_rows.append((datetime(y, mth, 1).strftime("%b %Y"), months.get((y, mth), 0)))
        mth += 1
        if mth == 13:
            y, mth = y + 1, 1

    ordered = ordered_countries(by_country)
    top = sorted(((c, len(by_country[c])) for c in ordered), key=lambda t: (-t[1], t[0]))[:10]
    online = per_region["Virtual/Online"][0]
    new_urls = {e["url"] for e in upcoming_events if e["new"]}

    return {
        "upcoming": total, "added": added, "when": when, "sources": source_count(root),
        "countries": len(by_country), "online_pct": round(100 * online / total) if total else 0,
        "regions": [{"label": r, "key": es.slug(r), "count": per_region[r][0], "new": per_region[r][1]}
                    for r in es.REGIONS],
        "months": month_rows, "top_countries": top,
        "by_country": by_country, "ordered": ordered, "events": upcoming_events, "new_urls": new_urls,
    }

# --------------------------------------------------------------------------- markdown


def picture(name, alt, width=None):
    w = f' width="{width}"' if width else ""
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{ASSETS}/{name}-dark.svg">\n'
            f'  <img{w} alt="{alt}" src="{ASSETS}/{name}-light.svg">\n</picture>')


def _cut(text, n):
    text = (text or "").replace("|", "/").replace("\n", " ").strip()
    return text if len(text) <= n else text[:n - 1].rstrip(" ,;/-–") + "…"


def next_conferences(stats, today):
    """The next in-person conferences by start date, skipping community meetup platforms."""
    picks = []
    for e in stats["events"]:
        host = urlparse(e["url"]).netloc.lower()
        end = parse_start_end(e["date"])[1]
        if e["region"] == "Virtual/Online" or e["start"] is None or e["start"] < today:
            continue
        if (end - e["start"]).days > MAX_CONFERENCE_DAYS:   # year-long programs and rolling series
            continue
        if any(host == h or host.endswith("." + h) for h in MEETUP_HOSTS):
            continue
        picks.append(e)
    picks.sort(key=lambda e: (e["start"], e["name"]))
    return picks[:NEXT_CONFERENCES]


def head():
    badge = lambda label, msg, color: (f"https://img.shields.io/badge/{label}-{msg}-{color}?style=flat-square&labelColor=2b3036")
    return f'''<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="{ASSETS}/banner-dark.svg">
    <img width="100%" alt="Developer Events & Conferences: upcoming developer conferences worldwide, refreshed nightly" src="{ASSETS}/banner-light.svg">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/sindresorhus/awesome"><img alt="Awesome" src="https://awesome.re/badge-flat2.svg"></a>
  <a href="https://github.com/{REPO}/actions/workflows/update-all-events.yml"><img alt="Nightly update" src="https://img.shields.io/github/actions/workflow/status/{REPO}/update-all-events.yml?label=nightly%20update&style=flat-square&labelColor=2b3036"></a>
  <a href="https://github.com/{REPO}/commits/{BRANCH}"><img alt="Last update" src="https://img.shields.io/github/last-commit/{REPO}/{BRANCH}?label=last%20update&style=flat-square&labelColor=2b3036"></a>
  <a href="https://github.com/{REPO}/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/{REPO}?style=flat-square&labelColor=2b3036"></a>
  <a href="./LICENSE"><img alt="MIT license" src="https://img.shields.io/github/license/{REPO}?style=flat-square&labelColor=2b3036"></a>
  <a href="./CONTRIBUTING.md"><img alt="PRs welcome" src="{badge('PRs', 'welcome', '6a5af0')}"></a>
</p>

<p align="center">
  <b>Every developer, cloud-native and open-source conference worth knowing about, in one place.</b><br>
  KubeCon, PlatformCon, DevOpsCon, Open Source Summit, DevFests and thousands more. Free, updated every night.
</p>

<p align="center">
  <a href="#browse-by-region"><b>Browse by region</b></a> &nbsp;·&nbsp;
  <a href="#next-conferences"><b>Next conferences</b></a> &nbsp;·&nbsp;
  <a href="#browse-by-country"><b>Browse by country</b></a> &nbsp;·&nbsp;
  <a href="#how-it-works"><b>How it works</b></a> &nbsp;·&nbsp;
  <a href="#add-an-event"><b>Add an event</b></a> &nbsp;·&nbsp;
  <a href="https://github.com/{REPO}/subscription"><b>Watch for updates</b></a>
</p>
'''


def tail():
    badge = lambda label, msg, color: (f"https://img.shields.io/badge/{label}-{msg}-{color}?style=flat-square&labelColor=2b3036")
    return f'''
## Add an event

<p>
  <a href="https://github.com/{REPO}/issues/new?template=submit_conference.md"><img alt="Submit a conference" src="{badge('Submit', 'a%20conference', '6a5af0')}"></a>
  <a href="https://github.com/{REPO}/issues/new?template=bug_report.md"><img alt="Report a bad listing" src="{badge('Report', 'a%20bad%20listing', '2b3036')}"></a>
</p>

Know a conference we are missing? Open an issue, or add a row to the right file in [`events/`](./events) and send a pull request. The format and the fetcher guide are in [CONTRIBUTING.md](./CONTRIBUTING.md).

---

<p align="center">
  <sub>Maintained by <a href="https://infrasity.com"><b>Infrasity</b></a>, a developer marketing agency for DevTools and B2B SaaS. We run this in public because we work in this space every day.</sub><br>
  <sub><a href="https://infrasity.com">Website</a> · <a href="https://linkedin.com/company/infrasity">LinkedIn</a> · <a href="./LICENSE">MIT License</a> · <a href="./CODE_OF_CONDUCT.md">Code of Conduct</a></sub>
</p>
'''


def body(stats, today):
    rows = ["| Region | Upcoming | New | |", "|:--|--:|--:|:--|"]
    for r in stats["regions"]:
        new = f"+{r['new']}" if r["new"] else "—"
        rows.append(f"| [{r['label']}](events/{r['key']}.md) | **{r['count']:,}** | {new} | "
                    f"{picture('bars/' + r['key'], str(r['count']) + ' events')} |".replace("\n", " "))

    nxt = ["| Conference | Date | Location | |", "|:--|:--|:--|:-:|"]
    for e in next_conferences(stats, today):
        tag = f' <img src="{ASSETS}/new.svg" height="16" alt="new">' if e["new"] else ""
        nxt.append(f"| **{_cut(e['name'], 70)}**{tag} | {e['date']} | {_cut(e['location'], 40) or '—'} | "
                   f"[Register ↗]({e['url']}) |")

    ordered, by_country = stats["ordered"], stats["by_country"]
    def country_rows(names):
        return ["| Country | Upcoming |", "|:--|--:|"] + [
            f"| [{c}](countries/{slugify(c)}.md) | {len(by_country[c])} |" for c in names]
    shown, rest = ordered[:TOP_COUNTRIES_SHOWN], ordered[TOP_COUNTRIES_SHOWN:]
    country_md = "\n".join(country_rows(shown))
    if rest:
        country_md += (f"\n\n<details>\n<summary><b>Show {len(rest)} more countries</b></summary>\n\n"
                       + "\n".join(country_rows(rest)) + "\n\n</details>")

    return "\n".join([
        "## Browse by region", "",
        "Every event sits in one list per region, soonest first. Events drop off a week after they end.", "",
        "\n".join(rows), "",
        "<sub>Bars share one scale. The darker part of each bar is events added in the last run.</sub>", "",
        "## Next conferences", "",
        "The next in-person conferences by start date. Community meetups from Meetup, Luma and GDG are in the regional lists.", "",
        "\n".join(nxt), "",
        "## Events at a glance", "",
        "<p align=\"center\">", picture("by-month", "Upcoming events by month", "49%"),
        picture("top-countries", "Upcoming events by country", "49%"), "</p>", "",
        "## Browse by country", "",
        "Jump straight to upcoming in-person events in a country. Each page is rebuilt nightly.", "",
        country_md, "",
        "## How it works", "",
        "<p align=\"center\">", picture("pipeline", "Fetch, merge, check, publish: the nightly pipeline", "100%"), "</p>", "",
        "Don't edit `README.md`, `countries/` or `.github/assets/` by hand: the next run rebuilds them. "
        "The event tables you can edit live in [`events/`](./events).", "",
    ])


def build(today=None, root=".", previous_ref=None, when=None):
    today = today or datetime.now().date()
    stats = compute_stats(today, root, previous_lines(root, previous_ref), when)
    text = head() + "\n" + body(stats, today) + tail()
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as f:
        f.write(text)
    readme_assets.write_all(stats, root)
    return stats, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previous-ref", help="git ref whose README.md holds the previous run's tables")
    ap.add_argument("--when", help="override the 'last run' timestamp (one-off seeding)")
    args = ap.parse_args()
    stats, text = build(previous_ref=args.previous_ref, when=args.when)
    print(f"README.md rebuilt: {stats['upcoming']} upcoming, +{stats['added']} new, "
          f"{stats['countries']} countries, {len(text) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
