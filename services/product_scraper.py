import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup

from core.http_session_provider import HttpSessionProvider
from domain.scrape_error import ScrapeError
from domain.scraped_product import ScrapedProduct
from services.price_parser import PriceParser


class ProductScraper:
    _CODE = re.compile(r"Kod\s+producenta\s*:\s*(?P<kod>[^\s]+)", re.IGNORECASE)

    def __init__(self, threads: int = 5, price_parser: PriceParser | None = None) -> None:
        if threads < 1:
            raise ValueError("Liczba wątków musi być dodatnia.")
        self._threads = threads
        self._prices = price_parser or PriceParser()

    @staticmethod
    def _page_text(soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        text = soup.get_text(" ", strip=True)
        text = text.replace("\xa0", " ").replace("\u202f", " ")
        return re.sub(r"\s+", " ", text)

    def _extract_code(self, text: str) -> str:
        match = self._CODE.search(text)
        if match is None:
            raise ValueError(
                "Brak pola „Kod producenta” — nie rozpoznano oczekiwanego układu karty."
            )
        return match.group("kod")

    @staticmethod
    def _build_notes(netto, brutto, unit) -> list[str]:
        notes: list[str] = []
        if netto is None or brutto is None:
            notes.append(
                "Nie znaleziono pary cen: brutto i następującej bezpośrednio po niej netto."
            )
        if unit is None:
            notes.append("Nie ustalono jednostki sprzedaży: szt lub kg.")
        return notes

    def _scrape_one(self, http: HttpSessionProvider, url: str) -> ScrapedProduct:
        response = http.get().get(url, timeout=http.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        if soup.find("h1") is None:
            raise ValueError("Brak nagłówka h1 — nie rozpoznano karty produktu.")

        text = self._page_text(soup)
        code = self._extract_code(text)
        netto, brutto, unit = self._prices.parse(text)

        return ScrapedProduct(
            kod_producenta=code,
            cena_netto=netto,
            cena_brutto=brutto,
            jednostka=unit,
            url=response.url,
            uwagi=self._build_notes(netto, brutto, unit),
        )

    def scrape(self, links: list[str]) -> tuple[list[ScrapedProduct], list[ScrapeError]]:
        links = list(dict.fromkeys(links))
        results: dict[int, ScrapedProduct] = {}
        errors: dict[int, ScrapeError] = {}

        with HttpSessionProvider() as http, \
                ThreadPoolExecutor(max_workers=self._threads) as executor:
            futures = {
                executor.submit(self._scrape_one, http, url): (index, url)
                for index, url in enumerate(links)
            }
            for future in as_completed(futures):
                index, url = futures[future]
                try:
                    results[index] = future.result()
                except Exception as err:
                    errors[index] = ScrapeError(url, f"{type(err).__name__}: {err}")

        return (
            [results[i] for i in sorted(results)],
            [errors[i] for i in sorted(errors)],
        )
