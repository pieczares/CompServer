from contextlib import contextmanager
from typing import Iterator

from fastapi import HTTPException, Query
from sqlalchemy.orm import sessionmaker

from api.controller import Controller
from repositories.produkt_repository import ProduktRepository
from schemas.produkty import CountResponse, OfertaResponse, ProduktResponse


class ProduktyController(Controller):
    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__(prefix="/produkty", tags=["Produkty"])
        self._session_factory = session_factory

        self.router.add_api_route(
            "/oferta", self.get_oferty, methods=["GET"],
            response_model=list[OfertaResponse],
            summary="Pobierz oferty produktów")
        self.router.add_api_route(
            "/cena", self.get_cena, methods=["GET"],
            response_model=OfertaResponse,
            responses={404: {"description": "Brak produktu w podanej hurtowni"}},
            summary="Pobierz cenę produktu w hurtowni (nazwa hurtowni + kod)")
        self.router.add_api_route(
            "", self.get_produkty, methods=["GET"],
            response_model=list[ProduktResponse],
            summary="Pobierz nazwy produktów")
        self.router.add_api_route(
            "/count", self.get_count, methods=["GET"],
            response_model=CountResponse,
            summary="Pobierz liczbę produktów")

    @contextmanager
    def _repository(self) -> Iterator[ProduktRepository]:
        with self._session_factory() as session:
            yield ProduktRepository(session)

    def get_oferty(
        self,
        hurtownia_id: int | None = Query(
            None, ge=1, description="Opcjonalny identyfikator hurtowni"),
        kod: str | None = Query(
            None, min_length=1, max_length=13, description="Dokładny kod produktu"),
    ) -> list[OfertaResponse]:
        with self._repository() as repo:
            return [OfertaResponse.model_validate(o)
                    for o in repo.get_oferty(hurtownia_id=hurtownia_id, kod=kod)]

    def get_cena(
        self,
        hurtownia: str = Query(
            ..., min_length=1, description="Nazwa hurtowni (wielkość liter bez znaczenia)"),
        kod: str = Query(
            ..., min_length=1, max_length=13, description="Dokładny kod produktu"),
    ) -> OfertaResponse:
        with self._repository() as repo:
            oferta = repo.get_oferta_by_hurtownia_nazwa(hurtownia, kod)
        if oferta is None:
            raise HTTPException(
                status_code=404,
                detail="Nie znaleziono produktu o podanym kodzie w tej hurtowni")
        return OfertaResponse.model_validate(oferta)

    def get_produkty(
        self,
        kod: str | None = Query(
            None, min_length=1, max_length=13, description="Dokładny kod produktu"),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[ProduktResponse]:
        with self._repository() as repo:
            return [ProduktResponse.model_validate(p)
                    for p in repo.get_nazwy(kod=kod, limit=limit, offset=offset)]

    def get_count(self) -> CountResponse:
        with self._repository() as repo:
            return CountResponse.model_validate({"count": repo.count_nazwy()})
