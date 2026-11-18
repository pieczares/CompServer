from dataclasses import dataclass


@dataclass
class RefreshStats:
    inserted: int = 0
    updated: int = 0
    errors: int = 0
    skipped: int = 0
