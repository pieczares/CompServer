from fastapi import APIRouter, Query

from db.session import SessionLocal
from repositories.produkty import get_products_from_db
from schemas.produkty import ProduktResponse


router = APIRouter(
    prefix="/produkty",
    tags=["Produkty"],
)


@router.get(
    "",
    response_model=list[ProduktResponse],
    summary="Pobierz listę produktów",
)
def get_produkty(
    hurtownia_id: int | None = Query(
        default=None,
        ge=1,
        description="Opcjonalny identyfikator hurtowni",
    ),
    kod: str | None = Query(
        default=None,
        min_length=1,
        max_length=13,
        description="Dokładny kod produktu",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maksymalna liczba zwracanych produktów",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Liczba pomijanych produktów",
    ),
) -> list[ProduktResponse]:
    with SessionLocal() as session:
        produkty = get_products_from_db(
            session=session,
            hurtownia_id=hurtownia_id,
            kod=kod,
            limit=limit,
            offset=offset,
        )

        return [
            ProduktResponse.model_validate(produkt)
            for produkt in produkty
        ]