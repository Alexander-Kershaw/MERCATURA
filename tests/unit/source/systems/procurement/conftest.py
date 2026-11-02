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
from mercatura.source.systems.pim.model import (
    Product,
)
from mercatura.source.systems.pricing.generator import (
    generate_prices,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.procurement.generator import (
    generate_sourcing_agreements,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.supplier.generator import (
    generate_suppliers,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


@pytest.fixture(scope="session")
def context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
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


@pytest.fixture(scope="session")
def suppliers(
    context: SimulationContext,
) -> tuple[Supplier, ...]:
    return generate_suppliers(context)


@pytest.fixture(scope="session")
def agreements(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> tuple[SourcingAgreement, ...]:
    return generate_sourcing_agreements(
        context,
        products,
        assortments,
        suppliers,
        prices,
    )
