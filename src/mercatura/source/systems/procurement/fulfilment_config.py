from dataclasses import dataclass
from decimal import Decimal

"""
==================================================================================================

FULFILMENT SIMULATOR CONFIGURATION

==================================================================================================

The FulfilmentSimulationConfig dataclass contains the following:

- The probabilities of fulfilment outcomes
- The maximum days shipments can be early or late
- The fraction of shipment fulfilment in a split outcome as well as delays
- The fraction of shipment fulfilment in a short shipment

With the configured default values for these simulation parameters I expect approximately:

- 68% exact/on-time full
- 10% early full
- 10% late full
- 7% split but eventually full
- 4% permanently short
- 1% cancelled

==================================================================================================
"""


@dataclass(frozen=True, slots=True)
class FulfilmentSimulationConfig:
    on_time_full_probability: float = 0.68
    early_full_probability: float = 0.10
    late_full_probability: float = 0.10
    split_full_probability: float = 0.07
    short_shipped_probability: float = 0.04
    cancelled_probability: float = 0.01
    maximum_early_days: int = 7
    maximum_late_days: int = 14
    split_minimum_fraction: Decimal = Decimal(value="0.40")
    split_maximum_fraction: Decimal = Decimal(value="0.70")
    split_maximum_delay_days: int = 14
    short_minimum_fraction: Decimal = Decimal(value="0.75")
    short_maximum_fraction: Decimal = Decimal(value="0.95")

    def __post_init__(self) -> None:
        probabilities: tuple[float, float, float, float, float, float] = (
            self.on_time_full_probability,
            self.early_full_probability,
            self.late_full_probability,
            self.split_full_probability,
            self.short_shipped_probability,
            self.cancelled_probability,
        )

        if any(value < 0.0 or value > 1.0 for value in probabilities):
            raise ValueError("fulfilment probabilities must be between 0 and 1")

        if abs(sum(probabilities) - 1.0) > 1e-9:
            raise ValueError("fulfilment probabilities must sum to 1")

        if self.maximum_early_days < 0:
            raise ValueError("maximum_early_days must be non-negative")

        if self.maximum_late_days < 0:
            raise ValueError("maximum_late_days must be non-negative")

        if self.split_maximum_delay_days <= 0:
            raise ValueError("split delay must be positive")

        if not (
            Decimal(value="0")
            < self.split_minimum_fraction
            < self.split_maximum_fraction
            < Decimal("1")
        ):
            raise ValueError("invalid split fractions")

        if not (
            Decimal(value="0")
            < self.short_minimum_fraction
            <= self.short_maximum_fraction
            < Decimal("1")
        ):
            raise ValueError("invalid short-shipment fractions")


DEFAULT_FULFILMENT_CONFIG = FulfilmentSimulationConfig()
