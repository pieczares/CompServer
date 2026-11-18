from dataclasses import dataclass


@dataclass(frozen=True)
class ProductName:
    kod: str
    nazwa: str
    url: str
