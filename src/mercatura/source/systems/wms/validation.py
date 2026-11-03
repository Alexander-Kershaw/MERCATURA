from collections import defaultdict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.wms.config import (
    DEFAULT_INVENTORY_ZONES,
    InventoryZoneDefinition,
)
from mercatura.source.systems.wms.model import (
    INVENTORY_LOCATION_TYPES,
    WAREHOUSE_TYPES,
    InventoryLocation,
    InventoryLocationType,
    Warehouse,
    WarehouseType,
)

EXPECTED_WAREHOUSE_CAPABILITIES: dict[
    WarehouseType,
    tuple[bool, bool],
] = {
    "NATIONAL_DC": (
        True,
        False,
    ),
    "REGIONAL_DC": (
        True,
        False,
    ),
    "ECOMMERCE_FC": (
        False,
        True,
    ),
    "HYBRID_FC": (
        True,
        True,
    ),
}


def validate_wms_topology(
    warehouses: tuple[Warehouse, ...],
    locations: tuple[InventoryLocation, ...],
    context: SimulationContext,
) -> None:
    _validate_warehouses(
        warehouses,
        context,
    )

    _validate_market_coverage(
        warehouses,
        context,
    )

    _validate_locations(
        warehouses,
        locations,
    )

    _validate_location_topology(
        warehouses,
        locations,
    )


def _validate_warehouses(
    warehouses: tuple[Warehouse, ...],
    context: SimulationContext,
) -> None:
    warehouse_ids: list[str] = [warehouse.warehouse_id for warehouse in warehouses]

    if len(warehouse_ids) != len(set(warehouse_ids)):
        raise ValueError("duplicate warehouse_id detected")

    warehouse_codes: list[str] = [warehouse.warehouse_code for warehouse in warehouses]

    if len(warehouse_codes) != len(set(warehouse_codes)):
        raise ValueError("duplicate warehouse_code detected")

    market_codes: set[str] = {market.market_code for market in context.config.markets}

    valid_types = set(WAREHOUSE_TYPES)

    for warehouse in warehouses:
        if not warehouse.warehouse_code.strip():
            raise ValueError("warehouse_code cannot be empty")

        if not warehouse.warehouse_name.strip():
            raise ValueError("warehouse_name cannot be empty")

        if warehouse.market_code not in market_codes:
            raise ValueError(f"{warehouse.warehouse_code} references unknown market")

        if warehouse.country_code != warehouse.market_code:
            raise ValueError(f"{warehouse.warehouse_code} country does not match market")

        if warehouse.warehouse_type not in valid_types:
            raise ValueError(f"{warehouse.warehouse_code} has invalid warehouse type")

        _validate_timezone(warehouse)

        _validate_warehouse_lifecycle(
            warehouse,
            context,
        )

        _validate_warehouse_capabilities(warehouse)


def _validate_timezone(
    warehouse: Warehouse,
) -> None:
    try:
        ZoneInfo(key=warehouse.timezone)

    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"{warehouse.warehouse_code} has invalid timezone") from exc


def _validate_warehouse_lifecycle(
    warehouse: Warehouse,
    context: SimulationContext,
) -> None:
    if warehouse.opened_at > context.config.end_date:
        raise ValueError(f"{warehouse.warehouse_code} opens after simulation end")

    if warehouse.closed_at is not None:
        if warehouse.closed_at <= warehouse.opened_at:
            raise ValueError(f"{warehouse.warehouse_code} has invalid lifecycle")

        if warehouse.closed_at <= context.config.start_date:
            raise ValueError(f"{warehouse.warehouse_code} does not overlap simulation")


def _validate_warehouse_capabilities(
    warehouse: Warehouse,
) -> None:
    expected: tuple[bool, bool] = EXPECTED_WAREHOUSE_CAPABILITIES[warehouse.warehouse_type]

    expected_store: bool = expected[0]
    expected_ecommerce: bool = expected[1]

    if warehouse.supports_store_replenishment != expected_store:
        raise ValueError(
            f"{warehouse.warehouse_code} "
            "store-replenishment capability "
            "does not match warehouse type"
        )

    if warehouse.supports_ecommerce != expected_ecommerce:
        raise ValueError(
            f"{warehouse.warehouse_code} ecommerce capability does not match warehouse type"
        )


