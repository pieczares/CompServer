import threading
from concurrent.futures import (
    ThreadPoolExecutor,
    wait,
    FIRST_COMPLETED,
)
from urllib.parse import urljoin, urlsplit, urlunsplit
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
from bs4 import BeautifulSoup, SoupStrainer


def get_links(
    poczatek_linku: str,
    liczba_watkow: int = 5,
    limit_stron: int = 500,
) -> list[str]:
    if liczba_watkow < 1 or limit_stron < 1:
        raise ValueError(
            "Liczba wątków i limit stron muszą być dodatnie."
        )

    poczatek_linku = poczatek_linku.rstrip("/") + "/"
    domena = urlsplit(poczatek_linku).hostname

    if (
        urlsplit(poczatek_linku).scheme not in {"http", "https"}
        or not domena
    ):
        raise ValueError("Podaj pełny adres zaczynający się od http lub https.")

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

    def pobierz_strone(numer: int) -> list[str]:
        url = f"{poczatek_linku}{numer}"
        session = pobierz_sesje()

        response = session.get(url, timeout=(10, 30))

        if response.status_code == 404 and numer > 1:
            return []

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "lxml",
            parse_only=SoupStrainer("a", href=True),
        )

        linki = set()

        for element in soup.find_all("a", href=True):
            adres = urljoin(response.url, element["href"])
            czesci = urlsplit(adres)

            if (
                czesci.scheme in {"http", "https"}
                and czesci.hostname == domena
                and czesci.path.endswith(".html")
                and not czesci.path.startswith("/category/")
            ):
                adres = urlunsplit((
                    czesci.scheme,
                    czesci.netloc,
                    czesci.path,
                    "",
                    "",
                ))

                linki.add(adres)

        return sorted(linki)

    wszystkie_linki = []
    znalezione = set()
    sygnatury_stron = set()

    try:
        with ThreadPoolExecutor(max_workers=liczba_watkow) as executor:
            oczekujace = {}
            bufor = {}

            nastepna_do_zlecenia = 1
            nastepna_do_analizy = 1
            koniec_wykryty = False

            # Małe okno wyprzedzenia, zamiast zlecania wszystkich stron.
            okno = liczba_watkow * 2

            def uzupelnij_kolejke():
                nonlocal nastepna_do_zlecenia

                while (
                        not koniec_wykryty
                        and len(oczekujace) < liczba_watkow
                        and nastepna_do_zlecenia <= limit_stron
                        and nastepna_do_zlecenia
                        < nastepna_do_analizy + okno
                ):
                    numer = nastepna_do_zlecenia
                    zadanie = executor.submit(pobierz_strone, numer)
                    oczekujace[zadanie] = numer
                    nastepna_do_zlecenia += 1

            uzupelnij_kolejke()

            while oczekujace:
                zakonczone, _ = wait(
                    oczekujace,
                    return_when=FIRST_COMPLETED,
                )

                for zadanie in zakonczone:
                    numer = oczekujace.pop(zadanie)

                    try:
                        linki = zadanie.result()
                    except Exception as blad:
                        for pozostale in oczekujace:
                            pozostale.cancel()

                        raise RuntimeError(
                            f"Nie udało się przetworzyć strony: "
                            f"{poczatek_linku}{numer}\n"
                            f"Przyczyna: {type(blad).__name__}: {blad}"
                        ) from blad

                    bufor[numer] = linki

                    # Pusta strona zatrzymuje zlecanie nowych zadań.
                    # Wcześniejsze strony nadal muszą zostać odebrane.
                    if not linki:
                        koniec_wykryty = True

                # Wyniki mogą przyjść w dowolnej kolejności,
                # ale koniec katalogu analizujemy według numerów stron.
                while nastepna_do_analizy in bufor:
                    linki = bufor.pop(nastepna_do_analizy)
                    sygnatura = frozenset(linki)

                    if not linki or sygnatura in sygnatury_stron:
                        for pozostale in oczekujace:
                            pozostale.cancel()

                        return wszystkie_linki

                    sygnatury_stron.add(sygnatura)

                    for adres in linki:
                        if adres not in znalezione:
                            znalezione.add(adres)
                            wszystkie_linki.append(adres)

                    nastepna_do_analizy += 1

                uzupelnij_kolejke()

        return wszystkie_linki

    finally:
        for session in sesje:
            session.close()