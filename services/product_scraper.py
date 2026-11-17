import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from decimal import Decimal

from bs4 import BeautifulSoup

from core.http import HttpSessionProvider


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
    def _norm_unit(unit: str | None) -> str | None:
        return unit.lower().rstrip(".") if unit else None

    def parse(self, text: str) -> tuple[Decimal | None, Decimal | None, str | None]:
        m = self._PATTERN.search(text)
        if m is None:
            return None, None, None
        ub = self._norm_unit(m.group("ub"))
        un = self._norm_unit(m.group("un"))
        if ub and un and ub != un:
            raise ValueError("Różne jednostki przy cenie brutto i netto.")
        return (self._to_decimal(m.group("netto")),
                self._to_decimal(m.group("brutto")),
                ub or un)


class ProductScraper:
    _CODE = re.compile(r"Kod\s+producenta\s*:\s*(?P<kod>[^\s]+)", re.IGNORECASE)

    def __init__(self, threads: int = 5,
                 price_parser: PriceParser | None = None) -> None:
        if threads < 1:
            raise ValueError("Liczba wątków musi być dodatnia.")
        self._threads = threads
        self._prices = price_parser or PriceParser()

    @staticmethod
    def _page_text(soup: BeautifulSoup) -> str:
        for el in soup(["script", "style", "noscript"]):
            el.decompose()
        text = soup.get_text(" ", strip=True)
        text = text.replace("\xa0", " ").replace("\u202f", " ")
        return re.sub(r"\s+", " ", text)

    def _scrape_one(self, http: HttpSessionProvider, url: str) -> ScrapedProduct:
        response = http.get().get(url, timeout=http.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        if soup.find("h1") is None:
            raise ValueError("Brak nagłówka h1 — nie rozpoznano karty produktu.")

        text = self._page_text(soup)
        code = self._CODE.search(text)
        if code is None:
            raise ValueError("Brak pola „Kod producenta” — nie rozpoznano "
                             "oczekiwanego układu karty.")

        netto, brutto, unit = self._prices.parse(text)
        notes: list[str] = []
        if netto is None or brutto is None:
            notes.append("Nie znaleziono pary cen: brutto i następującej "
                         "bezpośrednio po niej netto.")
        if unit is None:
            notes.append("Nie ustalono jednostki sprzedaży: szt lub kg.")

        return ScrapedProduct(code.group("kod"), netto, brutto, unit,
                              response.url, notes)

    def scrape(self, links: list[str]) -> tuple[list[ScrapedProduct], list[ScrapeError]]:
        links = list(dict.fromkeys(links))
        results: dict[int, ScrapedProduct] = {}
        errors: dict[int, ScrapeError] = {}

        with HttpSessionProvider() as http, \
                ThreadPoolExecutor(max_workers=self._threads) as executor:
            futures = {executor.submit(self._scrape_one, http, url): (i, url)
                       for i, url in enumerate(links)}
            for future in as_completed(futures):
                i, url = futures[future]
                try:
                    results[i] = future.result()
                except Exception as err:
                    errors[i] = ScrapeError(url, f"{type(err).__name__}: {err}")

        return ([results[i] for i in sorted(results)],
                [errors[i] for i in sorted(errors)])
