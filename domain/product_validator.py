from decimal import Decimal

from domain.product_name import ProductName
from domain.scraped_product import ScrapedProduct


class ProductValidator:
    MAX_CODE_LEN = 13
    MAX_PRICE = Decimal("99999999.99")
    UNITS = ("kg", "szt")

    def validate(self, data: ScrapedProduct) -> str:
        """Zwraca oczyszczony kod produktu albo zgłasza ValueError."""
        kod = self._validate_code(data.kod_producenta)
        self._validate_price("netto", data.cena_netto)
        self._validate_price("brutto", data.cena_brutto)
        self._validate_unit(data.jednostka)
        return kod

    def validate_name(self, data: ProductName) -> ProductName:
        """Zwraca ProductName z oczyszczonym kodem i nazwą albo zgłasza ValueError."""
        kod = self._validate_code(data.kod)
        nazwa = (data.nazwa or "").strip()
        if not nazwa:
            raise ValueError(f"Pusta nazwa produktu dla kodu: {kod}")
        return ProductName(kod=kod, nazwa=nazwa, url=data.url)

    def _validate_code(self, raw: str | None) -> str:
        kod = (raw or "").strip()
        if not kod:
            raise ValueError("Brak kodu producenta")
        if len(kod) > self.MAX_CODE_LEN:
            raise ValueError(
                f"Kod produktu przekracza limit {self.MAX_CODE_LEN} znaków: {kod}"
            )
        return kod

    def _validate_price(self, name: str, value: Decimal | None) -> None:
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError(f"Niepoprawna cena {name}: {value!r}")
        if value < 0 or value > self.MAX_PRICE:
            raise ValueError(f"Cena {name} poza zakresem DECIMAL(10,2)")

    def _validate_unit(self, unit: str | None) -> None:
        if unit not in self.UNITS:
            raise ValueError(f"Niepoprawna jednostka produktu: {unit!r}")
