from dataclasses import dataclass
from decimal import Decimal

"""
===========================================================================================

PURCHASE ORDER SIMULATION CONFIGURATION

===========================================================================================

The PurchaseOrderSimulationConfig class defines the configuration parameters for 
simulating purchase orders. It includes options for cycle days, 
weights for supplier selection, and factors for minimum and maximum order quantities.

The cycle_options_dayes is in multiples of 14 days, this two week cadence is useful
for calendar grouping instead of having 4,390 produces all ordering on unrelated
and arbitary dates.

===========================================================================================
"""


@dataclass(frozen=True, slots=True)
class PurchaseOrderSimulationConfig:
    cycle_options_days: tuple[int, ...] = (
        14,
        28,
        42,
        56,
        84,
        112,
    )

    primary_weight: float = 0.85
    secondary_weight: float = 0.12
    backup_weight: float = 0.03

    minimum_quantity_factor: Decimal = Decimal(value="0.90")

    maximum_quantity_factor: Decimal = Decimal(value="1.10")

    def __post_init__(self) -> None:
        if not self.cycle_options_days:
            raise ValueError("cycle_options_days cannot be empty")

        if any(days <= 0 for days in self.cycle_options_days):
            raise ValueError("cycle days must be positive")

        if tuple(sorted(self.cycle_options_days)) != self.cycle_options_days:
            raise ValueError("cycle options must be sorted")

        weights: tuple[float, float, float] = (
            self.primary_weight,
            self.secondary_weight,
            self.backup_weight,
        )

        if any(weight < 0.0 for weight in weights):
            raise ValueError("supplier-selection weights must be non-negative")

        if sum(weights) <= 0.0:
            raise ValueError("supplier-selection weights must contain a positive value")

        if self.minimum_quantity_factor <= Decimal(value="0"):
            raise ValueError("minimum quantity factor must be positive")

        if self.maximum_quantity_factor < self.minimum_quantity_factor:
            raise ValueError("maximum quantity factor must be >= minimum")


DEFAULT_PURCHASE_ORDER_CONFIG = PurchaseOrderSimulationConfig()
