from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapeError:
    url: str
    blad: str
