from datetime import date

import pytest

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.pricing.generator import (
    generate_prices,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)


@pytest.fixture(scope="session")
def context() -> SimulationContext:
    return SimulationContext.create(
        SimulationConfig(
            start_date=date(2024, 1, 1),
            end_date=date(2026, 12, 31),
            seed=42,
        )
    )


@pytest.fixture(scope="session")
def products(
    context: SimulationContext,
) -> tuple[Product, ...]:
    return generate_products(context)


@pytest.fixture(scope="session")
def assortments(
    context: SimulationContext,
    products: tuple[Product, ...],
) -> tuple[ProductMarketAssortment, ...]:
    return generate_assortments(
        context,
        products,
    )


@pytest.fixture(scope="session")
def prices(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[ProductPrice, ...]:
    return generate_prices(
        context,
        products,
        assortments,
    )
