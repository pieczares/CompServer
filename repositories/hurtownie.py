from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Hurtownia


class HurtowniaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_links(self) -> list[tuple[int, str]]:
        stmt = select(Hurtownia.hurtownia_id, Hurtownia.link).order_by(Hurtownia.hurtownia_id)
        return [(i, l) for i, l in self._session.execute(stmt)]
