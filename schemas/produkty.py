from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class OfertaResponse(BaseModel):
    hurtownia: str
    cena_netto: Decimal
    cena_brutto: Decimal
    jednostka: Literal["szt", "kg"]

class ProduktResponse(BaseModel):
    kod: str
    nazwa: str