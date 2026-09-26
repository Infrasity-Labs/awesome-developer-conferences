import pytest

from fetchers.config import deduplicate_events, determine_region, parse_date


@pytest.mark.parametrize(
    ("location", "expected_region"),
    [
        ("Nairobi, Kenya", "Africa"),
        ("Sydney, Australia", "Australia"),
        ("São Paulo, Brazil", "South America"),
        ("Berlin, Germany", "Europe"),
        ("Toronto, Canada", "North America"),
        ("Singapore", "Asia"),
    ],
)
def test_determine_region(location, expected_region):
    assert determine_region(location) == expected_region


def test_determine_region_uses_event_details_for_unknown_locations():
    assert (
        determine_region(
            "Unknown",
            name="PyCon Berlin",
            link="https://example.com/events/berlin",
        )
        == "Europe"
    )


def test_deduplicate_events_keeps_same_series_in_different_cities():
    events = [
        {"name": "PyCon 2027", "date": "2027-04-10", "location": "Berlin, Germany"},
        {"name": "PyCon 2027", "date": "2027-04-10", "location": "Paris, France"},
    ]

    assert deduplicate_events(events) == events


def test_deduplicate_events_collapses_reworded_same_event():
    first = {
        "name": "PyCon Conference 2027",
        "date": "2027-04-10",
        "location": "Berlin, Germany",
    }
    duplicate = {
        "name": "PyCon 2027",
        "date": "2027-04-12",
        "location": "Berlin (Germany)",
    }

    assert deduplicate_events([first, duplicate]) == [first]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2027-04-10 to 2027-04-12", "2027-04-10"),
        ("Apr 10, 2027", "2027-04-01"),
    ],
)
def test_parse_date(value, expected):
    assert parse_date(value) == expected
