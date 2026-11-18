from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generic, TypeVar

from core.http_session_provider import HttpSessionProvider
from domain.scrape_error import ScrapeError

T = TypeVar("T")


class ParallelPageFetcher(Generic[T]):
    """Wielowątkowo przetwarza listę adresów podaną funkcją; zachowuje kolejność wejścia."""

    def __init__(self, threads: int = 5) -> None:
        if threads < 1:
            raise ValueError("Liczba wątków musi być dodatnia.")
        self._threads = threads

    def run(self, links: list[str],
            handler: Callable[[HttpSessionProvider, str], T]) -> tuple[list[T], list[ScrapeError]]:
        links = list(dict.fromkeys(links))
        results: dict[int, T] = {}
        errors: dict[int, ScrapeError] = {}

        with HttpSessionProvider() as http, \
                ThreadPoolExecutor(max_workers=self._threads) as executor:
            futures = {
                executor.submit(handler, http, url): (index, url)
                for index, url in enumerate(links)
            }
            for future in as_completed(futures):
                index, url = futures[future]
                try:
                    results[index] = future.result()
                except Exception as err:
                    errors[index] = ScrapeError(url, f"{type(err).__name__}: {err}")

        return (
            [results[i] for i in sorted(results)],
            [errors[i] for i in sorted(errors)],
        )
