from decimal import Decimal

from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

from db.models import Produkt, Hurtownia, Nazwy_produktow
from services.product_scraper import ScrapedProduct


class ProduktRepository:
    MAX_CODE_LEN = 13
    MAX_PRICE = Decimal("99999999.99")
    UNITS = ("kg", "szt")

    def __init__(self, session: Session) -> None:
        self._session = session

    def _validate(self, data: ScrapedProduct) -> str:
        kod = (data.kod_producenta or "").strip()
        if not kod:
            raise ValueError("Brak kodu producenta")
        if len(kod) > self.MAX_CODE_LEN:
            raise ValueError(f"Kod produktu przekracza limit {self.MAX_CODE_LEN} znaków: {kod}")
        for name, value in (("netto", data.cena_netto), ("brutto", data.cena_brutto)):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"Niepoprawna cena {name}: {value!r}")
            if value < 0 or value > self.MAX_PRICE:
                raise ValueError(f"Cena {name} poza zakresem DECIMAL(10,2)")
        if data.jednostka not in self.UNITS:
            raise ValueError(f"Niepoprawna jednostka produktu: {data.jednostka!r}")
        return kod

    def save(self, hurtownia_id: int, data: ScrapedProduct) -> str:
        kod = self._validate(data)
        stmt = select(Produkt).where(Produkt.hurtownia_id == hurtownia_id,
                                     Produkt.kod == kod)
        produkt = self._session.scalars(stmt).one_or_none()

        if produkt is None:
            self._session.add(Produkt(
                hurtownia_id=hurtownia_id, kod=kod, netto=data.cena_netto,
                brutto=data.cena_brutto, jednostka=data.jednostka))
            return "inserted"

        produkt.netto = data.cena_netto
        produkt.brutto = data.cena_brutto
        produkt.jednostka = data.jednostka
        return "updated"

    def get_oferty(self, *, hurtownia_id: int | None = None,
                   kod: str | None = None) -> list[dict]:
        stmt = (select(Hurtownia.nazwa.label("hurtownia"),
                       Produkt.netto.label("cena_netto"),
                       Produkt.brutto.label("cena_brutto"),
                       Produkt.jednostka.label("jednostka"))
                .select_from(Produkt)
                .join(Hurtownia, Produkt.hurtownia_id == Hurtownia.hurtownia_id))
        if hurtownia_id is not None:
            stmt = stmt.where(Produkt.hurtownia_id == hurtownia_id)
        if kod is not None:
            stmt = stmt.where(Produkt.kod == kod)
        stmt = stmt.order_by(Produkt.produkt_id)
        return [dict(r) for r in self._session.execute(stmt).mappings().all()]

    def get_nazwy(self, *, kod: str | None = None,
                  limit: int = 100, offset: int = 0) -> list[dict]:
        stmt = select(Nazwy_produktow.kod.label("kod"),
                      Nazwy_produktow.nazwa.label("nazwa"))
        if kod is not None:
            stmt = stmt.where(Nazwy_produktow.kod == kod)
        stmt = stmt.order_by(Nazwy_produktow.kod).offset(offset).limit(limit)
        return [dict(r) for r in self._session.execute(stmt).mappings().all()]

    def count_nazwy(self) -> int:
        stmt = select(func.count(distinct(Nazwy_produktow.kod)))
        return self._session.execute(stmt).scalar_one()
