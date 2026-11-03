from collections import Counter, defaultdict

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.wms.generator import (
    generate_inventory_locations,
    generate_warehouses,
)
from mercatura.source.systems.wms.model import (
    INVENTORY_LOCATION_TYPES,
    InventoryLocation,
    Warehouse,
)

EXPECTED_WAREHOUSE_COUNTS: dict[str, int] = {
    "GB": 4,
    "DE": 3,
    "US": 5,
    "CN": 4,
    "NO": 1,
    "RU": 2,
    "JP": 3,
    "KR": 2,
    "FR": 3,
    "NL": 2,
    "PL": 2,
}


def test_warehouse_generation_is_deterministic(
    wms_context: SimulationContext,
) -> None:
    first: tuple[Warehouse, ...] = generate_warehouses(context=wms_context)

    second: tuple[Warehouse, ...] = generate_warehouses(context=wms_context)

    assert first == second


def test_expected_warehouse_count(
    warehouses: tuple[Warehouse, ...],
) -> None:
    assert len(warehouses) == 31


def test_expected_warehouse_counts_by_market(
    warehouses: tuple[Warehouse, ...],
) -> None:
    counts: Counter[str] = Counter(warehouse.market_code for warehouse in warehouses)

    assert dict(counts) == (EXPECTED_WAREHOUSE_COUNTS)


def test_warehouse_ids_are_unique(
    warehouses: tuple[Warehouse, ...],
) -> None:
    ids: list[str] = [warehouse.warehouse_id for warehouse in warehouses]

    assert len(ids) == len(set(ids))


def test_warehouse_codes_are_unique(
    warehouses: tuple[Warehouse, ...],
) -> None:
    codes: list[str] = [warehouse.warehouse_code for warehouse in warehouses]

    assert len(codes) == len(set(codes))


def test_all_warehouses_exist_before_simulation(
    wms_context: SimulationContext,
    warehouses: tuple[Warehouse, ...],
) -> None:
    assert all(warehouse.opened_at < wms_context.config.start_date for warehouse in warehouses)


def test_every_market_supports_store_replenishment(
    warehouses: tuple[Warehouse, ...],
) -> None:
    grouped: dict[
        str,
        list[Warehouse],
    ] = defaultdict(list)

    for warehouse in warehouses:
        grouped[warehouse.market_code].append(warehouse)

    assert all(
        any(warehouse.supports_store_replenishment for warehouse in rows)
        for rows in grouped.values()
    )


def test_every_market_supports_ecommerce(
    warehouses: tuple[Warehouse, ...],
) -> None:
    grouped: dict[
        str,
        list[Warehouse],
    ] = defaultdict(list)

    for warehouse in warehouses:
        grouped[warehouse.market_code].append(warehouse)

    assert all(any(warehouse.supports_ecommerce for warehouse in rows) for rows in grouped.values())


def test_inventory_location_generation_is_deterministic(
    wms_context: SimulationContext,
    warehouses: tuple[Warehouse, ...],
) -> None:
    first = generate_inventory_locations(
        wms_context,
        warehouses,
    )

    second = generate_inventory_locations(
        wms_context,
        warehouses,
    )

    assert first == second


def test_expected_inventory_location_count(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    assert len(inventory_locations) == 155


def test_each_warehouse_has_five_locations(
    warehouses: tuple[Warehouse, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    counts: Counter[str] = Counter(location.warehouse_id for location in inventory_locations)

    assert all(counts[warehouse.warehouse_id] == 5 for warehouse in warehouses)


def test_each_warehouse_has_every_location_type(
    warehouses: tuple[Warehouse, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    grouped: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for location in inventory_locations:
        grouped[location.warehouse_id].add(location.location_type)

    expected = set(INVENTORY_LOCATION_TYPES)

    assert all(grouped[warehouse.warehouse_id] == expected for warehouse in warehouses)


def test_inventory_location_ids_are_unique(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    ids: list[str] = [location.inventory_location_id for location in inventory_locations]

    assert len(ids) == len(set(ids))


def test_inventory_location_codes_are_unique(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    codes: list[str] = [location.location_code for location in inventory_locations]

    assert len(codes) == len(set(codes))


def test_location_generation_is_independent_of_warehouse_order(
    wms_context: SimulationContext,
    warehouses: tuple[Warehouse, ...],
) -> None:
    first = generate_inventory_locations(
        wms_context,
        warehouses,
    )

    second = generate_inventory_locations(
        wms_context,
        tuple(reversed(warehouses)),
    )

    assert first == second


def test_receiving_locations_accept_receipts_only(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    receiving: list[InventoryLocation] = [
        location for location in inventory_locations if (location.location_type == "RECEIVING")
    ]

    assert receiving

    assert all(
        location.accepts_receipts and not location.is_sellable and not location.allows_dispatch
        for location in receiving
    )


def test_pick_faces_are_sellable_and_dispatchable(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    pick_faces: list[InventoryLocation] = [
        location for location in inventory_locations if (location.location_type == "PICK_FACE")
    ]

    assert pick_faces

    assert all(
        location.is_sellable and location.allows_dispatch and not location.accepts_receipts
        for location in pick_faces
    )


def test_quarantine_is_not_sellable(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    quarantine: list[InventoryLocation] = [
        location for location in inventory_locations if (location.location_type == "QUARANTINE")
    ]

    assert all(not location.is_sellable and not location.allows_dispatch for location in quarantine)


def test_only_receiving_accepts_supplier_receipts(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    accepting: set[str] = {
        location.location_type for location in inventory_locations if location.accepts_receipts
    }

    assert accepting == {"RECEIVING"}


def test_only_pick_face_allows_dispatch(
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    dispatching: set[str] = {
        location.location_type for location in inventory_locations if location.allows_dispatch
    }

    assert dispatching == {"PICK_FACE"}
