from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class WarehouseAssortmentSimulationConfig:
    low_demand_threshold: Decimal = Decimal(value="0.75")
    medium_demand_threshold: Decimal = Decimal(value="1.75")
    high_demand_threshold: Decimal = Decimal(value="3.00")

    low_demand_warehouse_count: int = 1
    medium_demand_warehouse_count: int = 2
    high_demand_warehouse_count: int = 3
    very_high_demand_warehouse_count: int = 4

    national_dc_weight: float = 1.00
    hybrid_fc_weight: float = 1.00
    regional_dc_weight: float = 0.85
    ecommerce_fc_weight: float = 0.65

    def __post_init__(self) -> None:
        if not (
            Decimal(value="0")
            < self.low_demand_threshold
            < self.medium_demand_threshold
            < self.high_demand_threshold
        ):
            raise ValueError("demand thresholds must be positive and increasing")

        counts: tuple[int, int, int, int] = (
            self.low_demand_warehouse_count,
            self.medium_demand_warehouse_count,
            self.high_demand_warehouse_count,
            self.very_high_demand_warehouse_count,
        )

        if any(count <= 0 for count in counts):
            raise ValueError("warehouse counts must be positive")

        if tuple(sorted(counts)) != counts:
            raise ValueError("warehouse counts must be non-decreasing")

        weights: tuple[float, float, float, float] = (
            self.national_dc_weight,
            self.hybrid_fc_weight,
            self.regional_dc_weight,
            self.ecommerce_fc_weight,
        )

        if any(weight <= 0.0 for weight in weights):
            raise ValueError("warehouse selection weights must be positive")


DEFAULT_WAREHOUSE_ASSORTMENT_CONFIG = WarehouseAssortmentSimulationConfig()
