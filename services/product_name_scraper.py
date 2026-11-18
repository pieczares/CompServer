from bs4 import BeautifulSoup

from core.http_session_provider import HttpSessionProvider
from domain.product_name import ProductName
from domain.scrape_error import ScrapeError
from services.parallel_page_fetcher import ParallelPageFetcher
from services.product_page_parser import ProductPageParser


class ProductNameScraper:
    """Czyta ze stron produktów nazwę (h1) oraz kod producenta."""

    def __init__(self, threads: int = 5, page_parser: ProductPageParser | None = None) -> None:
        self._fetcher: ParallelPageFetcher[ProductName] = ParallelPageFetcher(threads)
        self._page = page_parser or ProductPageParser()

    def _scrape_one(self, http: HttpSessionProvider, url: str) -> ProductName:
        response = http.get().get(url, timeout=http.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        name = self._page.extract_name(soup)
        code = self._page.extract_code(self._page.page_text(soup))
        return ProductName(kod=code, nazwa=name, url=response.url)

    def scrape(self, links: list[str]) -> tuple[list[ProductName], list[ScrapeError]]:
        return self._fetcher.run(links, self._scrape_one)
