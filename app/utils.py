from icalendar import Event as IcalEvent

KEY_WORDS = ["Ausweich", "Alternative"]


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

    except Exception:
        return group[0]
