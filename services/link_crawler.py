from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, SoupStrainer

from core.http_session_provider import HttpSessionProvider
from services.crawl_state import CrawlState


class LinkCrawler:
    def __init__(self, start_url: str, threads: int = 5, page_limit: int = 500) -> None:
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

    def _is_product_url(self, parts: SplitResult) -> bool:
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
        for anchor in soup.find_all("a", href=True):
            parts = urlsplit(urljoin(response.url, anchor["href"]))
            if self._is_product_url(parts):
                links.add(urlunsplit((parts.scheme, parts.netloc, parts.path, "", "")))
        return sorted(links)

    def _refill(self, executor: ThreadPoolExecutor, state: CrawlState) -> None:
        while (number := state.next_page_to_submit()) is not None:
            state.register(executor.submit(self._fetch_page, number), number)

    def _collect(self, state: CrawlState, future: Future) -> None:
        number = state.pop(future)
        try:
            links = future.result()
        except Exception as err:
            state.cancel_pending()
            raise RuntimeError(
                f"Nie udało się przetworzyć strony: {self.base_url}{number}\n"
                f"Przyczyna: {type(err).__name__}: {err}"
            ) from err
        state.store(number, links)

    def crawl(self) -> list[str]:
        state = CrawlState(self.threads, self.page_limit)
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                self._refill(executor, state)
                while state.pending:
                    done, _ = wait(list(state.pending), return_when=FIRST_COMPLETED)
                    for future in done:
                        self._collect(state, future)
                    if state.drain():
                        return state.links
                    self._refill(executor, state)
            return state.links
        finally:
            self._http.close()
