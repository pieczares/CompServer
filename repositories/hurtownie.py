from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Hurtownia


def get_hurtownie_links(
    session: Session,
) -> list[tuple[int, str]]:
    statement = (
        select(
            Hurtownia.hurtownia_id,
            Hurtownia.link,
        )
        .order_by(Hurtownia.hurtownia_id)
    )

    return [
        (hurtownia_id, link)
        for hurtownia_id, link in session.execute(statement)
    ]