from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Produkt, Hurtownia, Nazwy_produktow


def save_product(
    session: Session,
    hurtownia_id: int,
    data: dict,
) -> str:
    raw_kod = data.get("kod_producenta")

    if not isinstance(raw_kod, str) or not raw_kod.strip():
        raise ValueError("Brak kodu producenta")

    kod = raw_kod.strip()

    if len(kod) > 13:
        raise ValueError(
            f"Kod produktu przekracza limit 13 znaków: {kod}"
        )

    netto = data.get("cena_netto")
    brutto = data.get("cena_brutto")
    jednostka = data.get("jednostka")

    for field_name, value in (
        ("netto", netto),
        ("brutto", brutto),
    ):
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError(f"Niepoprawna cena {field_name}: {value!r}")

        if value < 0 or value > Decimal("99999999.99"):
            raise ValueError(
                f"Cena {field_name} poza zakresem DECIMAL(10,2)"
            )

    if jednostka not in ("kg", "szt"):
        raise ValueError(
            f"Niepoprawna jednostka produktu: {jednostka!r}"
        )

    statement = select(Produkt).where(
        Produkt.hurtownia_id == hurtownia_id,
        Produkt.kod == kod,
    )

    # Jeżeli w bazie istnieją duplikaty tej pary,
    # zgłoszony zostanie błąd zamiast aktualizacji losowego rekordu.
    produkt = session.scalars(statement).one_or_none()

    if produkt is None:
        produkt = Produkt(
            hurtownia_id=hurtownia_id,
            kod=kod,
            netto=netto,
            brutto=brutto,
            jednostka=jednostka,
        )

        session.add(produkt)
        return "inserted"

    produkt.netto = netto
    produkt.brutto = brutto
    produkt.jednostka = jednostka

    return "updated"


def get_oferty_from_db(
    session: Session,
    *,
    hurtownia_id: int | None = None,
    kod: str | None = None,
) -> list[dict]:
    statement = (
        select(
            Hurtownia.nazwa.label("hurtownia"),
            Produkt.netto.label("cena_netto"),
            Produkt.brutto.label("cena_brutto"),
            Produkt.jednostka.label("jednostka"),
        )
        .select_from(Produkt)
        .join(
            Hurtownia,
            Produkt.hurtownia_id == Hurtownia.hurtownia_id,
        )
    )

    if hurtownia_id is not None:
        statement = statement.where(
            Produkt.hurtownia_id == hurtownia_id
        )

    if kod is not None:
        statement = statement.where(
            Produkt.kod == kod
        )

    statement = (
        statement
        .order_by(Produkt.produkt_id)
    )

    rows = session.execute(statement).mappings().all()

    return [dict(row) for row in rows]


def get_produkty_from_db(
    session: Session,
    *,
    kod: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    statement = (
        select(
            Nazwy_produktow.kod.label("kod"),
            Nazwy_produktow.nazwa.label("nazwa"),
        )
        .select_from(Nazwy_produktow)
    )

    if kod is not None:
        statement = statement.where(
            Nazwy_produktow.kod == kod
        )

    statement = (
        statement
        .order_by(Nazwy_produktow.kod)
        .offset(offset)
        .limit(limit)
    )

    rows = session.execute(statement).mappings().all()

    return [dict(row) for row in rows]