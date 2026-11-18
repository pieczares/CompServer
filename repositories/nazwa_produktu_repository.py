from collections.abc import Iterable

from sqlalchemy import select

from db.models import Nazwy_produktow
from domain.product_name import ProductName
from repositories.base_repository import BaseRepository


class NazwaProduktuRepository(BaseRepository):
    def get_existing_codes(self, codes: Iterable[str]) -> set[str]:
        codes = list(codes)
        if not codes:
            return set()
        stmt = select(Nazwy_produktow.kod).where(Nazwy_produktow.kod.in_(codes))
        return set(self._session.scalars(stmt))

    def add_missing(self, names: list[ProductName]) -> int:
        """Zapisuje tylko nazwy, których kodu jeszcze nie ma w bazie. Zwraca liczbę dodanych."""
        existing = self.get_existing_codes(n.kod for n in names)
        new_names = [n for n in names if n.kod not in existing]
        self._session.add_all(
            [Nazwy_produktow(kod=n.kod, nazwa=n.nazwa) for n in new_names]
        )
        return len(new_names)
