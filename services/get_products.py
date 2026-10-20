import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_products(
    linki: list[str],
    liczba_watkow: int = 5,
) -> tuple[list[dict], list[dict]]:
    """
    Pobiera dane z kart produktów.

    Zwraca:
        produkty — lista słowników z odczytanymi danymi;
        bledy — lista adresów, których nie udało się przetworzyć.

    Ceny są obiektami Decimal.
    Jednostka to "szt", "kg" albo None.
    """

    if liczba_watkow < 1:
        raise ValueError("Liczba wątków musi być dodatnia.")

    # Usuń duplikaty, zachowując kolejność.
    linki = list(dict.fromkeys(linki))

    dane_watku = threading.local()
    sesje = []
    blokada_sesji = threading.Lock()

    def pobierz_sesje() -> requests.Session:
        if not hasattr(dane_watku, "session"):
            session = requests.Session()

            retry = Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                other=0,
                allowed_methods={"GET"},
                status_forcelist=[429, 500, 502, 503, 504],
                backoff_factor=1,
                respect_retry_after_header=True,
                raise_on_status=False,
            )

            adapter = HTTPAdapter(
                max_retries=retry,
                pool_connections=1,
                pool_maxsize=1,
            )

            session.mount("https://", adapter)
            session.mount("http://", adapter)

            dane_watku.session = session

            with blokada_sesji:
                sesje.append(session)

        return dane_watku.session

    def odczytaj_ceny(
        tekst: str,
    ) -> tuple[Decimal | None, Decimal | None, str | None]:
        """
        Oczekiwany układ:
            Cena brutto: 4,05 zł / szt. 3,29 zł / szt.

        Zwraca:
            cena_netto, cena_brutto, jednostka
        """

        kwota = r"\d+(?:[ ]\d{3})*[,.]\d{2}"
        jednostka = r"(?:szt\.?|kg)"

        wzorzec = (
            rf"\bCena\s+brutto\s*:?\s*"
            rf"(?P<brutto>{kwota})\s*zł"
            rf"(?:\s*/\s*(?P<jednostka_brutto>{jednostka}))?"
            rf"\s*"
            rf"(?:\(\s*)?"
            rf"(?P<netto>{kwota})\s*zł"
            rf"(?:\s*/\s*(?P<jednostka_netto>{jednostka}))?"
        )

        wynik = re.search(
            wzorzec,
            tekst,
            flags=re.IGNORECASE,
        )

        if wynik is None:
            return None, None, None

        cena_brutto = Decimal(
            wynik.group("brutto").replace(" ", "").replace(",", ".")
        )

        cena_netto = Decimal(
            wynik.group("netto").replace(" ", "").replace(",", ".")
        )

        jednostka_brutto = wynik.group("jednostka_brutto")
        jednostka_netto = wynik.group("jednostka_netto")

        if jednostka_brutto:
            jednostka_brutto = jednostka_brutto.lower().rstrip(".")

        if jednostka_netto:
            jednostka_netto = jednostka_netto.lower().rstrip(".")

        if (
            jednostka_brutto
            and jednostka_netto
            and jednostka_brutto != jednostka_netto
        ):
            raise ValueError(
                "Różne jednostki przy cenie brutto i netto."
            )

        jednostka_sprzedazy = jednostka_brutto or jednostka_netto

        return cena_netto, cena_brutto, jednostka_sprzedazy

    def odczytaj_produkt(url: str) -> dict:
        session = pobierz_sesje()

        response = session.get(url, timeout=(10, 30))
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        naglowek = soup.find("h1")

        if naglowek is None:
            raise ValueError(
                "Brak nagłówka h1 — nie rozpoznano karty produktu."
            )

        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        tekst = soup.get_text(" ", strip=True)
        tekst = tekst.replace("\xa0", " ").replace("\u202f", " ")
        tekst = re.sub(r"\s+", " ", tekst)

        kod_match = re.search(
            r"Kod\s+producenta\s*:\s*(?P<kod>[^\s]+)",
            tekst,
            flags=re.IGNORECASE,
        )

        if kod_match is None:
            raise ValueError(
                "Brak pola „Kod producenta” — nie rozpoznano "
                "oczekiwanego układu karty."
            )

        kod = kod_match.group("kod")

        cena_netto, cena_brutto, jednostka = odczytaj_ceny(tekst)

        uwagi = []

        if cena_netto is None or cena_brutto is None:
            uwagi.append(
                "Nie znaleziono pary cen: brutto i następującej "
                "bezpośrednio po niej netto."
            )

        if jednostka is None:
            uwagi.append(
                "Nie ustalono jednostki sprzedaży: szt lub kg."
            )

        return {
            "kod_producenta": kod,
            "cena_netto": cena_netto,
            "cena_brutto": cena_brutto,
            "jednostka": jednostka,
            "url": response.url,
            "uwagi": uwagi,
        }

    wyniki = {}
    bledy = {}

    try:
        with ThreadPoolExecutor(max_workers=liczba_watkow) as executor:
            zadania = {
                executor.submit(odczytaj_produkt, url): (indeks, url)
                for indeks, url in enumerate(linki)
            }

            for zadanie in as_completed(zadania):
                indeks, url = zadania[zadanie]

                try:
                    wyniki[indeks] = zadanie.result()

                except Exception as blad:
                    bledy[indeks] = {
                        "url": url,
                        "blad": f"{type(blad).__name__}: {blad}",
                    }

    finally:
        for session in sesje:
            session.close()

    # Zachowaj kolejność zgodną z wejściową listą linków.
    produkty = [
        wyniki[indeks]
        for indeks in sorted(wyniki)
    ]

    lista_bledow = [
        bledy[indeks]
        for indeks in sorted(bledy)
    ]

    return produkty, lista_bledow
