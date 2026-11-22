import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

import build_readme
import events_store as es

ROWS = {
    "Europe": (
        "| Big Conf Berlin | 2099-05-04 to 2099-05-06 | Berlin, Germany | [↗](https://bigconf.example/berlin) |\n"
        "| Old Meetup | 2001-01-01 | Paris, France | [↗](https://old.example) |\n"
    ),
    "Virtual/Online": "| Remote Summit | 2099-06-01 | Virtual/Online | [↗](https://remote.example) |\n",
}


class BuildReadmeTest(unittest.TestCase):
    def build(self, previous=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "events").mkdir()
        for region, rows in ROWS.items():
            (root / "events" / f"{es.slug(region)}.md").write_text(es.new_region_text(region, rows), encoding="utf-8")
        old = os.getcwd()
        os.chdir(root)
        try:
            stats = build_readme.compute_stats(date(2099, 1, 1), ".", previous, "01 Jan 2099, 00:00 UTC")
            build_readme.readme_assets.write_all(stats, ".")
        finally:
            os.chdir(old)
        return root, stats

    def test_only_upcoming_events_are_counted(self):
        _, stats = self.build()
        self.assertEqual(stats["upcoming"], 2)
        self.assertEqual(stats["countries"], 1)
        self.assertEqual(stats["online_pct"], 50)

    def test_new_events_are_those_missing_from_previous_run(self):
        previous = {"| Remote Summit | 2099-06-01 | Virtual/Online | [↗](https://remote.example) |"}
        _, stats = self.build(previous)
        self.assertEqual(stats["added"], 1)

    def test_without_history_nothing_is_marked_new(self):
        _, stats = self.build(None)
        self.assertEqual(stats["added"], 0)

    def test_graphics_are_written_in_light_and_dark(self):
        root, _ = self.build()
        for name in ("banner", "by-month", "top-countries", "pipeline"):
            for theme in ("light", "dark"):
                svg = (root / ".github" / "assets" / f"{name}-{theme}.svg").read_text(encoding="utf-8")
                self.assertTrue(svg.startswith("<svg"))

    def test_parse_start_end(self):
        self.assertEqual(build_readme.parse_start_end("2026-01-02 to 2026-01-04"), (date(2026, 1, 2), date(2026, 1, 4)))
        self.assertEqual(build_readme.parse_start_end("TBA"), (None, None))


if __name__ == "__main__":
    unittest.main()
