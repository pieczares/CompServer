from collections.abc import Iterator

from sqlalchemy.orm import sessionmaker

from domain.product_name import ProductName
from domain.product_validator import ProductValidator
from repositories.nazwa_produktu_repository import NazwaProduktuRepository
from repositories.product_link_repository import ProductLinkRepository
from services.product_name_scraper import ProductNameScraper
from tasks.refresh_stats import RefreshStats
from tasks.task import Task


class RefreshProductNamesTask(Task):
    """Przechodzi po wszystkich zapisanych linkach i zapisuje pary (kod, nazwa).

    Kod, który już istnieje (w bazie lub wcześniej w tym przebiegu), jest pomijany.
    """

    def __init__(self, session_factory: sessionmaker, scraper: ProductNameScraper,
                 batch_size: int = 200, validator: ProductValidator | None = None) -> None:
        super().__init__(session_factory)
        if batch_size < 1:
            raise ValueError("Rozmiar partii musi być dodatni.")
        self._scraper = scraper
        self._batch_size = batch_size
        self._validator = validator or ProductValidator()

    def _load_links(self) -> list[str]:
        with self._session_factory() as session:
            grouped = ProductLinkRepository(session).get_grouped_by_hurtownia()
        all_links = [link for links in grouped.values() for link in links]
        return list(dict.fromkeys(all_links))

    def _batches(self, links: list[str]) -> Iterator[list[str]]:
        for start in range(0, len(links), self._batch_size):
            yield links[start:start + self._batch_size]

    def _select_new(self, names: list[ProductName], seen_codes: set[str],
                    stats: RefreshStats) -> list[ProductName]:
        selected: list[ProductName] = []
        for raw in names:
            try:
                name = self._validator.validate_name(raw)
            except ValueError as err:
                stats.errors += 1
                self._log.warning("Pominięto nazwę: url=%s, powod=%s", raw.url, err)
                continue
            if name.kod in seen_codes:
                stats.skipped += 1
                continue
            seen_codes.add(name.kod)
            selected.append(name)
        return selected

    def _save_batch(self, names: list[ProductName], stats: RefreshStats) -> None:
        if not names:
            return
        try:
            with self._session_factory.begin() as session:
                added = NazwaProduktuRepository(session).add_missing(names)
        except Exception:
            self._log.exception("Zapis partii nieudany, zapis pojedynczo")
            self._save_individually(names, stats)
            return
        stats.inserted += added
        stats.skipped += len(names) - added

    def _save_individually(self, names: list[ProductName], stats: RefreshStats) -> None:
        for name in names:
            try:
                with self._session_factory.begin() as session:
                    added = NazwaProduktuRepository(session).add_missing([name])
            except Exception:
                stats.errors += 1
                self._log.exception("Nie udało się zapisać nazwy: kod=%s, url=%s",
                                    name.kod, name.url)
                continue
            stats.inserted += added
            stats.skipped += 1 - added

    def _log_scrape_errors(self, failed, stats: RefreshStats) -> None:
        for err in failed:
            stats.errors += 1
            self._log.warning("Nie udało się pobrać nazwy: url=%s, błąd=%s", err.url, err.blad)

    def run(self) -> None:
        links = self._load_links()
        self._log.info("Rozpoczęto zapis nazw produktów, liczba linków=%s", len(links))
        stats = RefreshStats()
        seen_codes: set[str] = set()

        for batch in self._batches(links):
            try:
                names, failed = self._scraper.scrape(batch)
            except Exception:
                stats.errors += 1
                self._log.exception("Błąd pobierania partii nazw")
                continue
            self._log_scrape_errors(failed, stats)
            self._save_batch(self._select_new(names, seen_codes, stats), stats)

        self._log.info(
            "Zakończono zapis nazw. Dodano: %s, pominięto (duplikat kodu): %s, błędy: %s",
            stats.inserted, stats.skipped, stats.errors)
