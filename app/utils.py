from app.constants import SessionType


def parse_session_type(
    description: str | None, categories: list[str] | str | None = None
) -> SessionType:
    if categories:
        cats = [categories] if isinstance(categories, str) else categories
        if "GROUP" in cats:
            return SessionType.GROUP

    desc_lower = description.lower() if description else ""

    if "vorlesung" in desc_lower or "lecture" in desc_lower:
        return SessionType.VORLESUNG

    if "vorbesprechung" in desc_lower:
        return SessionType.VORBESPRECHUNG

    if "testeinsicht" in desc_lower:
        return SessionType.TESTEINSICHT

    if "prüfung" in desc_lower or "test" in desc_lower:
        return SessionType.EXAM

    return SessionType.OTHER
