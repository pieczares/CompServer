from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_title: str = "Serwer zadań cyklicznych"
    host: str = "127.0.0.1"
    port: int = 8000

    http_threads: int = 5
    crawl_page_limit: int = 500

    # None = bez limitu (tryb produkcyjny); 100 = tryb testowy.
    products_links_limit: int | None = 100

    links_refresh_days: int = 1
    products_refresh_hours: int = 12
    products_first_run_delay_minutes: int = 3
