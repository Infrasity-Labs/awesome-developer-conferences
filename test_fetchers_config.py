import unittest

from fetchers import config


class MultiEventPromoPostTest(unittest.TestCase):
    def test_promo_guide_bundling_two_conferences_is_detected(self):
        self.assertTrue(
            config.is_multi_event_promo_post(
                "GITEX GLOBAL Dubai & AI Everything Abu Dhabi 2026 | GDG Dubai Promo Code Guide"
            )
        )

    def test_discount_code_bundling_two_conferences_is_detected(self):
        self.assertTrue(
            config.is_multi_event_promo_post(
                "50% Off GITEX 2026 & AI Everything Abu Dhabi - GDG Dubai Community Code GDGGTXE50"
            )
        )

    def test_ordinary_workshop_title_with_ampersand_is_not_flagged(self):
        self.assertFalse(
            config.is_multi_event_promo_post("Intro to Git & GitHub: Your First Steps in version control")
        )

    def test_title_without_ampersand_is_not_flagged(self):
        self.assertFalse(config.is_multi_event_promo_post("DevFest Yaounde 2026"))


if __name__ == "__main__":
    unittest.main()
