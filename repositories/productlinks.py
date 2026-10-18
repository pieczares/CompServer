from sqlalchemy import delete
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