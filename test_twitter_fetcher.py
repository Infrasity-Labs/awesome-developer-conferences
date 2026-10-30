import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "fetchers"))

import twitter


class TweetToRecordTest(unittest.TestCase):
    def test_keeps_expanded_links_and_drops_twitter_links(self):
        rec = twitter.tweet_to_record({
            "text": "Black Hat Asia is back! https://t.co/x",
            "created_at": "2026-10-01T12:00:00.000Z",
            "entities": {"urls": [
                {"expanded_url": "https://www.blackhat.com/asia-27/"},
                {"expanded_url": "https://x.com/BlackHatEvents/status/1"},
            ]},
        })
        self.assertEqual(rec["posted"], "2026-10-01")
        self.assertEqual(rec["links"], ["https://www.blackhat.com/asia-27/"])


class ToEventTuplesTest(unittest.TestCase):
    def test_builds_event_row_with_range(self):
        [(ev, end)] = twitter.to_event_tuples([{
            "name": "Black Hat Asia 2099", "start": "2099-04-01", "end": "2099-04-04",
            "location": "Singapore, Singapore", "url": "https://www.blackhat.com/asia-99/",
        }])
        self.assertEqual(ev["date"], "2099-04-01 to 2099-04-04")
        self.assertEqual(ev["line"], "| Black Hat Asia 2099 | 2099-04-01 to 2099-04-04 | Singapore, Singapore | [↗](https://www.blackhat.com/asia-99/) |")
        self.assertEqual(end.isoformat(), "2099-04-04")

    def test_drops_undated_malformed_and_promo_items(self):
        self.assertEqual(twitter.to_event_tuples([
            {"name": "No date", "start": None},
            {"name": "Bad date", "start": "soon"},
            "not a dict",
            {"name": "GITEX & AI Everything 50% off promo code", "start": "2099-01-01"},
        ]), [])

    def test_inverted_range_falls_back_to_single_day_and_bad_url_is_dropped(self):
        [(ev, end)] = twitter.to_event_tuples([
            {"name": "Conf", "start": "2099-05-02", "end": "2099-05-01", "url": "javascript:x"},
        ])
        self.assertEqual(ev["date"], "2099-05-02")
        self.assertEqual(ev["register"], "N/A")
        self.assertIsNone(end)


class MainWithoutKeysTest(unittest.TestCase):
    def test_skips_cleanly_without_credentials(self):
        saved = {k: os.environ.pop(k, None) for k in ("X_BEARER_TOKEN", "GEMINI_API_KEY")}
        try:
            self.assertEqual(twitter.main(), [])
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
