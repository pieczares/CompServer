from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class ScrapedProduct:
    kod_producenta: str
    cena_netto: Decimal | None
    cena_brutto: Decimal | None
    jednostka: str | None
    url: str
    uwagi: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScrapeError:
    url: str
    blad: str
