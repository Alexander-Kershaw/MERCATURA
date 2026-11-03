import random
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from mercatura.source.simulation.context import (
    SimulationContext,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.model import (
    Product,
)

"""
====================================================================================

DEMAND PROFILES

====================================================================================

Demand profiles are generated so the POS is not generated at random. Instead, using 
the demand profile, the procurement and order management system can actually 
represent a simulated demand with some level of realism.

The demand profile is ultimatly being used to be consumed by the order 
management and procurements systems so things like replemishment are represented
in a realistic way.

Note that this is not an actual source system, but instead is a simulation state
that serves to make the independent systems behave consistently.

-----------------------------------------------------------------------------------

see schematic:

                    DEMAND PROFILE
                    (simulator only)
                     /            |
                    /             |
                   ▼              ▼
             PROCUREMENT         OMS
                  │              sales
                  ▼
            Purchase Orders
                  │
                  ▼
              Receipts
                  │
                  ▼
              Inventory

-----------------------------------------------------------------------------------

The DemandBand dataclass is used to define the minimum and maximum daily units
for a given department. Daily units being a measure of demand for a given product
in a given market.

The DemandProfile dataclass is what is used to represent an actual demand profile 
for a product.


-----------------------------------------------------------------------------------

DEPARTMENT_DEMAND_BANDS is a dictionary that maps department codes to their
respective demand bands.

MARKET_DEMAND_FACTORS is a dictionary that maps market codes to their respective
demand factors. These factors are used to adjust the base demand for a product
based on the market it is being sold in.

Demand profiles are generated using the generate_demand_profiles function,
and seasonality strength is calculated based on the department code of the product.

====================================================================================
"""


@dataclass(frozen=True, slots=True)
class DemandBand:
    minimum_daily_units: Decimal
    maximum_daily_units: Decimal

    def __post_init__(self) -> None:
        if self.minimum_daily_units <= Decimal(value="0"):
            raise ValueError("minimum_daily_units must be positive")

        if self.maximum_daily_units < self.minimum_daily_units:
            raise ValueError("maximum_daily_units must be >= minimum")


@dataclass(frozen=True, slots=True)
class DemandProfile:
    assortment_id: str
    product_id: str
    sku: str
    market_code: str
    department_code: str
    average_daily_units: Decimal
    volatility: Decimal
    seasonality_strength: Decimal


DEPARTMENT_DEMAND_BANDS: dict[
    str,
    DemandBand,
] = {
    "APP": DemandBand(  # Apparel
        minimum_daily_units=Decimal(value="0.50"),
        maximum_daily_units=Decimal(value="4.50"),
    ),
    "BEAU": DemandBand(  # Beauty
        minimum_daily_units=Decimal(value="0.80"),
        maximum_daily_units=Decimal(value="5.50"),
    ),
    "ELEC": DemandBand(  # Electronics
        minimum_daily_units=Decimal(value="0.20"),
        maximum_daily_units=Decimal(value="2.00"),
    ),
    "GARD": DemandBand(  # Garden
        minimum_daily_units=Decimal(value="0.10"),
        maximum_daily_units=Decimal(value="1.20"),
    ),
    "HOME": DemandBand(  # Home
        minimum_daily_units=Decimal(value="0.20"),
        maximum_daily_units=Decimal(value="1.50"),
    ),
    "KIT": DemandBand(  # Kitchen
        minimum_daily_units=Decimal(value="0.30"),
        maximum_daily_units=Decimal(value="2.00"),
    ),
    "OFF": DemandBand(  # Office
        minimum_daily_units=Decimal(value="0.30"),
        maximum_daily_units=Decimal(value="2.20"),
    ),
    "SPORT": DemandBand(  # Sports
        minimum_daily_units=Decimal(value="0.20"),
        maximum_daily_units=Decimal(value="1.60"),
    ),
    "TOYS": DemandBand(  # Toys
        minimum_daily_units=Decimal(value="0.30"),
        maximum_daily_units=Decimal(value="2.40"),
    ),
}


MARKET_DEMAND_FACTORS: dict[
    str,
    Decimal,
] = {
    "GB": Decimal(value="1.00"),
    "DE": Decimal(value="0.85"),
    "US": Decimal(value="1.20"),
    "CN": Decimal(value="1.10"),
    "NO": Decimal(value="0.30"),
    "RU": Decimal(value="0.50"),
    "JP": Decimal(value="0.75"),
    "KR": Decimal(value="0.60"),
    "FR": Decimal(value="0.80"),
    "NL": Decimal(value="0.45"),
    "PL": Decimal(value="0.55"),
}


def generate_demand_profiles(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[DemandProfile, ...]:
    products_by_id: dict[str, Product] = {product.product_id: product for product in products}

    profiles: list[DemandProfile] = [
        _generate_demand_profile(
            context=context,
            assortment=assortment,
            product=products_by_id[assortment.product_id],
        )
        for assortment in sorted(
            assortments,
            key=lambda row: (
                row.market_code,
                row.sku,
            ),
        )
    ]

    return tuple(profiles)


def _generate_demand_profile(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    product: Product,
) -> DemandProfile:
    rng = random.Random(
        x=context.seed_for(namespace=(f"demand:{assortment.market_code}:{product.sku}"))
    )

    band: DemandBand = DEPARTMENT_DEMAND_BANDS[product.department_code]

    market_factor: Decimal = MARKET_DEMAND_FACTORS[assortment.market_code]

    base_rate = Decimal(
        value=str(
            object=rng.uniform(
                a=float(band.minimum_daily_units),
                b=float(band.maximum_daily_units),
            )
        )
    )

    average_daily_units: Decimal = _round_decimal(
        value=base_rate * market_factor,
        increment=Decimal(value="0.01"),
    )

    volatility: Decimal = _round_decimal(
        value=Decimal(
            value=str(
                object=rng.uniform(
                    a=0.10,
                    b=0.40,
                )
            )
        ),
        increment=Decimal(value="0.01"),
    )

    seasonality_strength: Decimal = _seasonality_strength(
        product=product,
        rng=rng,
    )

    return DemandProfile(
        assortment_id=(assortment.assortment_id),
        product_id=product.product_id,
        sku=product.sku,
        market_code=(assortment.market_code),
        department_code=(product.department_code),
        average_daily_units=(average_daily_units),
        volatility=volatility,
        seasonality_strength=(seasonality_strength),
    )


def _seasonality_strength(
    *,
    product: Product,
    rng: random.Random,
) -> Decimal:
    if product.department_code == "TOYS":
        minimum = 0.25
        maximum = 0.60

    elif product.department_code == "GARD":
        minimum = 0.20
        maximum = 0.50

    elif product.department_code == "APPR":
        minimum = 0.15
        maximum = 0.40

    else:
        minimum = 0.05
        maximum = 0.30

    value = Decimal(
        value=str(
            object=rng.uniform(
                a=minimum,
                b=maximum,
            )
        )
    )

    return _round_decimal(
        value,
        increment=Decimal(value="0.01"),
    )


def _round_decimal(
    value: Decimal,
    increment: Decimal,
) -> Decimal:
    return (value / increment).quantize(
        exp=Decimal(value="1"),
        rounding=ROUND_HALF_UP,
    ) * increment
