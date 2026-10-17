from fastapi import APIRouter, Query

from db.session import SessionLocal
from repositories.results import get_results
from schemas.results import ResultResponse


router = APIRouter(
    prefix="/results",
    tags=["Wyniki"],
)


@router.get("", response_model=list[ResultResponse])
def list_results(
    limit: int = Query(default=100, ge=1, le=1000),
):
    with SessionLocal() as session:
        results = get_results(session, limit=limit)

        return [
            ResultResponse.model_validate(result)
            for result in results
        ]