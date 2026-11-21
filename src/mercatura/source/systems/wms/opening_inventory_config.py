from dataclasses import dataclass
from decimal import Decimal

"""
==================================================================================================

OPENING INVENTORY CONFIGURATION

==================================================================================================

This dataclass describes the opening inventory (inventory accounting for stock before the
simulation window begins to avoid erroneous stockout behaviour)

The minimum and maximum cover days ranges 28-42 days. This does not mean that every retailer
carries 28-42 days of stock coverage days everywhere. This is just describing a logical starting
position:

- approximately 4-6 weeks of demand + 15 percent safety stock

This should be enough to create enough existing inventory for outbound order fulfilment to
operate without excessive stockout occuring.


==================================================================================================
"""


@dataclass(frozen=True, slots=True)
class OpeningInventoryConfig:
    minimum_cover_days: int = 28
    maximum_cover_days: int = 42
    safety_stock_multiplier: Decimal = Decimal(value="1.15")

    def __post_init__(self) -> None:
        if self.minimum_cover_days <= 0:
            raise ValueError("minimum_cover_days must be positive")

        if self.maximum_cover_days < self.minimum_cover_days:
            raise ValueError("maximum_cover_days must not be below minimum_cover_days")

        if self.safety_stock_multiplier <= Decimal("0"):
            raise ValueError("safety_stock_multiplier must be positive")


DEFAULT_OPENING_INVENTORY_CONFIG = OpeningInventoryConfig()
