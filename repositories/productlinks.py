from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.models import ProductLink


class ProductLinkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def replace(self, hurtownia_id: int, links: list[str]) -> int:
        self._session.execute(
            delete(ProductLink).where(ProductLink.hurtownia_id == hurtownia_id))
        self._session.add_all(
            [ProductLink(hurtownia_id=hurtownia_id, link=l) for l in links])
        return len(links)

    def get_grouped_by_hurtownia(self) -> dict[int, list[str]]:
        stmt = select(ProductLink.hurtownia_id, ProductLink.link).order_by(
            ProductLink.hurtownia_id, ProductLink.id)
        grouped: dict[int, list[str]] = {}
        for hid, link in self._session.execute(stmt):
            grouped.setdefault(hid, []).append(link)
        return grouped
