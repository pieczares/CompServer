import re

from bs4 import BeautifulSoup


class ProductPageParser:
    """Wspólne operacje na karcie produktu: nagłówek, tekst strony, kod producenta."""

    _CODE = re.compile(r"Kod\s+producenta\s*:\s*(?P<kod>[^\s]+)", re.IGNORECASE)

    def ensure_product_card(self, soup: BeautifulSoup) -> None:
        if soup.find("h1") is None:
            raise ValueError("Brak nagłówka h1 — nie rozpoznano karty produktu.")

    def extract_name(self, soup: BeautifulSoup) -> str:
        self.ensure_product_card(soup)
        name = re.sub(r"\s+", " ", soup.find("h1").get_text(" ", strip=True)).strip()
        if not name:
            raise ValueError("Pusty nagłówek h1 — brak nazwy produktu.")
        return name

    @staticmethod
    def page_text(soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        text = soup.get_text(" ", strip=True)
        text = text.replace("\xa0", " ").replace("\u202f", " ")
        return re.sub(r"\s+", " ", text)

    def extract_code(self, text: str) -> str:
        match = self._CODE.search(text)
        if match is None:
            raise ValueError(
                "Brak pola „Kod producenta” — nie rozpoznano oczekiwanego układu karty."
            )
        return match.group("kod")
