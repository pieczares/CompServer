import logging

from sqlalchemy.orm import sessionmaker

from repositories.hurtownie import HurtowniaRepository
from repositories.productlinks import ProductLinkRepository
from services.product_link_service import ProductLinkService

logger = logging.getLogger(__name__)


class RefreshProductLinksTask:
    def __init__(self, session_factory: sessionmaker,
                 link_service: ProductLinkService) -> None:
        self._sf = session_factory
        self._links = link_service

    def __call__(self) -> None:
        logger.info("Rozpoczęto odświeżanie linków produktów")

        with self._sf() as session:
            hurtownie = HurtowniaRepository(session).get_links()

        ok = errors = total = 0
        for hid, url in hurtownie:
            try:
                if not url or not url.strip():
                    raise ValueError("Hurtownia nie ma adresu strony")
                logger.info("Pobieranie linków: hurtownia_id=%s, url=%s", hid, url)
                links = self._links.fetch(url.strip())

                with self._sf.begin() as session:
                    saved = ProductLinkRepository(session).replace(hid, links)
                ok += 1
                total += saved
                logger.info("Zaktualizowano hurtownię id=%s: %s linków", hid, saved)
            except Exception:
                errors += 1
                logger.exception("Nie udało się odświeżyć linków hurtowni id=%s; "
                                 "poprzednie linki nie zostały zastąpione", hid)

        logger.info("Zakończono odświeżanie. Poprawnie: %s, błędy: %s, zapisane linki: %s",
                    ok, errors, total)
