from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Customer:
    customer_id: str
    customer_number: str
    market_code: str
    country_code: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    city: str
    region: str
    postal_code: str
    created_at: date
    deactivated_at: date | None

    @property
    def is_current(self) -> bool:
        return self.deactivated_at is None

    def is_active_on(
        self,
        value: date,
    ) -> bool:
        return value >= self.created_at and (
            self.deactivated_at is None or value < self.deactivated_at
        )
