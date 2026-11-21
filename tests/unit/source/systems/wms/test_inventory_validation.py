from dataclasses import replace
from datetime import timedelta

import pytest

from mercatura.source.systems.procurement.fulfilment_model import (
    GoodsReceipt,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.inventory_validation import (
    validate_inventory_movements,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)


def replace_movement(
    movements: tuple[InventoryMovement, ...],
    replacement: InventoryMovement,
) -> tuple[InventoryMovement, ...]:
    return tuple(
        replacement if movement.movement_id == replacement.movement_id else movement
        for movement in movements
    )


def validate(
    *,
    movements: tuple[InventoryMovement, ...],
    receipts: tuple[GoodsReceipt, ...],
    routes: tuple[InboundReceiptRoute, ...],
    locations: tuple[InventoryLocation, ...],
) -> None:
    validate_inventory_movements(
        movements,
        receipts,
        routes,
        locations,
    )


def test_valid_dataset_passes(
    inventory_movements: tuple[InventoryMovement, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    validate(
        movements=inventory_movements,
        receipts=goods_receipts,
        routes=inbound_routes,
        locations=inventory_locations,
    )


def test_rejects_duplicate_movement_id(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    broken = (
        *inventory_movements,
        inventory_movements[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate inventory movement_id",
    ):
        validate(
            movements=broken,
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_missing_movement(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    broken = inventory_movements[1:]

    with pytest.raises(
        expected_exception=ValueError,
        match="invalid source reference type",
    ):
        validate(
            movements=broken,
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_unknown_goods_receipt(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = inventory_movements[0]

    broken = replace(
        target,
        source_reference_id=("grn_missing"),
    )

    with pytest.raises(
        ValueError,
        match="unknown goods receipt",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_invalid_source_reference_type(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = inventory_movements[0]

    broken = replace(
        target,
        source_reference_type="INVALID",  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="invalid source reference type",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_inconsistent_group_id(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target_receipt = goods_receipts[0]

    target = next(
        movement
        for movement in inventory_movements
        if (
            movement.source_reference_id == target_receipt.goods_receipt_id
            and movement.movement_sequence == 2
        )
    )

    broken = replace(
        target,
        movement_group_id=("img_wrong"),
    )

    with pytest.raises(
        ValueError,
        match="share one movement_group_id",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_invalid_sequence(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = inventory_movements[0]

    broken = replace(
        target,
        movement_sequence=99,
    )

    with pytest.raises(
        ValueError,
        match="sequence must be 1, 2, 3",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_wrong_market(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = inventory_movements[0]

    broken = replace(
        target,
        market_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="market does not match route",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_wrong_warehouse(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = inventory_movements[0]

    broken = replace(
        target,
        warehouse_id="wh_wrong",
    )

    with pytest.raises(
        ValueError,
        match="warehouse does not match route",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_unknown_inventory_location(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = inventory_movements[0]

    broken = replace(
        target,
        inventory_location_id=("loc_missing"),
    )

    with pytest.raises(
        ValueError,
        match="unknown inventory location",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_wrong_receipt_quantity(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "RECEIPT")
    )

    broken = replace(
        target,
        quantity_delta=(target.quantity_delta + 1),
    )

    with pytest.raises(
        ValueError,
        match="RECEIPT quantity",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_wrong_putaway_out_quantity(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "PUTAWAY_OUT")
    )

    broken = replace(
        target,
        quantity_delta=(target.quantity_delta + 1),
    )

    with pytest.raises(
        ValueError,
        match="PUTAWAY_OUT quantity",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_wrong_putaway_in_quantity(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "PUTAWAY_IN")
    )

    broken = replace(
        target,
        quantity_delta=(target.quantity_delta + 1),
    )

    with pytest.raises(
        ValueError,
        match="PUTAWAY_IN quantity",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_receipt_on_wrong_date(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "RECEIPT")
    )

    broken = replace(
        target,
        event_date=(target.event_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="RECEIPT event date",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_putaway_before_receipt(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target_receipt = goods_receipts[0]

    target = next(
        movement
        for movement in inventory_movements
        if (
            movement.source_reference_id == target_receipt.goods_receipt_id
            and movement.movement_type == "PUTAWAY_OUT"
        )
    )

    partner = next(
        movement
        for movement in inventory_movements
        if (
            movement.source_reference_id == target_receipt.goods_receipt_id
            and movement.movement_type == "PUTAWAY_IN"
        )
    )

    invalid_date = target_receipt.received_date - timedelta(days=1)

    broken_out = replace(
        target,
        event_date=invalid_date,
    )

    broken_in = replace(
        partner,
        event_date=invalid_date,
    )

    broken_movements = replace_movement(
        inventory_movements,
        broken_out,
    )

    broken_movements = replace_movement(
        broken_movements,
        broken_in,
    )

    with pytest.raises(
        ValueError,
        match="putaway cannot occur before",
    ):
        validate(
            movements=broken_movements,
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_putaway_dates_that_do_not_match(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "PUTAWAY_IN")
    )

    broken = replace(
        target,
        event_date=(target.event_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="putaway movements must occur",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_excessive_putaway_delay(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    receipt = goods_receipts[0]

    group = [
        movement
        for movement in inventory_movements
        if (movement.source_reference_id == receipt.goods_receipt_id)
    ]

    broken_movements = inventory_movements

    for movement in group:
        if movement.movement_type in {
            "PUTAWAY_OUT",
            "PUTAWAY_IN",
        }:
            broken = replace(
                movement,
                event_date=(receipt.received_date + timedelta(days=3)),
            )

            broken_movements = replace_movement(
                broken_movements,
                broken,
            )

    with pytest.raises(
        ValueError,
        match="exceeds configured maximum",
    ):
        validate(
            movements=broken_movements,
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_receipt_into_non_receiving_location(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "RECEIPT")
    )

    alternative = next(
        location
        for location in inventory_locations
        if (
            location.warehouse_id == target.warehouse_id
            and location.location_type == "BULK_STORAGE"
        )
    )

    broken = replace(
        target,
        inventory_location_id=(alternative.inventory_location_id),
        location_code=(alternative.location_code),
    )

    with pytest.raises(
        ValueError,
        match="must target RECEIVING",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )


def test_rejects_putaway_in_to_non_bulk_location(
    inventory_movements,
    goods_receipts,
    inbound_routes,
    inventory_locations,
) -> None:
    target = next(
        movement for movement in inventory_movements if (movement.movement_type == "PUTAWAY_IN")
    )

    alternative = next(
        location
        for location in inventory_locations
        if (location.warehouse_id == target.warehouse_id and location.location_type == "PICK_FACE")
    )

    broken = replace(
        target,
        inventory_location_id=(alternative.inventory_location_id),
        location_code=(alternative.location_code),
    )

    with pytest.raises(
        ValueError,
        match="must target BULK_STORAGE",
    ):
        validate(
            movements=replace_movement(
                inventory_movements,
                broken,
            ),
            receipts=goods_receipts,
            routes=inbound_routes,
            locations=inventory_locations,
        )
