import math
import random
from collections import defaultdict
from datetime import date
from decimal import Decimal

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
from mercatura.source.systems.wms.opening_inventory_config import (
    DEFAULT_OPENING_INVENTORY_CONFIG,
    OpeningInventoryConfig,
)


def generate_opening_inventory_movements(
    context: SimulationContext,
    demand_profiles: tuple[DemandProfile, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    locations: tuple[InventoryLocation, ...],
    *,
    config: OpeningInventoryConfig = (DEFAULT_OPENING_INVENTORY_CONFIG),
) -> tuple[InventoryMovement, ...]:
    simulation_start: date = context.config.start_date

    demand_by_assortment: dict[str, DemandProfile] = {
        profile.assortment_id: profile for profile in demand_profiles
    }

    bulk_location_by_warehouse: dict[str, InventoryLocation] = _build_bulk_location_index(locations)

    active_by_assortment: dict[
        str,
        list[WarehouseAssortment],
    ] = defaultdict(list)

    for warehouse_assortment in warehouse_assortments:
        if not _is_active_on(
            warehouse_assortment,
            value=simulation_start,
        ):
            continue

        active_by_assortment[warehouse_assortment.assortment_id].append(warehouse_assortment)

    movements: list[InventoryMovement] = []

    for assortment_id in sorted(active_by_assortment):
        profile: DemandProfile | None = demand_by_assortment.get(assortment_id)

        if profile is None:
            raise ValueError(f"active warehouse assortment has no demand profile: {assortment_id}")

        active_warehouse_assortments: list[WarehouseAssortment] = sorted(
            active_by_assortment[assortment_id],
            key=lambda row: (
                row.stocking_priority,
                row.warehouse_code,
            ),
        )

        total_quantity: int = _calculate_opening_quantity(
            context=context,
            profile=profile,
            warehouse_count=len(active_warehouse_assortments),
            config=config,
        )

        allocations: tuple[int, ...] = _allocate_quantity(
            total_quantity=(total_quantity),
            warehouse_assortments=(active_warehouse_assortments),
        )

        for (
            warehouse_assortment,
            quantity,
        ) in zip(
            active_warehouse_assortments,
            allocations,
            strict=True,
        ):
            bulk_location: InventoryLocation | None = bulk_location_by_warehouse.get(
                warehouse_assortment.warehouse_id
            )

            if bulk_location is None:
                raise ValueError(
                    f"warehouse has no BULK_STORAGE location: {warehouse_assortment.warehouse_code}"
                )

            movements.append(
                _build_opening_movement(
                    context=context,
                    warehouse_assortment=(warehouse_assortment),
                    bulk_location=(bulk_location),
                    quantity=quantity,
                )
            )

    return tuple(
        sorted(
            movements,
            key=lambda row: (
                row.market_code,
                row.warehouse_code,
                row.sku,
                row.movement_id,
            ),
        )
    )


def _build_bulk_location_index(
    locations: tuple[InventoryLocation, ...],
) -> dict[
    str,
    InventoryLocation,
]:
    result: dict[
        str,
        InventoryLocation,
    ] = {}

    for location in locations:
        if location.location_type != "BULK_STORAGE":
            continue

        existing: InventoryLocation | None = result.get(location.warehouse_id)

        if existing is not None:
            raise ValueError(
                f"warehouse has multiple BULK_STORAGE locations: {location.warehouse_code}"
            )

        result[location.warehouse_id] = location

    return result


def _is_active_on(
    warehouse_assortment: WarehouseAssortment,
    value,
) -> bool:
    if value < warehouse_assortment.stocked_from:
        return False

    stocked_to: date | None = warehouse_assortment.stocked_to

    return stocked_to is None or value < stocked_to


def _calculate_opening_quantity(
    *,
    context: SimulationContext,
    profile: DemandProfile,
    warehouse_count: int,
    config: OpeningInventoryConfig,
) -> int:
    rng = random.Random(
        x=context.seed_for(namespace=(f"wms:opening_inventory:{profile.assortment_id}"))
    )

    cover_days: int = rng.randint(
        a=config.minimum_cover_days,
        b=config.maximum_cover_days,
    )

    expected_units: Decimal = (
        profile.average_daily_units * Decimal(value=cover_days) * config.safety_stock_multiplier
    )

    quantity: int = math.ceil(expected_units)

    return max(
        quantity,
        warehouse_count,
    )


def _allocate_quantity(
    *,
    total_quantity: int,
    warehouse_assortments: list[WarehouseAssortment],
) -> tuple[int, ...]:
    if not warehouse_assortments:
        raise ValueError("cannot allocate inventory without warehouses")

    if total_quantity < len(warehouse_assortments):
        raise ValueError("total opening quantity is smaller than warehouse count")

    maximum_priority: int = max(row.stocking_priority for row in warehouse_assortments)

    scores: list[int] = [
        (maximum_priority - row.stocking_priority + 1) for row in warehouse_assortments
    ]

    remaining_quantity: int = total_quantity - len(warehouse_assortments)

    score_total: int = sum(scores)

    allocations: list[int] = [1 for _ in warehouse_assortments]

    allocated_extra = 0

    for index, score in enumerate(iterable=scores[:-1]):
        extra: int = remaining_quantity * score // score_total

        allocations[index] += extra

        allocated_extra += extra

    allocations[-1] += remaining_quantity - allocated_extra

    return tuple(allocations)


def _build_opening_movement(
    *,
    context: SimulationContext,
    warehouse_assortment: WarehouseAssortment,
    bulk_location: InventoryLocation,
    quantity: int,
) -> InventoryMovement:
    stable_key: str = warehouse_assortment.warehouse_assortment_id

    movement_group_id: str = context.ids.id_for(
        namespace="inventory_movement_group",
        key=(f"opening_balance:{stable_key}"),
        prefix="img",
    )

    movement_id: str = context.ids.id_for(
        namespace="inventory_movement",
        key=(f"opening_balance:{stable_key}:1"),
        prefix="mov",
    )

    return InventoryMovement(
        movement_id=movement_id,
        movement_group_id=(movement_group_id),
        movement_sequence=1,
        movement_type=("OPENING_BALANCE"),
        source_reference_type=("OPENING_BALANCE"),
        source_reference_id=(warehouse_assortment.warehouse_assortment_id),
        market_code=(warehouse_assortment.market_code),
        warehouse_id=(warehouse_assortment.warehouse_id),
        warehouse_code=(warehouse_assortment.warehouse_code),
        inventory_location_id=(bulk_location.inventory_location_id),
        location_code=(bulk_location.location_code),
        assortment_id=(warehouse_assortment.assortment_id),
        product_id=(warehouse_assortment.product_id),
        sku=(warehouse_assortment.sku),
        quantity_delta=quantity,
        event_date=(context.config.start_date),
    )
