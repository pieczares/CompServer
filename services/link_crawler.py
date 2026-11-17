from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, SoupStrainer

from core.http import HttpSessionProvider


class LinkCrawler:
    def __init__(self, start_url: str, threads: int = 5,
                 page_limit: int = 500) -> None:
        if threads < 1 or page_limit < 1:
            raise ValueError("Liczba wątków i limit stron muszą być dodatnie.")
        parts = urlsplit(start_url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("Podaj pełny adres zaczynający się od http lub https.")

        self.base_url = start_url.rstrip("/") + "/"
        self.domain = parts.hostname
        self.threads = threads
        self.page_limit = page_limit
        self._http = HttpSessionProvider()

    def _is_product_url(self, parts) -> bool:
        return (
            parts.scheme in {"http", "https"}
            and parts.hostname == self.domain
            and parts.path.endswith(".html")
            and not parts.path.startswith("/category/")
        )

    def _fetch_page(self, number: int) -> list[str]:
        response = self._http.get().get(
            f"{self.base_url}{number}", timeout=self._http.timeout
        )
        if response.status_code == 404 and number > 1:
            return []
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml",
                             parse_only=SoupStrainer("a", href=True))
        links: set[str] = set()
        for a in soup.find_all("a", href=True):
            parts = urlsplit(urljoin(response.url, a["href"]))
            if self._is_product_url(parts):
                links.add(urlunsplit((parts.scheme, parts.netloc,
                                      parts.path, "", "")))
        return sorted(links)

    def crawl(self) -> list[str]:
        result: list[str] = []
        found: set[str] = set()
        seen_signatures: set[frozenset[str]] = set()
        pending: dict = {}
        buffer: dict[int, list[str]] = {}
        next_submit = next_analyze = 1
        end_detected = False
        window = self.threads * 2

        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                def refill() -> None:
                    nonlocal next_submit
                    while (not end_detected
                           and len(pending) < self.threads
                           and next_submit <= self.page_limit
                           and next_submit < next_analyze + window):
                        pending[executor.submit(self._fetch_page, next_submit)] = next_submit
                        next_submit += 1

                def cancel_pending() -> None:
                    for f in pending:
                        f.cancel()

                refill()
                while pending:
                    done, _ = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        number = pending.pop(future)
                        try:
                            links = future.result()
                        except Exception as err:
                            cancel_pending()
                            raise RuntimeError(
                                f"Nie udało się przetworzyć strony: "
                                f"{self.base_url}{number}\n"
                                f"Przyczyna: {type(err).__name__}: {err}"
                            ) from err
                        buffer[number] = links
                        if not links:
                            end_detected = True

                    while next_analyze in buffer:
                        links = buffer.pop(next_analyze)
                        signature = frozenset(links)
                        if not links or signature in seen_signatures:
                            cancel_pending()
                            return result
                        seen_signatures.add(signature)
                        for url in links:
                            if url not in found:
                                found.add(url)
                                result.append(url)
                        next_analyze += 1
                    refill()
            return result
        finally:
            self._http.close()
