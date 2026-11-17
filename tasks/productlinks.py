from sqlalchemy.orm import sessionmaker

from repositories.hurtownie import HurtowniaRepository
from repositories.productlinks import ProductLinkRepository
from services.product_link_service import ProductLinkService
from tasks.base import Task


class RefreshProductLinksTask(Task):
    def __init__(self, session_factory: sessionmaker,
                 link_service: ProductLinkService) -> None:
        super().__init__(session_factory)
        self._links = link_service

    def _load_warehouses(self) -> list[tuple[int, str]]:
        with self._session_factory() as session:
            return HurtowniaRepository(session).get_links()

    def _refresh_warehouse(self, hurtownia_id: int, url: str) -> int:
        if not url or not url.strip():
            raise ValueError("Hurtownia nie ma adresu strony")

        self._log.info("Pobieranie linków: hurtownia_id=%s, url=%s", hurtownia_id, url)
        links = self._links.fetch(url.strip())

        with self._session_factory.begin() as session:
            return ProductLinkRepository(session).replace(hurtownia_id, links)

    def run(self) -> None:
        self._log.info("Rozpoczęto odświeżanie linków produktów")
        ok = errors = total = 0

        for hurtownia_id, url in self._load_warehouses():
            try:
                saved = self._refresh_warehouse(hurtownia_id, url)
            except Exception:
                errors += 1
                self._log.exception(
                    "Nie udało się odświeżyć linków hurtowni id=%s; "
                    "poprzednie linki nie zostały zastąpione", hurtownia_id)
                continue
            ok += 1
            total += saved
            self._log.info("Zaktualizowano hurtownię id=%s: %s linków", hurtownia_id, saved)

        self._log.info(
            "Zakończono odświeżanie. Poprawnie: %s, błędy: %s, zapisane linki: %s",
            ok, errors, total)
