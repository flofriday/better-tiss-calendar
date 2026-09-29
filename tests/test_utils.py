from app.constants import SessionType
from app.utils import parse_session_type


def test_parse_session_type_vorlesung_de():
    assert parse_session_type("Vorlesung", None) == SessionType.VORLESUNG


def test_parse_session_type_lecture_en():
    assert parse_session_type("Lecture", None) == SessionType.VORLESUNG


def test_parse_session_type_lecture_with_alternative_rooms():
    assert (
        parse_session_type("Lecture (Alternative premises)", None)
        == SessionType.VORLESUNG
    )


def test_parse_session_type_vorbesprechung():
    assert parse_session_type("Vorbesprechung", None) == SessionType.VORBESPRECHUNG


def test_parse_session_type_testeinsicht():
    assert (
        parse_session_type("Testeinsicht Test 2 10:00-11:00", None)
        == SessionType.TESTEINSICHT
    )


def test_parse_session_type_exam():
    assert parse_session_type("Prüfung", None) == SessionType.EXAM


def test_parse_session_type_group_by_category():
    assert parse_session_type("some group description", ["GROUP"]) == (
        SessionType.GROUP
    )


def test_parse_session_type_group_takes_priority_over_description():
    # Even if the description happens to say "Vorlesung", a GROUP category
    # should win, since it is the more reliable signal
    assert parse_session_type("Vorlesung", ["GROUP"]) == SessionType.GROUP


def test_parse_session_type_no_categories_falls_back_to_description():
    assert parse_session_type("Vorlesung", []) == SessionType.VORLESUNG


def test_parse_session_type_unrecognized_description():
    assert (
        parse_session_type("Orientierung: 1. Block - Röpke", None) == SessionType.OTHER
    )


def test_parse_session_type_none_description():
    assert parse_session_type(None, None) == SessionType.OTHER
