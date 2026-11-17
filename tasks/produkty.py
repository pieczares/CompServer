from dataclasses import dataclass

from sqlalchemy.orm import sessionmaker

from domain.scraping import ScrapedProduct, ScrapeError
from repositories.productlinks import ProductLinkRepository
from repositories.produkty import ProduktRepository
from services.product_scraper import ProductScraper
from tasks.base import Task


@dataclass
class RefreshStats:
    inserted: int = 0
    updated: int = 0
    errors: int = 0


class RefreshProductsTask(Task):
    def __init__(self, session_factory: sessionmaker, scraper: ProductScraper,
                 links_limit: int | None = 100) -> None:
        super().__init__(session_factory)
        self._scraper = scraper
        self._limit = links_limit

    def _load_links(self) -> dict[int, list[str]]:
        with self._session_factory() as session:
            return ProductLinkRepository(session).get_grouped_by_hurtownia()

    def _limit_links(self, links: list[str]) -> list[str]:
        return links if self._limit is None else links[: self._limit]

    def _log_scrape_errors(self, hurtownia_id: int, failed: list[ScrapeError],
                           stats: RefreshStats) -> None:
        for err in failed:
            stats.errors += 1
            self._log.warning(
                "Nie udało się pobrać produktu: hurtownia_id=%s, url=%s, błąd=%s",
                hurtownia_id, err.url, err.blad)

    def _log_notes(self, hurtownia_id: int, product: ScrapedProduct) -> None:
        for note in product.uwagi:
            self._log.warning("Uwaga scrapera: hurtownia_id=%s, url=%s, %s",
                              hurtownia_id, product.url, note)

    def _save_product(self, hurtownia_id: int, product: ScrapedProduct,
                      stats: RefreshStats) -> None:
        try:
            with self._session_factory.begin() as session:
                operation = ProduktRepository(session).save(hurtownia_id, product)
        except Exception:
            stats.errors += 1
            self._log.exception(
                "Nie udało się zapisać produktu: hurtownia_id=%s, kod=%s, url=%s",
                hurtownia_id, product.kod_producenta, product.url)
            return

        if operation == "inserted":
            stats.inserted += 1
        else:
            stats.updated += 1

    def _refresh_warehouse(self, hurtownia_id: int, links: list[str],
                           stats: RefreshStats) -> None:
        self._log.info("Pobieranie produktów: hurtownia_id=%s, liczba linków=%s",
                       hurtownia_id, len(links))
        try:
            products, failed = self._scraper.scrape(self._limit_links(links))
        except Exception:
            stats.errors += 1
            self._log.exception("Błąd pobierania produktów hurtowni id=%s", hurtownia_id)
            return

        self._log_scrape_errors(hurtownia_id, failed, stats)
        for product in products:
            self._log_notes(hurtownia_id, product)
            self._save_product(hurtownia_id, product, stats)

    def run(self) -> None:
        self._log.info("Rozpoczęto aktualizację danych produktów")
        stats = RefreshStats()

        for hurtownia_id, links in self._load_links().items():
            self._refresh_warehouse(hurtownia_id, links, stats)

        self._log.info(
            "Zakończono aktualizację produktów. Dodano: %s, zaktualizowano: %s, błędy: %s",
            stats.inserted, stats.updated, stats.errors)
