from sqlalchemy import delete, select

from db.models import ProductLink
from repositories.base import BaseRepository


class ProductLinkRepository(BaseRepository):
    def replace(self, hurtownia_id: int, links: list[str]) -> int:
        self._session.execute(
            delete(ProductLink).where(ProductLink.hurtownia_id == hurtownia_id)
        )
        self._session.add_all(
            [ProductLink(hurtownia_id=hurtownia_id, link=link) for link in links]
        )
        return len(links)

    def get_grouped_by_hurtownia(self) -> dict[int, list[str]]:
        stmt = select(ProductLink.hurtownia_id, ProductLink.link).order_by(
            ProductLink.hurtownia_id, ProductLink.id
        )
        grouped: dict[int, list[str]] = {}
        for hid, link in self._session.execute(stmt):
            grouped.setdefault(hid, []).append(link)
        return grouped
