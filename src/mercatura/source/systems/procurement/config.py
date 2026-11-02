from dataclasses import dataclass
from decimal import Decimal

"""
==========================================================================================

SOURCING PROCUREMENT CONFIGURATION

==========================================================================================

A produrement source can be one of three roles: PRIMARY, SECONDARY, or BACKUP.

The ProcurementSimulationConfig dataclass defines the probabilities of a product
being source from a single source, a dual source, or from a triple source.

The DEFAULT_PROCUREMENT_CONFIG is an instance of ProcurementSimulationConfig 
with the defail probabilities attached to it. The probabilities represent:

45% of product-market combinations = one supplier
40%                                = two suppliers
15%                                = three suppliers

------------------------------------------------------------------------------------------

The ROLE_COST_RANGES dictionary defines the cost ranges for each sourcing role.

SUPPLIER_TYPE_COST_ADJUSTMENTS defines the cost adjustments for each supplier type.

And the SUPPLIER_TYPE_LOGISTICS dictionary defines the lead time and minimum order quantity
ranges for each supplier type.

Note: every assortment in the simulation will have at least one primary supplier,
along with a secondary and/or backup supplier if the product is sourced from multiple 
suppliers.

The MARKET_REGIONS dictionary defines the market regions for each country code. This
is for logistics grouping and for determining the market region of a supplier based 
on its country code.

------------------------------------------------------------------------------------------

The market region selection will be biased:

- same market = strong bias
- same region = moderate bias
- different region = weak bias

For instance a French assortment can source from:

- A FR supplier (strong bias) as same market
- A DE / NL / PL supplier (moderate bias) as in Eurpoe region
- CN / JP / KR supplier (weak bias) as in East Asia region
- A US supplier (weak bias) as in North America region

==========================================================================================
"""


SOURCING_ROLES: tuple[str, ...] = (
    "PRIMARY",
    "SECONDARY",
    "BACKUP",
)


@dataclass(frozen=True, slots=True)
class ProcurementSimulationConfig:
    single_source_probability: float = 0.45
    dual_source_probability: float = 0.40
    triple_source_probability: float = 0.15

    def __post_init__(self) -> None:
        probabilities: tuple[float, float, float] = (
            self.single_source_probability,
            self.dual_source_probability,
            self.triple_source_probability,
        )

        if any(probability < 0.0 or probability > 1.0 for probability in probabilities):
            raise ValueError("source-count probabilities must be between 0 and 1")

        if abs(sum(probabilities) - 1.0) > 1e-9:
            raise ValueError("source-count probabilities must sum to 1")


DEFAULT_PROCUREMENT_CONFIG = ProcurementSimulationConfig()


ROLE_COST_RANGES: dict[
    str,
    tuple[Decimal, Decimal],
] = {
    "PRIMARY": (
        Decimal(value="0.45"),
        Decimal(value="0.62"),
    ),
    "SECONDARY": (
        Decimal(value="0.50"),
        Decimal(value="0.68"),
    ),
    "BACKUP": (
        Decimal(value="0.55"),
        Decimal(value="0.74"),
    ),
}


SUPPLIER_TYPE_COST_ADJUSTMENTS: dict[
    str,
    Decimal,
] = {
    "MANUFACTURER": Decimal(value="-0.03"),
    "DISTRIBUTOR": Decimal(value="0.02"),
    "WHOLESALER": Decimal(value="0.03"),
    "IMPORTER": Decimal(value="0.05"),
}


SUPPLIER_TYPE_LOGISTICS: dict[
    str,
    tuple[int, int, int, int],
] = {
    # lead_min, lead_max, moq_min, moq_max
    "MANUFACTURER": (
        21,
        60,
        50,
        500,
    ),
    "DISTRIBUTOR": (
        5,
        21,
        10,
        100,
    ),
    "WHOLESALER": (
        3,
        14,
        10,
        200,
    ),
    "IMPORTER": (
        14,
        45,
        25,
        300,
    ),
}


MARKET_REGIONS: dict[str, str] = {
    "GB": "EUROPE",
    "DE": "EUROPE",
    "FR": "EUROPE",
    "NL": "EUROPE",
    "NO": "EUROPE",
    "PL": "EUROPE",
    "RU": "EUROPE",
    "CN": "EAST_ASIA",
    "JP": "EAST_ASIA",
    "KR": "EAST_ASIA",
    "US": "NORTH_AMERICA",
}
