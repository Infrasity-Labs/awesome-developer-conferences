"""Draw every SVG the README uses (banner, per-region bars, charts, pipeline).

Standard library only. Each graphic is written twice, light and dark, and
embedded with a <picture> element so GitHub shows the one that matches the
reader's theme. Only system fonts are used so the files render the same inside
GitHub's <img> sandbox. All numbers come from the stats dict that
build_readme.py computes from events/*.md on every nightly run.
"""
import os
from xml.sax.saxutils import escape

import hero_banner

ASSET_DIR = os.path.join(".github", "assets")
REPO_SLUG = "infrasity-labs / awesome-developer-conferences"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "light": dict(panel="#f6f8fa", line="#d1d9e0", card="#ffffff", fg="#1f2328", muted="#59636e",
                  dim="#818b98", accent="#6a5af0", accent_bg="#ece9ff", track="#eef1f4", green="#1a7f37"),
    "dark": dict(panel="#151b23", line="#30363d", card="#0d1117", fg="#f0f6fc", muted="#9198a1",
                 dim="#6e7681", accent="#8b7dff", accent_bg="#262046", track="#1d242d", green="#3fb950"),
}


def _t(x, y, text, size, fill, weight=None, anchor=None, family=SANS, spacing=None, tabular=False):
    a = [f'x="{x}"', f'y="{y}"', f'font-family="{family}"', f'font-size="{size}"', f'fill="{fill}"']
    if weight:
        a.append(f'font-weight="{weight}"')
    if anchor:
        a.append(f'text-anchor="{anchor}"')
    if spacing:
        a.append(f'letter-spacing="{spacing}"')
    if tabular:
        a.append('style="font-variant-numeric:tabular-nums"')
    return f'<text {" ".join(a)}>{escape(str(text))}</text>'


def _svg(w, h, label, body, desc=None):
    title = f'<title id="t">{escape(label)}</title>\n<desc id="d">{escape(desc)}</desc>\n' if desc else ""
    aria = 'aria-labelledby="t d"' if desc else f'aria-label="{escape(label)}"'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" {aria}>\n{title}{body}\n</svg>\n')


def _panel(w, h, c, rx=14):
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{c["panel"]}" stroke="{c["line"]}"/>'


def banner(s, c):
    tiles = [
        (f"{s['upcoming']:,}", "upcoming events", False),
        (f"+{s['added']:,}", "new since last run", True),
        (f"{s['countries']:,}", "countries", False),
        (f"{s['online_pct']}%", "online or hybrid", False),
    ]
    out = [_panel(1280, 360, c, 16),
           f'<rect x="64" y="56" width="34" height="34" rx="8" fill="{c["accent"]}"/>',
           f'<rect x="73" y="66" width="16" height="15" rx="2" fill="none" stroke="#ffffff" stroke-width="2.5"/>',
           '<path d="M73 71 h16" stroke="#ffffff" stroke-width="2.5"/>',
           _t(112, 82, REPO_SLUG, 15, c["muted"], family=MONO),
           _t(64, 138, "Developer Events & Conferences", 50, c["fg"], 700, spacing=-1.2),
           _t(64, 172, "Developer, cloud-native and open-source conferences worldwide. Refreshed nightly.", 19, c["muted"])]
    for i, (num, label, hot) in enumerate(tiles):
        x = 64 + i * 286
        if hot:
            out.append(f'<rect x="{x}" y="200" width="266" height="96" rx="12" fill="{c["accent_bg"]}" stroke="{c["accent"]}" stroke-opacity="0.55"/>')
        else:
            out.append(f'<rect x="{x}" y="200" width="266" height="96" rx="12" fill="{c["card"]}" stroke="{c["line"]}"/>')
        out.append(_t(x + 22, 252, num, 36, c["accent"] if hot else c["fg"], 700, spacing=-0.8, tabular=True))
        out.append(_t(x + 22, 278, label, 15, c["muted"]))
    out.append(f'<circle cx="70" cy="328" r="4" fill="{c["green"]}"/>')
    out.append(_t(82, 333, f"last run {s['when']}  ·  next run 00:00 UTC  ·  {s['sources']} sources", 13, c["dim"], family=MONO))
    desc = (f"{s['upcoming']:,} upcoming developer events in {s['countries']} countries; "
            f"{s['added']:,} new since the last run; updated {s['when']}.")
    return _svg(1280, 360, "Developer Events & Conferences", "\n".join(out), desc)


def bar(count, new, scale_max, c):
    w = 240
    total_w = round(count / scale_max * w) if scale_max else 0
    if count:
        total_w = max(total_w, 6)
    new_w = round(new / scale_max * w) if scale_max else 0
    if new:
        new_w = max(min(new_w, total_w), 5)
    body = f'<rect x="0" y="0" width="{w}" height="12" rx="4" fill="{c["track"]}"/>'
    if total_w:
        body += f'<rect x="0" y="0" width="{total_w}" height="12" rx="4" fill="{c["accent"]}" fill-opacity="0.45"/>'
    if new_w:
        body += f'<rect x="0" y="0" width="{new_w}" height="12" rx="4" fill="{c["accent"]}"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="12" viewBox="0 0 {w} 12">{body}</svg>\n'


