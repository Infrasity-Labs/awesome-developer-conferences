import json
import os
import tempfile
import unittest
from pathlib import Path

import aggregate

README = """# Test

### Asia
| Event Name | Date | Location | Register |
|---|---|---|---|
| Build With Gemma Hackathon | 2099-08-01 | Mumbai, India | [link](https://example.com/one) |

</details>
"""


class AggregateDeduplicationTest(unittest.TestCase):
    def aggregate(self, events):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(README, encoding="utf-8")
            (root / "events_test.json").write_text(json.dumps(events), encoding="utf-8")
            old_cwd = Path.cwd()
            try:
                os.chdir(root)
                aggregate.main()
            finally:
                os.chdir(old_cwd)
            return (root / "README.md").read_text(encoding="utf-8")

    def test_distinct_event_with_longer_name_is_not_dropped(self):
        result = self.aggregate(
            [
                {
                    "name": "Build With Gemma Hackathon - in-a-box",
                    "date": "2099-08-02",
                    "location": "Delhi, India",
                    "register": "[link](https://example.com/two)",
                }
            ]
        )

        self.assertIn("Build With Gemma Hackathon - in-a-box", result)

    def test_same_event_is_still_deduplicated(self):
        result = self.aggregate(
            [
                {
                    "name": "Build With Gemma Hackathon",
                    "date": "2099-08-02",
                    "location": "Mumbai, India",
                    "register": "[link](https://example.com/two)",
                }
            ]
        )

        self.assertEqual(result.count("Build With Gemma Hackathon"), 1)


if __name__ == "__main__":
    unittest.main()
