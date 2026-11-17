from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from db.models import Hurtownia, Nazwy_produktow, Produkt
from domain.scraping import ScrapedProduct
from domain.validation import ProductValidator
from repositories.base import BaseRepository


class ProduktRepository(BaseRepository):
    def __init__(self, session: Session, validator: ProductValidator | None = None) -> None:
        super().__init__(session)
        self._validator = validator or ProductValidator()

    def save(self, hurtownia_id: int, data: ScrapedProduct) -> str:
        """Zwraca \"inserted\" albo \"updated\"."""
        kod = self._validator.validate(data)

        stmt = select(Produkt).where(
            Produkt.hurtownia_id == hurtownia_id, Produkt.kod == kod
        )
        # one_or_none: duplikaty pary (hurtownia, kod) zgłoszą błąd zamiast cichej aktualizacji.
        produkt = self._session.scalars(stmt).one_or_none()

        if produkt is None:
            self._session.add(Produkt(
                hurtownia_id=hurtownia_id,
                kod=kod,
                netto=data.cena_netto,
                brutto=data.cena_brutto,
                jednostka=data.jednostka,
            ))
            return "inserted"

        produkt.netto = data.cena_netto
        produkt.brutto = data.cena_brutto
        produkt.jednostka = data.jednostka
        return "updated"

    def get_oferty(self, *, hurtownia_id: int | None = None,
                   kod: str | None = None) -> list[dict]:
        stmt = (
            select(
                Hurtownia.nazwa.label("hurtownia"),
                Produkt.netto.label("cena_netto"),
                Produkt.brutto.label("cena_brutto"),
                Produkt.jednostka.label("jednostka"),
            )
            .select_from(Produkt)
            .join(Hurtownia, Produkt.hurtownia_id == Hurtownia.hurtownia_id)
        )
        if hurtownia_id is not None:
            stmt = stmt.where(Produkt.hurtownia_id == hurtownia_id)
        if kod is not None:
            stmt = stmt.where(Produkt.kod == kod)
        stmt = stmt.order_by(Produkt.produkt_id)
        return [dict(row) for row in self._session.execute(stmt).mappings().all()]

    def get_nazwy(self, *, kod: str | None = None,
                  limit: int = 100, offset: int = 0) -> list[dict]:
        stmt = select(
            Nazwy_produktow.kod.label("kod"),
            Nazwy_produktow.nazwa.label("nazwa"),
        )
        if kod is not None:
            stmt = stmt.where(Nazwy_produktow.kod == kod)
        stmt = stmt.order_by(Nazwy_produktow.kod).offset(offset).limit(limit)
        return [dict(row) for row in self._session.execute(stmt).mappings().all()]

    def count_nazwy(self) -> int:
        stmt = select(func.count(distinct(Nazwy_produktow.kod)))
        return self._session.execute(stmt).scalar_one()