def _hbar_chart(title, subtitle, rows, c, label_max=24):
    n = max(len(rows), 1)
    h = 109 + 34 * (n - 1) + 45
    out = [_panel(620, h, c), _t(28, 44, title, 19, c["fg"], 650), _t(28, 68, subtitle, 13.5, c["muted"])]
    top = max((v for _, v in rows), default=1) or 1
    for i, (label, value) in enumerate(rows):
        y = 109 + 34 * i
        w = max(round(value / top * 360), 6)
        name = label if len(label) <= label_max else label[:label_max - 1].rstrip() + "…"
        out.append(_t(28, y, name, 14, c["fg"]))
        out.append(f'<rect x="190" y="{y - 12}" width="{w}" height="16" rx="4" fill="{c["accent"]}"/>')
        out.append(_t(190 + w + 8, y + 1, f"{value:,}", 13.5, c["muted"], 600, tabular=True))
    return _svg(620, h, title, "\n".join(out))


def by_month(s, c):
    return _hbar_chart("When events happen", f"Upcoming events by start month, next {len(s['months'])} months",
                       s["months"], c)


def top_countries(s, c):
    return _hbar_chart("Where events happen", f"Upcoming in-person events, top {len(s['top_countries'])} of {s['countries']} countries",
                       s["top_countries"], c)


def pipeline(s, c):
    steps = [
        ("Fetch", f"{s['sources']} sources: GDG, CNCF, Luma,", "Meetup, dev.events and more"),
        ("Merge", "New events deduplicated into", "one file per region"),
        ("Check", "Dates, dead links and", "spelling verified"),
        ("Publish", "README, region lists and", "country pages rebuilt"),
    ]
    out = [_panel(1280, 230, c), _t(28, 44, "Every night at 00:00 UTC", 19, c["fg"], 650),
           _t(1252, 44, ".github/workflows/update-all-events.yml", 13, c["dim"], anchor="end", family=MONO)]
    for i, (name, l1, l2) in enumerate(steps):
        x = 28 + i * 310
        last = i == len(steps) - 1
        fill, stroke, op = (c["accent_bg"], c["accent"], ' stroke-opacity="0.55"') if last else (c["card"], c["line"], "")
        out.append(f'<rect x="{x}" y="70" width="266" height="120" rx="12" fill="{fill}" stroke="{stroke}"{op}/>')
        out.append(f'<circle cx="{x + 30}" cy="102" r="13" fill="{c["accent"]}"/>')
        out.append(_t(x + 30, 107, i + 1, 13, "#ffffff", 700, anchor="middle"))
        out.append(_t(x + 54, 108, name, 18, c["fg"], 650))
        out.append(_t(x + 20, 146, l1, 14, c["muted"]))
        out.append(_t(x + 20, 167, l2, 14, c["muted"]))
        if not last:
            out.append(f'<path d="M{x + 274} 130 h28" stroke="{c["dim"]}" stroke-width="2" fill="none"/>')
            out.append(f'<path d="M{x + 296} 124 l7 6 l-7 6" stroke="{c["dim"]}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    return _svg(1280, 230, "How the nightly run works", "\n".join(out))


def new_tag(c):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="38" height="18" viewBox="0 0 38 18">'
            f'<rect width="38" height="18" rx="9" fill="{c["accent"]}"/>'
            f'<text x="19" y="12.6" text-anchor="middle" font-family="{SANS}" font-size="10" font-weight="700" '
            'letter-spacing="0.6" fill="#ffffff">NEW</text></svg>\n')


def _write(root, name, text):
    path = os.path.join(root, ASSET_DIR, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_all(s, root="."):
    """Write every graphic. `s` is the stats dict built by build_readme.compute_stats."""
    scale = max((r["count"] for r in s["regions"]), default=1) or 1
    _write(root, "hero.svg", hero_banner.render("events", ("Every developer", "conference."),
           f"{s['upcoming']:,} upcoming events across {s['countries']} countries", f"{s['upcoming']:,} events"))
    for theme, c in THEMES.items():
        _write(root, f"banner-{theme}.svg", banner(s, c))
        _write(root, f"by-month-{theme}.svg", by_month(s, c))
        _write(root, f"top-countries-{theme}.svg", top_countries(s, c))
        _write(root, f"pipeline-{theme}.svg", pipeline(s, c))
        for r in s["regions"]:
            _write(root, f"bars/{r['key']}-{theme}.svg", bar(r["count"], r["new"], scale, c))
    _write(root, "new.svg", new_tag(THEMES["light"]))
