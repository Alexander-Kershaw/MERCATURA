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


@pytest.fixture(scope="session")
def crm_context() -> SimulationContext:
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
def customers(
    crm_context: SimulationContext,
) -> tuple[Customer, ...]:
    return generate_customers(context=crm_context)
