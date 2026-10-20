from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ProduktResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hurtownia_id: int
    kod: str
    brutto: Decimal
    netto: Decimal
    jednostka: Literal["kg", "szt"]