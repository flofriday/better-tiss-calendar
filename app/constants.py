from enum import StrEnum

KEY_WORDS = ["Ausweich", "Alternative"]

class SessionType(StrEnum):
    VORLESUNG = "Vorlesung"
    VORBESPRECHUNG = "Vorbesprechung"
    TESTEINSICHT = "Testeinsicht"
    GROUP = "Übung"
    EXAM = "Prüfung"
    OTHER = "Other"

    @property
    def shorthand(self) -> str:
        mapping = {
            SessionType.VORLESUNG: "VO",
            SessionType.VORBESPRECHUNG: "VB",
            SessionType.TESTEINSICHT: "TE",
            SessionType.GROUP: "ÜB",
            SessionType.EXAM: "PR",
            SessionType.OTHER: "",
        }
        return mapping[self]
