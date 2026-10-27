from fastapi import APIRouter, Query

from db.session import SessionLocal
from repositories.produkty import get_oferty_from_db, get_produkty_from_db
from schemas.produkty import OfertaResponse, ProduktResponse

router = APIRouter(
    prefix="/produkty",
    tags=["Produkty"],
)


@router.get(
    "/oferta",
    response_model=list[OfertaResponse],
    summary="Pobierz oferty produktów",
)
def get_oferty(
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
) -> list[OfertaResponse]:
    with SessionLocal() as session:
        oferty = get_oferty_from_db(
            session=session,
            hurtownia_id=hurtownia_id,
            kod=kod,
        )

        return [
            OfertaResponse.model_validate(oferta)
            for oferta in oferty
        ]


@router.get(
    "",
    response_model=list[ProduktResponse],
    summary="Pobierz nazwy produktów",
)
def get_produkty(
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
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> list[ProduktResponse]:
    with SessionLocal() as session:
        produkty = get_produkty_from_db(
            session=session,
            kod=kod,
            limit=limit,
            offset=offset,
        )

        return [
            ProduktResponse.model_validate(produkt)
            for produkt in produkty
        ]