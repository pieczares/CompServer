import logging

from db.session import SessionLocal
from repositories.productlinks import get_links_grouped_by_hurtownia
from repositories.produkty import save_product
from services.get_products import get_products


logger = logging.getLogger(__name__)


def refresh_products() -> None:
    logger.info("Rozpoczęto aktualizację danych produktów")

    with SessionLocal() as session:
        grouped_links = get_links_grouped_by_hurtownia(session)

    inserted_count = 0
    updated_count = 0
    error_count = 0

    for hurtownia_id, links in grouped_links.items():
        logger.info(
            "Pobieranie produktów: hurtownia_id=%s, liczba linków=%s",
            hurtownia_id,
            len(links),
        )

        try:
            #ograniczone do testów!!!!!!!!!!!!!!!!!!!!!!
            produkty, bledy = get_products(
                linki=links[:100],
                liczba_watkow=5,
            )

        except Exception:
            error_count += 1

            logger.exception(
                "Błąd pobierania produktów hurtowni id=%s",
                hurtownia_id,
            )
            continue

        for blad in bledy:
            error_count += 1

            logger.warning(
                "Nie udało się pobrać produktu: "
                "hurtownia_id=%s, url=%s, błąd=%s",
                hurtownia_id,
                blad.get("url"),
                blad.get("blad"),
            )

        for data in produkty:
            for uwaga in data.get("uwagi", []):
                logger.warning(
                    "Uwaga scrapera: hurtownia_id=%s, url=%s, %s",
                    hurtownia_id,
                    data.get("url"),
                    uwaga,
                )

            try:
                with SessionLocal.begin() as session:
                    operation = save_product(
                        session=session,
                        hurtownia_id=hurtownia_id,
                        data=data,
                    )

                # Liczymy dopiero po pomyślnym zatwierdzeniu transakcji.
                if operation == "inserted":
                    inserted_count += 1
                else:
                    updated_count += 1

            except Exception:
                error_count += 1

                logger.exception(
                    "Nie udało się zapisać produktu: "
                    "hurtownia_id=%s, kod=%s, url=%s",
                    hurtownia_id,
                    data.get("kod_producenta"),
                    data.get("url"),
                )

    logger.info(
        "Zakończono aktualizację produktów. "
        "Dodano: %s, zaktualizowano: %s, błędy: %s",
        inserted_count,
        updated_count,
        error_count,
    )