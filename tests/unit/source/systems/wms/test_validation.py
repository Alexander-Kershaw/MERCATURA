from dataclasses import replace
from datetime import timedelta
from typing import cast

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
    InventoryLocationType,
    Warehouse,
    WarehouseType,
)
from mercatura.source.systems.wms.validation import (
    validate_wms_topology,
)


def replace_warehouse(
    warehouses: tuple[Warehouse, ...],
    replacement: Warehouse,
) -> tuple[Warehouse, ...]:
    return tuple(
        replacement if warehouse.warehouse_id == replacement.warehouse_id else warehouse
        for warehouse in warehouses
    )


def replace_location(
    locations: tuple[InventoryLocation, ...],
    replacement: InventoryLocation,
) -> tuple[InventoryLocation, ...]:
    return tuple(
        replacement
        if location.inventory_location_id == replacement.inventory_location_id
        else location
        for location in locations
    )


def validate(
    *,
    warehouses: tuple[Warehouse, ...],
    locations: tuple[InventoryLocation, ...],
    context: SimulationContext,
) -> None:
    validate_wms_topology(
        warehouses,
        locations,
        context,
    )


def test_valid_topology_passes_validation(
    warehouses: tuple[Warehouse, ...],
    inventory_locations: tuple[InventoryLocation, ...],
    wms_context: SimulationContext,
) -> None:
    validate(
        warehouses=warehouses,
        locations=inventory_locations,
        context=wms_context,
    )


def test_rejects_duplicate_warehouse_id(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    broken = (
        *warehouses,
        warehouses[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate warehouse_id",
    ):
        validate(
            warehouses=broken,
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_duplicate_warehouse_code(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        warehouses[1],
        warehouse_code=(warehouses[0].warehouse_code),
    )

    with pytest.raises(
        ValueError,
        match="duplicate warehouse_code",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_unknown_market(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        warehouses[0],
        market_code="ZZ",
        country_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="unknown market",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_country_market_mismatch(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        warehouses[0],
        country_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="country does not match market",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_invalid_warehouse_type(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        warehouses[0],
        warehouse_type=cast(
            WarehouseType,
            "INVALID",
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid warehouse type",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_invalid_timezone(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        warehouses[0],
        timezone=("Mars/Olympus_Mons"),
    )

    with pytest.raises(
        ValueError,
        match="invalid timezone",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_warehouse_opening_after_simulation(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        warehouses[0],
        opened_at=(wms_context.config.end_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="opens after simulation end",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_invalid_warehouse_lifecycle(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target = warehouses[0]

    replacement = replace(
        target,
        closed_at=target.opened_at,
    )

    with pytest.raises(
        ValueError,
        match="invalid lifecycle",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_incorrect_store_capability(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target = next(
        warehouse for warehouse in warehouses if (warehouse.warehouse_type == "REGIONAL_DC")
    )

    replacement = replace(
        target,
        supports_store_replenishment=False,
    )

    with pytest.raises(
        ValueError,
        match="store-replenishment capability",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_incorrect_ecommerce_capability(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target = next(
        warehouse for warehouse in warehouses if (warehouse.warehouse_type == "ECOMMERCE_FC")
    )

    replacement = replace(
        target,
        supports_ecommerce=False,
    )

    with pytest.raises(
        ValueError,
        match="ecommerce capability",
    ):
        validate(
            warehouses=replace_warehouse(
                warehouses,
                replacement,
            ),
            locations=inventory_locations,
            context=wms_context,
        )


def test_rejects_duplicate_location_id(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    broken = (
        *inventory_locations,
        inventory_locations[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate inventory_location_id",
    ):
        validate(
            warehouses=warehouses,
            locations=broken,
            context=wms_context,
        )


def test_rejects_duplicate_location_code(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        inventory_locations[1],
        location_code=(inventory_locations[0].location_code),
    )

    with pytest.raises(
        ValueError,
        match="duplicate inventory location code",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_unknown_location_warehouse(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        inventory_locations[0],
        warehouse_id="wh_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown warehouse",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_location_warehouse_code_mismatch(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        inventory_locations[0],
        warehouse_code="WH-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="warehouse code does not match",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_invalid_location_type(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        inventory_locations[0],
        location_type=cast(
            InventoryLocationType,
            "INVALID",
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid inventory location type",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_wrong_location_code(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    replacement = replace(
        inventory_locations[0],
        location_code=("WH-WRONG-RCV"),
    )

    with pytest.raises(
        ValueError,
        match="location code does not match",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_wrong_sellable_flag(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target = next(
        location for location in inventory_locations if (location.location_type == "RECEIVING")
    )

    replacement = replace(
        target,
        is_sellable=True,
    )

    with pytest.raises(
        ValueError,
        match="sellable flag",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_wrong_receipt_capability(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target = next(
        location for location in inventory_locations if (location.location_type == "RECEIVING")
    )

    replacement = replace(
        target,
        accepts_receipts=False,
    )

    with pytest.raises(
        ValueError,
        match="receipt capability",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_wrong_dispatch_capability(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target = next(
        location for location in inventory_locations if (location.location_type == "PICK_FACE")
    )

    replacement = replace(
        target,
        allows_dispatch=False,
    )

    with pytest.raises(
        ValueError,
        match="dispatch capability",
    ):
        validate(
            warehouses=warehouses,
            locations=replace_location(
                inventory_locations,
                replacement,
            ),
            context=wms_context,
        )


def test_rejects_missing_inventory_zone(
    warehouses,
    inventory_locations,
    wms_context,
) -> None:
    target_warehouse = warehouses[0]

    target_location = next(
        location
        for location in inventory_locations
        if (location.warehouse_id == target_warehouse.warehouse_id)
    )

    broken = tuple(
        location
        for location in inventory_locations
        if (location.inventory_location_id != target_location.inventory_location_id)
    )

    with pytest.raises(
        ValueError,
        match="expected inventory location topology",
    ):
        validate(
            warehouses=warehouses,
            locations=broken,
            context=wms_context,
        )
