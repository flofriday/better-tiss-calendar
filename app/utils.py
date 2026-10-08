from logging import getLogger

from icalendar import Event as IcalEvent

from app.constants import KEY_WORDS, SessionType

logger = getLogger(__name__)


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


def merge_group(group: list[IcalEvent]) -> IcalEvent:
    if len(group) == 1:
        return group[0]

    original: IcalEvent | None = None
    main_components = []
    extra_components = []
    try:
        missing_location = sum(1 for c in group if c.get("LOCATION") is None)
        if missing_location:
            raise ValueError(
                f"{missing_location} of {len(group)} events have no LOCATION"
            )

        for component in group:
            if any(word in component.get("DESCRIPTION", "") for word in KEY_WORDS):
                extra_components.append(component)
            else:
                main_components.append(component)

        sorted_main_components = sorted(
            main_components, key=lambda c: c.get("LOCATION", "")
        )
        sorted_fallback = sorted(extra_components, key=lambda c: c.get("LOCATION", ""))
        original = (
            sorted_main_components[0]
            if len(sorted_main_components) > 0
            else sorted_fallback[0]
        )

        assert type(original) is IcalEvent
        extra_locations = []

        for component in group:
            if component is not original:
                extra_locations.append(component.get("LOCATION"))

        updated_component = original.copy()
        updated_component.add("X-EXTRA-ROOMS", ",".join(sorted(extra_locations)))

        return updated_component

    except Exception as e:
        data_to_log = []
        for component in group:
            data_to_log.append(component.to_json())

        logger.error(
            f"Could not merge {len(group)} events with the same name and start, "
            f"using the first one instead. Reason: {type(e).__name__}: {e}. "
            f"Data: {data_to_log}"
        )
        return group[0]
