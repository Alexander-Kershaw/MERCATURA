from dataclasses import dataclass
from decimal import Decimal


@dataclass(
    frozen=True,
    slots=True,
)
class AvailabilitySimulationConfig:
    low_stock_days: Decimal = Decimal("7.00")

    def __post_init__(self) -> None:
        if self.low_stock_days <= Decimal("0"):
            raise ValueError("low_stock_days must be positive")


DEFAULT_AVAILABILITY_CONFIG = AvailabilitySimulationConfig()
