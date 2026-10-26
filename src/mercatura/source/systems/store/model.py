from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Store:
    store_id: str
    market_code: str
    store_code: str
    store_name: str
    store_format: str
    city: str
    region: str
    postal_code: str
    country_code: str
    timezone: str
    opened_at: date
    closed_at: date | None = None

    @property
    def is_current(self) -> bool:
        return self.closed_at is None
