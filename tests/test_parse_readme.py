from datetime import date

import pytest

from checks.parse_readme import parse_date, parse_readme


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2027-04-10", date(2027, 4, 10)),
        ("Apr 10, 2027", date(2027, 4, 1)),
    ],
)
def test_parse_date(value, expected):
    assert parse_date(value) == expected


def test_parse_readme_preserves_escaped_pipes(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        """### Europe
| Event Name | Date | Location | Register |
|---|---|---|---|
| Python \\| Data Summit | 2027-04-10 | Berlin, Germany | [Register](https://example.com) |
""",
        encoding="utf-8",
    )

    assert parse_readme(readme) == [
        {
            "line_number": 4,
            "region": "Europe",
            "name": "Python | Data Summit",
            "date_raw": "2027-04-10",
            "date_start": date(2027, 4, 10),
            "date_end": date(2027, 4, 10),
            "location": "Berlin, Germany",
            "url": "https://example.com",
        }
    ]
