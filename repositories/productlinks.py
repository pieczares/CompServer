from sqlalchemy import (
    delete,
    select
)
from sqlalchemy.orm import Session

from db.models import ProductLink


def replace_product_links(
    session: Session,
    hurtownia_id: int,
    links: list[str],
) -> int:
    statement = delete(ProductLink).where(
        ProductLink.hurtownia_id == hurtownia_id
    )

    session.execute(statement)

    session.add_all(
        [
            ProductLink(
                hurtownia_id=hurtownia_id,
                link=link,
            )
            for link in links
        ]
    )

    return len(links)


def get_links_grouped_by_hurtownia(
    session: Session,
) -> dict[int, list[str]]:
    statement = (
        select(
            ProductLink.hurtownia_id,
            ProductLink.link,
        )
        .order_by(
            ProductLink.hurtownia_id,
            ProductLink.id,
        )
    )

    grouped: dict[int, list[str]] = {}

    for hurtownia_id, link in session.execute(statement):
        grouped.setdefault(hurtownia_id, []).append(link)

    return grouped