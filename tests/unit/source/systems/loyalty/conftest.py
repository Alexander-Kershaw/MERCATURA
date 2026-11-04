from datetime import date

import pytest

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.crm.generator import (
    generate_customers,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.loyalty.generator import (
    generate_loyalty_memberships,
)
from mercatura.source.systems.loyalty.model import (
    LoyaltyMembership,
)


@pytest.fixture(scope="session")
def loyalty_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(
                year=2024,
                month=1,
                day=1,
            ),
            end_date=date(
                year=2026,
                month=12,
                day=31,
            ),
            seed=42,
        )
    )


@pytest.fixture(scope="session")
def loyalty_customers(
    loyalty_context: SimulationContext,
) -> tuple[Customer, ...]:
    return generate_customers(context=loyalty_context)


@pytest.fixture(scope="session")
def memberships(
    loyalty_context: SimulationContext,
    loyalty_customers: tuple[Customer, ...],
) -> tuple[LoyaltyMembership, ...]:
    return generate_loyalty_memberships(
        context=loyalty_context,
        customers=loyalty_customers,
    )
