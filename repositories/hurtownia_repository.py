from sqlalchemy import select

from db.models import Hurtownia
from repositories.base_repository import BaseRepository


class HurtowniaRepository(BaseRepository):
    def get_links(self) -> list[tuple[int, str]]:
        stmt = select(Hurtownia.hurtownia_id, Hurtownia.link).order_by(
            Hurtownia.hurtownia_id
        )
        return [(hid, link) for hid, link in self._session.execute(stmt)]
