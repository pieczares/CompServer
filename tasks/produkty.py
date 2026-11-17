import logging

from sqlalchemy.orm import sessionmaker

from repositories.productlinks import ProductLinkRepository
from repositories.produkty import ProduktRepository
from services.product_scraper import ProductScraper

logger = logging.getLogger(__name__)


class RefreshProductsTask:
    def __init__(self, session_factory: sessionmaker, scraper: ProductScraper,
                 links_limit: int | None = 100) -> None:
        self._sf = session_factory
        self._scraper = scraper
        self._limit = links_limit

    def __call__(self) -> None:
        logger.info("Rozpoczęto aktualizację danych produktów")

        with self._sf() as session:
            grouped = ProductLinkRepository(session).get_grouped_by_hurtownia()

        inserted = updated = errors = 0
        for hid, links in grouped.items():
            logger.info("Pobieranie produktów: hurtownia_id=%s, liczba linków=%s",
                        hid, len(links))
            try:
                batch = links if self._limit is None else links[:self._limit]
                products, failed = self._scraper.scrape(batch)
            except Exception:
                errors += 1
                logger.exception("Błąd pobierania produktów hurtowni id=%s", hid)
                continue

            for err in failed:
                errors += 1
                logger.warning("Nie udało się pobrać produktu: hurtownia_id=%s, "
                               "url=%s, błąd=%s", hid, err.url, err.blad)

            for product in products:
                for note in product.uwagi:
                    logger.warning("Uwaga scrapera: hurtownia_id=%s, url=%s, %s",
                                   hid, product.url, note)
                try:
                    with self._sf.begin() as session:
                        op = ProduktRepository(session).save(hid, product)
                    if op == "inserted":
                        inserted += 1
                    else:
                        updated += 1
                except Exception:
                    errors += 1
                    logger.exception("Nie udało się zapisać produktu: "
                                     "hurtownia_id=%s, kod=%s, url=%s",
                                     hid, product.kod_producenta, product.url)

        logger.info("Zakończono aktualizację produktów. Dodano: %s, "
                    "zaktualizowano: %s, błędy: %s", inserted, updated, errors)
