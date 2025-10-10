from flask.testing import FlaskClient
from icalendar import Calendar, Component


def get_test_calendar(lang: str = "de"):
    # FIXME: we need better examples, at the moment they only have 5 events and
    # we could even merge multiple into one.
    with open(f"tests/calendar_{lang}.ics") as f:
        cal = Calendar.from_ical(f.read())
    return cal


def calendar_event_cnt(cal: Component) -> int:
    return sum([1 for c in cal.walk() if c.name == "VEVENT"])


def calendar_summaries(cal: Component) -> list[str]:
    return [c.get("summary") for c in cal.walk() if c.name == "VEVENT"]


def calendar_descriptions(cal: Component) -> list[str]:
    descriptions = [c.get("description") for c in cal.walk() if c.name == "VEVENT"]
    return [d for d in descriptions if d is not None]


def test_home_page(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Original calendar url" in response.data


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
        "/verify?url=https://tiss.tuwien.ac.at/events/rest/calendar/personal?locale=de%26token=justATestingTokenObviouslyNotReal"
    )
    assert response.status_code == 200


def test_icalendar_de_success(client: FlaskClient, mocker, snapshot_ical):
    testcal = get_test_calendar(lang="de")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=de&token=justATestingTokenObviouslyNotReal"
    )
    assert response.status_code == 200

    # Make sure the thing returned is still parseable
    Calendar.from_ical(response.data)

    assert snapshot_ical == response.text


def test_icalendar_en_success(client: FlaskClient, mocker, snapshot_ical):
    testcal = get_test_calendar(lang="en")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=en&token=justATestingTokenObviouslyNotReal"
    )
    assert response.status_code == 200

    # Make sure the thing returned is still parseable
    Calendar.from_ical(response.data)

    assert snapshot_ical == response.text


def test_icalendar_forgoogle_de_success(client: FlaskClient, mocker, snapshot_ical):
    testcal = get_test_calendar(lang="de")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=de&token=justATestingTokenObviouslyNotReal&google"
    )
    assert response.status_code == 200

    # Make sure the thing returned is still parseable
    Calendar.from_ical(response.data)

    assert snapshot_ical == response.text


def test_icalendar_forgoogle_en_success(client: FlaskClient, mocker, snapshot_ical):
    testcal = get_test_calendar(lang="en")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=en&token=justATestingTokenObviouslyNotReal&google"
    )
    assert response.status_code == 200

    # Make sure the thing returned is still parseable
    Calendar.from_ical(response.data)

    assert snapshot_ical == response.text


def test_icalendar_noshorthands_de_success(client: FlaskClient, mocker, snapshot_ical):
    testcal = get_test_calendar(lang="de")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=de&token=justATestingTokenObviouslyNotReal&noshorthand"
    )
    assert response.status_code == 200

    # Make sure the thing returned is still parseable
    Calendar.from_ical(response.data)

    assert snapshot_ical == response.text


def test_icalendar_noshorthands_en_success(client: FlaskClient, mocker, snapshot_ical):
    testcal = get_test_calendar(lang="en")
    mocker.patch("app.tiss.get_calendar", return_value=testcal)

    response = client.get(
        "/personal.ics?locale=en&token=justATestingTokenObviouslyNotReal&noshorthand"
    )
    assert response.status_code == 200

    # Make sure the thing returned is still parseable
    Calendar.from_ical(response.data)

    assert snapshot_ical == response.text
