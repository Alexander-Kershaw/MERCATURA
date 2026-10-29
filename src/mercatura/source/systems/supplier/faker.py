from faker import Faker

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig

"""
======================================================================

DETERMINISTIC FAKER FOR SUPPLIERS

======================================================================

Takes the simulation context, market_code, supplier_number as
as priority.

the market code is extracted from the context, and faker is used to
generate a supplier relevant to the market code locale and keeping 
the supplier number.

======================================================================
"""


def build_supplier_faker(
    context: SimulationContext,
    *,
    market_code: str,
    supplier_number: int,
) -> Faker:
    market: MarketConfig = context.market(market_code)

    fake = Faker(locale=market.locale)

    fake.seed_instance(
        seed=context.seed_for(namespace=(f"faker:supplier:{market_code}:{supplier_number}"))
    )

    return fake
