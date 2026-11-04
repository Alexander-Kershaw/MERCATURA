from datetime import date

import pytest

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    DemandProfile,
    generate_demand_profiles,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.crm.generator import (
    generate_customers,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.oms.config import (
    MarketOrderConfig,
    OMSSimulationConfig,
)
from mercatura.source.systems.oms.generator import (
    generate_orders,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderItem,
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
from mercatura.source.systems.store.generator import (
    generate_stores,
)
from mercatura.source.systems.store.model import (
    Store,
)


@pytest.fixture(scope="session")
def oms_context() -> SimulationContext:
    return SimulationContext.create(
        SimulationConfig(
            start_date=date(
                2024,
                1,
                1,
            ),
            end_date=date(
                2026,
                12,
                31,
            ),
            seed=42,
        )
    )


@pytest.fixture(scope="session")
def oms_customers(
    oms_context: SimulationContext,
) -> tuple[Customer, ...]:
    return generate_customers(oms_context)


@pytest.fixture(scope="session")
def oms_stores(
    oms_context: SimulationContext,
) -> tuple[Store, ...]:
    return generate_stores(oms_context)


@pytest.fixture(scope="session")
def oms_products(
    oms_context: SimulationContext,
) -> tuple[Product, ...]:
    return generate_products(oms_context)


@pytest.fixture(scope="session")
def oms_assortments(
    oms_context: SimulationContext,
    oms_products: tuple[Product, ...],
) -> tuple[ProductMarketAssortment, ...]:
    return generate_assortments(
        oms_context,
        oms_products,
    )


@pytest.fixture(scope="session")
def oms_prices(
    oms_context: SimulationContext,
    oms_products: tuple[Product, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[ProductPrice, ...]:
    return generate_prices(
        oms_context,
        oms_products,
        oms_assortments,
    )


@pytest.fixture(scope="session")
def oms_demand_profiles(
    oms_context: SimulationContext,
    oms_products: tuple[Product, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[DemandProfile, ...]:
    return generate_demand_profiles(
        oms_context,
        oms_products,
        oms_assortments,
    )


@pytest.fixture(scope="session")
def oms_dataset(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
) -> tuple[
    tuple[Order, ...],
    tuple[OrderItem, ...],
]:
    return generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
    )


@pytest.fixture(scope="session")
def orders(
    oms_dataset: tuple[
        tuple[Order, ...],
        tuple[OrderItem, ...],
    ],
) -> tuple[Order, ...]:
    return oms_dataset[0]


@pytest.fixture(scope="session")
def order_items(
    oms_dataset: tuple[
        tuple[Order, ...],
        tuple[OrderItem, ...],
    ],
) -> tuple[OrderItem, ...]:
    return oms_dataset[1]


@pytest.fixture(scope="session")
def small_oms_config() -> OMSSimulationConfig:
    return OMSSimulationConfig(
        market_configs=(
            MarketOrderConfig(
                market_code="GB",
                order_count=500,
            ),
        ),
        cancellation_probability=0.10,
    )


@pytest.fixture(scope="session")
def small_oms_dataset(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> tuple[
    tuple[Order, ...],
    tuple[OrderItem, ...],
]:
    return generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )


@pytest.fixture(scope="session")
def small_orders(
    small_oms_dataset: tuple[
        tuple[Order, ...],
        tuple[OrderItem, ...],
    ],
) -> tuple[Order, ...]:
    return small_oms_dataset[0]


@pytest.fixture(scope="session")
def small_order_items(
    small_oms_dataset: tuple[
        tuple[Order, ...],
        tuple[OrderItem, ...],
    ],
) -> tuple[OrderItem, ...]:
    return small_oms_dataset[1]
