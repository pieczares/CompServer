from bs4 import BeautifulSoup

from core.http_session_provider import HttpSessionProvider
from domain.scrape_error import ScrapeError
from domain.scraped_product import ScrapedProduct
from services.parallel_page_fetcher import ParallelPageFetcher
from services.price_parser import PriceParser
from services.product_page_parser import ProductPageParser


class ProductScraper:
    def __init__(self, threads: int = 5, price_parser: PriceParser | None = None,
                 page_parser: ProductPageParser | None = None) -> None:
        self._fetcher: ParallelPageFetcher[ScrapedProduct] = ParallelPageFetcher(threads)
        self._prices = price_parser or PriceParser()
        self._page = page_parser or ProductPageParser()

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

        self._page.ensure_product_card(soup)
        text = self._page.page_text(soup)
        code = self._page.extract_code(text)
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
        return self._fetcher.run(links, self._scrape_one)