def _validate_market_coverage(
    warehouses: tuple[Warehouse, ...],
    context: SimulationContext,
) -> None:
    warehouses_by_market: dict[
        str,
        list[Warehouse],
    ] = defaultdict(list)

    for warehouse in warehouses:
        warehouses_by_market[warehouse.market_code].append(warehouse)

    for market in context.config.markets:
        market_warehouses: list[Warehouse] = warehouses_by_market.get(
            market.market_code,
            [],
        )

        if not market_warehouses:
            raise ValueError(f"market {market.market_code} has no warehouse")

        if not any(warehouse.supports_store_replenishment for warehouse in market_warehouses):
            raise ValueError(f"market {market.market_code} has no store-replenishment warehouse")

        if not any(warehouse.supports_ecommerce for warehouse in market_warehouses):
            raise ValueError(f"market {market.market_code} has no ecommerce-capable warehouse")


def _validate_locations(
    warehouses: tuple[Warehouse, ...],
    locations: tuple[InventoryLocation, ...],
) -> None:
    location_ids: list[str] = [location.inventory_location_id for location in locations]

    if len(location_ids) != len(set(location_ids)):
        raise ValueError("duplicate inventory_location_id detected")

    location_codes: list[str] = [location.location_code for location in locations]

    if len(location_codes) != len(set(location_codes)):
        raise ValueError("duplicate inventory location code detected")

    warehouses_by_id: dict[str, Warehouse] = {
        warehouse.warehouse_id: warehouse for warehouse in warehouses
    }

    valid_location_types = set(INVENTORY_LOCATION_TYPES)

    zone_by_type: dict[str, InventoryZoneDefinition] = {
        zone.location_type: zone for zone in DEFAULT_INVENTORY_ZONES
    }

    for location in locations:
        warehouse: Warehouse | None = warehouses_by_id.get(location.warehouse_id)

        if warehouse is None:
            raise ValueError("inventory location references unknown warehouse")

        if location.warehouse_code != warehouse.warehouse_code:
            raise ValueError("inventory location warehouse code does not match warehouse")

        if location.location_type not in valid_location_types:
            raise ValueError("invalid inventory location type")

        zone: InventoryZoneDefinition = zone_by_type[location.location_type]

        expected_code: str = f"{warehouse.warehouse_code}-{zone.code_suffix}"

        if location.location_code != expected_code:
            raise ValueError("inventory location code does not match warehouse and zone")

        if location.is_sellable != zone.is_sellable:
            raise ValueError("inventory location sellable flag does not match zone")

        if location.accepts_receipts != zone.accepts_receipts:
            raise ValueError("inventory location receipt capability does not match zone")

        if location.allows_dispatch != zone.allows_dispatch:
            raise ValueError("inventory location dispatch capability does not match zone")


def _validate_location_topology(
    warehouses: tuple[Warehouse, ...],
    locations: tuple[InventoryLocation, ...],
) -> None:
    locations_by_warehouse: dict[
        str,
        list[InventoryLocation],
    ] = defaultdict(list)

    for location in locations:
        locations_by_warehouse[location.warehouse_id].append(location)

    expected_types: set[InventoryLocationType] = set(INVENTORY_LOCATION_TYPES)

    for warehouse in warehouses:
        warehouse_locations: list[InventoryLocation] = locations_by_warehouse.get(
            warehouse.warehouse_id,
            [],
        )

        if len(warehouse_locations) != len(expected_types):
            raise ValueError(
                f"{warehouse.warehouse_code} "
                "does not contain the expected "
                "inventory location topology"
            )

        actual_types: list[str] = [location.location_type for location in warehouse_locations]

        if set(actual_types) != expected_types:
            raise ValueError(
                f"{warehouse.warehouse_code} "
                "does not contain every required "
                "inventory location type"
            )

        if len(actual_types) != len(set(actual_types)):
            raise ValueError(
                f"{warehouse.warehouse_code} contains duplicate inventory location types"
            )
