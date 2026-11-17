from typing import Iterator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.session import SessionLocal
from repositories.produkty import ProduktRepository
from schemas.produkty import OfertaResponse, ProduktResponse, CountResponse


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def get_repository(session: Session = Depends(get_session)) -> ProduktRepository:
    return ProduktRepository(session)


class ProduktyController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/produkty", tags=["Produkty"])
        self.router.add_api_route("/oferta", self.get_oferty, methods=["GET"],
                                  response_model=list[OfertaResponse],
                                  summary="Pobierz oferty produktów")
        self.router.add_api_route("", self.get_produkty, methods=["GET"],
                                  response_model=list[ProduktResponse],
                                  summary="Pobierz nazwy produktów")
        self.router.add_api_route("/count", self.get_count, methods=["GET"],
                                  response_model=CountResponse,
                                  summary="Pobierz liczbę produktów")

    def get_oferty(
        self,
        hurtownia_id: int | None = Query(None, ge=1, description="Opcjonalny identyfikator hurtowni"),
        kod: str | None = Query(None, min_length=1, max_length=13, description="Dokładny kod produktu"),
        repo: ProduktRepository = Depends(get_repository),
    ) -> list[OfertaResponse]:
        return [OfertaResponse.model_validate(o)
                for o in repo.get_oferty(hurtownia_id=hurtownia_id, kod=kod)]

    def get_produkty(
        self,
        kod: str | None = Query(None, min_length=1, max_length=13, description="Dokładny kod produktu"),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        repo: ProduktRepository = Depends(get_repository),
    ) -> list[ProduktResponse]:
        return [ProduktResponse.model_validate(p)
                for p in repo.get_nazwy(kod=kod, limit=limit, offset=offset)]

    def get_count(self, repo: ProduktRepository = Depends(get_repository)) -> CountResponse:
        return CountResponse.model_validate({"count": repo.count_nazwy()})
