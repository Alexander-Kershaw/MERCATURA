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
from mercatura.source.systems.oms.generator import (
    generate_orders,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderItem,
)
from mercatura.source.systems.payments.generator import (
    generate_payment_attempts,
)
from mercatura.source.systems.payments.model import (
    PaymentAttempt,
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
def payment_context() -> SimulationContext:
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
def payment_customers(
    payment_context: SimulationContext,
) -> tuple[Customer, ...]:
    return generate_customers(payment_context)


@pytest.fixture(scope="session")
def payment_stores(
    payment_context: SimulationContext,
) -> tuple[Store, ...]:
    return generate_stores(payment_context)


@pytest.fixture(scope="session")
def payment_products(
    payment_context: SimulationContext,
) -> tuple[Product, ...]:
    return generate_products(payment_context)


@pytest.fixture(scope="session")
def payment_assortments(
    payment_context: SimulationContext,
    payment_products: tuple[Product, ...],
) -> tuple[ProductMarketAssortment, ...]:
    return generate_assortments(
        payment_context,
        payment_products,
    )


@pytest.fixture(scope="session")
def payment_prices(
    payment_context: SimulationContext,
    payment_products: tuple[Product, ...],
    payment_assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[ProductPrice, ...]:
    return generate_prices(
        payment_context,
        payment_products,
        payment_assortments,
    )


@pytest.fixture(scope="session")
def payment_demand_profiles(
    payment_context: SimulationContext,
    payment_products: tuple[Product, ...],
    payment_assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[DemandProfile, ...]:
    return generate_demand_profiles(
        payment_context,
        payment_products,
        payment_assortments,
    )


@pytest.fixture(scope="session")
def payment_oms_dataset(
    payment_context: SimulationContext,
    payment_customers: tuple[Customer, ...],
    payment_stores: tuple[Store, ...],
    payment_assortments: tuple[ProductMarketAssortment, ...],
    payment_prices: tuple[ProductPrice, ...],
    payment_demand_profiles: tuple[DemandProfile, ...],
) -> tuple[
    tuple[Order, ...],
    tuple[OrderItem, ...],
]:
    return generate_orders(
        payment_context,
        payment_customers,
        payment_stores,
        payment_assortments,
        payment_prices,
        payment_demand_profiles,
    )


@pytest.fixture(scope="session")
def payment_orders(
    payment_oms_dataset: tuple[
        tuple[Order, ...],
        tuple[OrderItem, ...],
    ],
) -> tuple[Order, ...]:
    return payment_oms_dataset[0]


@pytest.fixture(scope="session")
def payment_attempts(
    payment_context: SimulationContext,
    payment_orders: tuple[Order, ...],
) -> tuple[PaymentAttempt, ...]:
    return generate_payment_attempts(
        payment_context,
        payment_orders,
    )


@pytest.fixture(scope="session")
def small_payment_orders(
    payment_orders: tuple[Order, ...],
) -> tuple[Order, ...]:
    return payment_orders[:5_000]


@pytest.fixture(scope="session")
def small_payment_attempts(
    payment_context: SimulationContext,
    small_payment_orders: tuple[Order, ...],
) -> tuple[PaymentAttempt, ...]:
    return generate_payment_attempts(
        payment_context,
        small_payment_orders,
    )
