from datetime import date

import pytest

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.wms.generator import (
    generate_inventory_locations,
    generate_warehouses,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
    Warehouse,
)


@pytest.fixture(scope="session")
def wms_context() -> SimulationContext:
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
def warehouses(
    wms_context: SimulationContext,
) -> tuple[Warehouse, ...]:
    return generate_warehouses(context=wms_context)


@pytest.fixture(scope="session")
def inventory_locations(
    wms_context: SimulationContext,
    warehouses: tuple[Warehouse, ...],
) -> tuple[InventoryLocation, ...]:
    return generate_inventory_locations(
        wms_context,
        warehouses,
    )
