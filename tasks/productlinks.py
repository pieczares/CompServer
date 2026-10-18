import logging

from db.session import SessionLocal
from repositories.hurtownie import get_hurtownie_links
from repositories.productlinks import replace_product_links
from services.productlinks import fetch_product_links


logger = logging.getLogger(__name__)


def refresh_product_links() -> None:
    logger.info("Rozpoczęto odświeżanie linków produktów")

    # Sesja odczytu zostaje zamknięta przed pobieraniem stron.
    with SessionLocal() as session:
        hurtownie = get_hurtownie_links(session)

    success_count = 0
    error_count = 0
    total_links = 0

    for hurtownia_id, hurtownia_url in hurtownie:
        try:
            if not hurtownia_url or not hurtownia_url.strip():
                raise ValueError("Hurtownia nie ma adresu strony")

            logger.info(
                "Pobieranie linków: hurtownia_id=%s, url=%s",
                hurtownia_id,
                hurtownia_url,
            )

            # Najpierw pobieramy dane, bez otwartej transakcji bazy.
            links = fetch_product_links(hurtownia_url.strip())

            # Usunięcie starych i zapis nowych linków:
            # jedna transakcja dla danej hurtowni.
            with SessionLocal.begin() as session:
                saved_count = replace_product_links(
                    session=session,
                    hurtownia_id=hurtownia_id,
                    links=links,
                )

            success_count += 1
            total_links += saved_count

            logger.info(
                "Zaktualizowano hurtownię id=%s: %s linków",
                hurtownia_id,
                saved_count,
            )

        except Exception:
            error_count += 1

            logger.exception(
                "Nie udało się odświeżyć linków hurtowni id=%s; "
                "poprzednie linki nie zostały zastąpione",
                hurtownia_id,
            )

    logger.info(
        "Zakończono odświeżanie. "
        "Poprawnie: %s, błędy: %s, zapisane linki: %s",
        success_count,
        error_count,
        total_links,
    )