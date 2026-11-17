import re
from decimal import Decimal


class PriceParser:
    _AMOUNT = r"\d+(?:[ ]\d{3})*[,.]\d{2}"
    _UNIT = r"(?:szt\.?|kg)"
    _PATTERN = re.compile(
        rf"\bCena\s+brutto\s*:?\s*(?P<brutto>{_AMOUNT})\s*zł"
        rf"(?:\s*/\s*(?P<ub>{_UNIT}))?\s*(?:\(\s*)?"
        rf"(?P<netto>{_AMOUNT})\s*zł(?:\s*/\s*(?P<un>{_UNIT}))?",
        re.IGNORECASE,
    )

    @staticmethod
    def _to_decimal(text: str) -> Decimal:
        return Decimal(text.replace(" ", "").replace(",", "."))

    @staticmethod
    def _normalize_unit(unit: str | None) -> str | None:
        return unit.lower().rstrip(".") if unit else None

    def parse(self, text: str) -> tuple[Decimal | None, Decimal | None, str | None]:
        """Zwraca (netto, brutto, jednostka); same None, gdy brak dopasowania."""
        match = self._PATTERN.search(text)
        if match is None:
            return None, None, None

        unit_gross = self._normalize_unit(match.group("ub"))
        unit_net = self._normalize_unit(match.group("un"))
        if unit_gross and unit_net and unit_gross != unit_net:
            raise ValueError("Różne jednostki przy cenie brutto i netto.")

        return (
            self._to_decimal(match.group("netto")),
            self._to_decimal(match.group("brutto")),
            unit_gross or unit_net,
        )
