from dataclasses import dataclass
from datetime import date
from typing import Literal

LoyaltyTier = Literal[
    "STANDARD",
    "SILVER",
    "GOLD",
    "PLATINUM",
]


LOYALTY_TIERS: tuple[LoyaltyTier, ...] = (
    "STANDARD",
    "SILVER",
    "GOLD",
    "PLATINUM",
)


@dataclass(frozen=True, slots=True)
class LoyaltyMembership:
    membership_id: str
    loyalty_number: str
    customer_id: str
    market_code: str
    enrolled_at: date
    tier: LoyaltyTier
    closed_at: date | None

    @property
    def is_current(self) -> bool:
        return self.closed_at is None

    def is_active_on(
        self,
        value: date,
    ) -> bool:
        return value >= self.enrolled_at and (self.closed_at is None or value < self.closed_at)
