from flask.testing import FlaskClient
from icalendar import Calendar
import re


def get_test_calendar(lang: str = "de"):
    # FIXME: we need better examples, at the moment they only have 5 events and
    # we could even merge multiple into one.
    with open(f"tests/calendar_{lang}.ics") as f:
        cal = Calendar.from_ical(f.read())
    return cal


def calendar_event_cnt(cal: Calendar) -> int:
    return sum([1 for c in cal.walk() if c.name == "VEVENT"])


def calendar_summaries(cal: Calendar) -> [str]:
    return [c.get("summary") for c in cal.walk() if c.name == "VEVENT"]


def calendar_descriptions(cal: Calendar) -> [str]:
    descriptions = [c.get("description") for c in cal.walk() if c.name == "VEVENT"]
    return [d for d in descriptions if d is not None]


def test_home_page(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200
    assert b"flofriday" in response.data
    assert b"Used by 0 students" in response.data


def test_verify_bad_url(client: FlaskClient, mocker):
    mocker.patch("app.tiss.get_calendar", return_value=None)

    response = client.get("/verify?url=nooAUrl")
    assert response.status_code == 400


def test_verify_not_tiss_url(client: FlaskClient, mocker):
    mocker.patch("app.tiss.get_calendar", return_value=get_test_calendar())

    response = client.get("/verify?url=https://example.com")
    assert response.status_code == 400


def test_verify_success(client: FlaskClient, mocker):
    mocker.patch("app.tiss.get_calendar", return_value=get_test_calendar())

    response = client.get(
        "/verify?url=https://tiss.tuwien.ac.at/events/rest/calendar/personal?locale=en&token=justATestingTokenObviouslyNotReal"
    )
    assert response.status_code == 200


def test_icalendar_de_success(client: FlaskClient, mocker):
    testcal = get_test_calendar(lang="de")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=de&token=justATestingTokenObviouslyNotReal"
    )
    assert response.status_code == 200

    cal = Calendar.from_ical(response.data)
    summaries = calendar_summaries(cal)
    descriptions = calendar_descriptions(cal)

    # Number of events
    assert calendar_event_cnt(testcal) == calendar_event_cnt(cal)

    # Shorthands
    assert "PS VU" in summaries
    assert "SEPS SE" in summaries

    # Correct Language
    assert any(["Programmiersprachen" in d for d in descriptions])
    assert not any(["Programming Languages" in d for d in descriptions])
    assert all(["Raum:" in d for d in descriptions])
    assert not any(["Room:" in d for d in descriptions])
    assert any(["Stock:" in d for d in descriptions])
    assert not any(["Floor:" in d for d in descriptions])

    # No HTML
    assert not any(["<b>" in d for d in descriptions])

    # No left template strings
    assert not any(
        [
            re.fullmatch(".*\\{.*\\}.*", d) is not None in d
            for d in calendar_descriptions(cal)
        ]
    )


def test_icalendar_en_success(client: FlaskClient, mocker):
    testcal = get_test_calendar(lang="en")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=en&token=justATestingTokenObviouslyNotReal"
    )
    assert response.status_code == 200

    cal = Calendar.from_ical(response.data)
    summaries = calendar_summaries(cal)
    descriptions = calendar_descriptions(cal)

    # Number of events
    assert calendar_event_cnt(testcal) == calendar_event_cnt(cal)

    # Shorthands
    assert "PS VU" in summaries
    assert "SEPS SE" in summaries

    # Correct language
    assert any(["Programming Languages" in d for d in descriptions])
    assert not any(["Programmiersprachen" in d for d in descriptions])
    assert any(["Room:" in d for d in descriptions])
    assert not all(["Raum:" in d for d in descriptions])
    assert any(["Floor:" in d for d in descriptions])
    assert not any(["Stock:" in d for d in descriptions])

    # No HTML
    assert not any(["<b>" in d for d in descriptions])

    # No left template strings
    assert not any(
        [
            re.fullmatch(".*\\{.*\\}.*", d) is not None in d
            for d in calendar_descriptions(cal)
        ]
    )


def test_icalendar_forgoogle_de_success(client: FlaskClient, mocker):
    testcal = get_test_calendar(lang="de")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=de&token=justATestingTokenObviouslyNotReal&google"
    )
    assert response.status_code == 200

    cal = Calendar.from_ical(response.data)
    summaries = calendar_summaries(cal)
    descriptions = calendar_descriptions(cal)

    # Number of events
    assert calendar_event_cnt(testcal) == calendar_event_cnt(cal)

    # Shorthands
    assert "PS VU" in summaries
    assert "SEPS SE" in summaries

    # Correct Language
    assert any(["Programmiersprachen" in d for d in descriptions])
    assert not any(["Programming Languages" in d for d in descriptions])
    assert all(["Raum:" in d for d in descriptions])
    assert not any(["Room:" in d for d in descriptions])
    assert any(["Stock:" in d for d in descriptions])
    assert not any(["Floor:" in d for d in descriptions])

    # HTML in description
    assert any(["<b>" in d for d in descriptions])

    # No left template strings
    assert not any(
        [
            re.fullmatch(".*\\{.*\\}.*", d) is not None in d
            for d in calendar_descriptions(cal)
        ]
    )


def test_icalendar_forgoogle_en_success(client: FlaskClient, mocker):
    testcal = get_test_calendar(lang="en")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=en&token=justATestingTokenObviouslyNotReal&google"
    )
    assert response.status_code == 200

    cal = Calendar.from_ical(response.data)
    summaries = calendar_summaries(cal)
    descriptions = calendar_descriptions(cal)

    # Number of events
    assert calendar_event_cnt(testcal) == calendar_event_cnt(cal)

    # Shorthands
    assert "PS VU" in summaries
    assert "SEPS SE" in summaries

    # Correct language
    assert any(["Programming Languages" in d for d in descriptions])
    assert not any(["Programmiersprachen" in d for d in descriptions])
    assert any(["Room:" in d for d in descriptions])
    assert not all(["Raum:" in d for d in descriptions])
    assert any(["Floor:" in d for d in descriptions])
    assert not any(["Stock:" in d for d in descriptions])

    # HTML in description
    assert any(["<b>" in d for d in descriptions])

    # No left template strings
    assert not any(
        [
            re.fullmatch(".*\\{.*\\}.*", d) is not None in d
            for d in calendar_descriptions(cal)
        ]
    )


def test_icalendar_noshorthands_de_success(client: FlaskClient, mocker):
    testcal = get_test_calendar(lang="de")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=de&token=justATestingTokenObviouslyNotReal&noshorthand"
    )
    assert response.status_code == 200

    cal = Calendar.from_ical(response.data)
    summaries = calendar_summaries(cal)
    descriptions = calendar_descriptions(cal)

    # Number of events
    assert calendar_event_cnt(testcal) == calendar_event_cnt(cal)

    # No shorthands
    assert "PS VU" not in summaries
    assert "SEPS SE" not in summaries

    # No full lecture name in description if already in title
    assert not any(["Programmiersprachen" in d for d in descriptions])
    assert not any(["Programming Languages" in d for d in descriptions])

    # Correct language
    assert all(["Raum:" in d for d in descriptions])
    assert not any(["Room:" in d for d in descriptions])
    assert any(["Stock:" in d for d in descriptions])
    assert not any(["Floor:" in d for d in descriptions])

    # No HTML
    assert not any(["<b>" in d for d in descriptions])

    # No left template strings
    assert not any(
        [
            re.fullmatch(".*\\{.*\\}.*", d) is not None in d
            for d in calendar_descriptions(cal)
        ]
    )
