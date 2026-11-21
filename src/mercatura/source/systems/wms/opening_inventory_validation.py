from collections import Counter
from datetime import date

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    DemandProfile,
)
from mercatura.source.systems.wms.assortment_model import (
    WarehouseAssortment,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)


def validate_opening_inventory_movements(
    movements: tuple[InventoryMovement, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    locations: tuple[InventoryLocation, ...],
    context: SimulationContext,
) -> None:
    simulation_start: date = context.config.start_date

    _validate_unique_ids(movements)

    warehouse_assortments_by_id: dict[str, WarehouseAssortment] = {
        row.warehouse_assortment_id: row for row in warehouse_assortments
    }

    demand_assortment_ids: set[str] = {profile.assortment_id for profile in demand_profiles}

    locations_by_id: dict[str, InventoryLocation] = {
        location.inventory_location_id: location for location in locations
    }

    active_warehouse_assortments: dict[str, WarehouseAssortment] = {
        row.warehouse_assortment_id: row
        for row in warehouse_assortments
        if _is_active_on(
            warehouse_assortment=row,
            value=simulation_start,
        )
    }

    movement_sources: Counter[str] = Counter(movement.source_reference_id for movement in movements)

    if set(movement_sources) != set(active_warehouse_assortments):
        raise ValueError("opening inventory coverage does not match active warehouse assortments")

    if any(count != 1 for count in movement_sources.values()):
        raise ValueError("each active warehouse assortment must have exactly one opening movement")

    for movement in movements:
        _validate_movement(
            movement=movement,
            simulation_start=(simulation_start),
            warehouse_assortments_by_id=(warehouse_assortments_by_id),
            demand_assortment_ids=(demand_assortment_ids),
            locations_by_id=(locations_by_id),
        )


def _validate_unique_ids(
    movements: tuple[InventoryMovement, ...],
) -> None:
    movement_ids: list[str] = [movement.movement_id for movement in movements]

    if len(movement_ids) != len(set(movement_ids)):
        raise ValueError("duplicate opening inventory movement_id detected")

    group_ids: list[str] = [movement.movement_group_id for movement in movements]

    if len(group_ids) != len(set(group_ids)):
        raise ValueError("duplicate opening inventory movement_group_id detected")


def _validate_movement(
    *,
    movement: InventoryMovement,
    simulation_start: date,
    warehouse_assortments_by_id: dict[
        str,
        WarehouseAssortment,
    ],
    demand_assortment_ids: set[str],
    locations_by_id: dict[
        str,
        InventoryLocation,
    ],
) -> None:
    if movement.movement_type != "OPENING_BALANCE":
        raise ValueError("opening inventory movement has invalid movement_type")

    if movement.source_reference_type != "OPENING_BALANCE":
        raise ValueError("opening inventory movement has invalid source type")

    if movement.event_date != simulation_start:
        raise ValueError("opening inventory movement must occur on simulation start")

    if movement.movement_sequence != 1:
        raise ValueError("opening inventory movement sequence must be 1")

    if movement.quantity_delta <= 0:
        raise ValueError("opening inventory quantity must be positive")

    warehouse_assortment: WarehouseAssortment | None = warehouse_assortments_by_id.get(
        movement.source_reference_id
    )

    if warehouse_assortment is None:
        raise ValueError("opening inventory movement references unknown warehouse assortment")

    if not _is_active_on(
        warehouse_assortment,
        value=simulation_start,
    ):
        raise ValueError("opening inventory movement references inactive warehouse assortment")

    if movement.assortment_id not in demand_assortment_ids:
        raise ValueError("opening inventory movement has no demand profile")

    if (
        movement.market_code != warehouse_assortment.market_code
        or movement.warehouse_id != warehouse_assortment.warehouse_id
        or movement.warehouse_code != warehouse_assortment.warehouse_code
        or movement.assortment_id != warehouse_assortment.assortment_id
        or movement.product_id != warehouse_assortment.product_id
        or movement.sku != warehouse_assortment.sku
    ):
        raise ValueError("opening inventory metadata does not match warehouse assortment")

    location: InventoryLocation | None = locations_by_id.get(movement.inventory_location_id)

    if location is None:
        raise ValueError("opening inventory movement references unknown location")

    if (
        location.location_code != movement.location_code
        or location.warehouse_id != movement.warehouse_id
        or location.warehouse_code != movement.warehouse_code
    ):
        raise ValueError("opening inventory location metadata mismatch")

    if location.location_type != "BULK_STORAGE":
        raise ValueError("opening inventory must be placed in BULK_STORAGE")

    if not location.is_sellable:
        raise ValueError("opening inventory must start in a sellable location")


def _is_active_on(
    warehouse_assortment: WarehouseAssortment,
    value: date,
) -> bool:
    if value < warehouse_assortment.stocked_from:
        return False

    stocked_to: date | None = warehouse_assortment.stocked_to

    return stocked_to is None or value < stocked_to
