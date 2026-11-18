from concurrent.futures import Future


class CrawlState:
    """Stan paginacji: kolejka zadań, bufor wyników i wykrywanie końca katalogu."""

    def __init__(self, threads: int, page_limit: int) -> None:
        self.threads = threads
        self.page_limit = page_limit
        self.window = threads * 2
        self.pending: dict[Future, int] = {}
        self.links: list[str] = []
        self._buffer: dict[int, list[str]] = {}
        self._found: set[str] = set()
        self._signatures: set[frozenset[str]] = set()
        self._next_submit = 1
        self._next_analyze = 1
        self._end_detected = False

    def next_page_to_submit(self) -> int | None:
        if (not self._end_detected
                and len(self.pending) < self.threads
                and self._next_submit <= self.page_limit
                and self._next_submit < self._next_analyze + self.window):
            number = self._next_submit
            self._next_submit += 1
            return number
        return None

    def register(self, future: Future, number: int) -> None:
        self.pending[future] = number

    def pop(self, future: Future) -> int:
        return self.pending.pop(future)

    def store(self, number: int, links: list[str]) -> None:
        self._buffer[number] = links
        if not links:
            self._end_detected = True

    def cancel_pending(self) -> None:
        for future in self.pending:
            future.cancel()

    def drain(self) -> bool:
        """Analizuje strony po kolei. True = koniec katalogu."""
        while self._next_analyze in self._buffer:
            links = self._buffer.pop(self._next_analyze)
            signature = frozenset(links)
            if not links or signature in self._signatures:
                self.cancel_pending()
                return True
            self._signatures.add(signature)
            for url in links:
                if url not in self._found:
                    self._found.add(url)
                    self.links.append(url)
            self._next_analyze += 1
        return False
