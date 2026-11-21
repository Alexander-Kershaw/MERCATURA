import os
from datetime import date

import pytest

from mercatura.source.estate.build import (
    build_source_estate,
)
from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)

RUN_FULL_ESTATE = os.getenv("MERCATURA_RUN_FULL_ESTATE") == "1"


@pytest.mark.skipif(
    not RUN_FULL_ESTATE,
    reason=("set MERCATURA_RUN_FULL_ESTATE=1 to run the complete simulator"),
)
def test_complete_source_estate_builds() -> None:
    config = SimulationConfig(
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
        seed=777,
    )

    context = SimulationContext.create(config)

    estate = build_source_estate(context)

    assert estate.reconciliation.passed

    assert estate.stores
    assert estate.products
    assert estate.orders
    assert estate.order_items
    assert estate.payment_attempts

    assert estate.inventory_movements

    assert estate.availability_snapshots

    assert len(estate.availability_snapshots) == len(estate.demand_profiles)
