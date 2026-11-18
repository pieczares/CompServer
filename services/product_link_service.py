from services.link_crawler import LinkCrawler


class ProductLinkService:
    MAX_LINK_LENGTH = 255

    def __init__(self, threads: int = 5, page_limit: int = 500) -> None:
        self._threads = threads
        self._page_limit = page_limit

    def fetch(self, warehouse_url: str) -> list[str]:
        raw = LinkCrawler(warehouse_url, self._threads, self._page_limit).crawl()
        return self._clean(raw)

    def _clean(self, raw_links: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for link in raw_links:
            link = link.strip()
            if not link or link in seen:
                continue
            self._check_length(link)
            seen.add(link)
            cleaned.append(link)
        return cleaned

    def _check_length(self, link: str) -> None:
        if len(link) > self.MAX_LINK_LENGTH:
            raise ValueError(
                f"Pobrany link przekracza limit kolumny link "
                f"({self.MAX_LINK_LENGTH} znaków): {link}"
            )
