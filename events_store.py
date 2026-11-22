"""Shared access to the event tables.

The tables live in one Markdown file per region under events/, so every file
stays small enough for GitHub to render. README.md is only an overview that
build_readme.py regenerates from these files.
"""
import os
import re

EVENTS_DIR = "events"
REGIONS = ["Africa", "Asia", "Australia", "Europe", "North America", "South America", "Virtual/Online"]

BLURBS = {
    "Africa": "Developer conferences, DevFests and community summits across Africa.",
    "Asia": "Developer conferences, summits and community events across Asia.",
    "Australia": "Developer conferences and meetups across Australia and Oceania.",
    "Europe": "Developer conferences, summits and community events across Europe.",
    "North America": "Developer conferences, summits and meetups across the United States, Canada and Mexico.",
    "South America": "Developer conferences and community events across South America.",
    "Virtual/Online": "Online and hybrid developer events you can join from anywhere.",
}

TABLE_HEAD = "| Event Name | Date | Location | Register |\n|------------|------|----------|----------|\n"
ROW_SPLIT = re.compile(r"(?<!\\)\|")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def region_file(region, root="."):
    return os.path.join(root, EVENTS_DIR, f"{slug(region)}.md")


def event_files(root="."):
    """Existing region files, in README order."""
    return [p for p in (region_file(r, root) for r in REGIONS) if os.path.exists(p)]


def new_region_text(region, rows=""):
    return (f"# {region} developer events\n\n{BLURBS.get(region, '')} "
            f"[Back to the directory](../README.md)\n\n### {region}\n\n{TABLE_HEAD}{rows}")


def parse_rows(text):
    """Yield (line, name, date, location, register) for every table row in a region file."""
    for line in text.split("\n"):
        if not line.startswith("|") or line.startswith("| Event Name") or line.startswith("|--"):
            continue
        parts = ROW_SPLIT.split(line)
        if len(parts) >= 5:
            yield line, parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()


def link_of(register):
    m = re.search(r"\[.*?\]\((.*?)\)", register)
    return m.group(1).strip() if m else register.strip()
