from collections import Counter, defaultdict

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.procurement.fulfilment_model import (
    GoodsReceipt,
)
from mercatura.source.systems.wms.inventory_generator import (
    generate_inventory_movements,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)


def test_generation_is_deterministic(
    wms_context: SimulationContext,
    goods_receipts: tuple[GoodsReceipt, ...],
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    first = generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        inventory_locations,
    )

    second = generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        inventory_locations,
    )

    assert first == second


def test_three_movements_per_receipt(
    inventory_movements: tuple[InventoryMovement, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    assert len(inventory_movements) == len(goods_receipts) * 3


def test_movement_ids_are_unique(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    identifiers = [movement.movement_id for movement in inventory_movements]

    assert len(identifiers) == len(set(identifiers))


def test_each_receipt_has_one_movement_group(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    groups: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for movement in inventory_movements:
        groups[movement.source_reference_id].add(movement.movement_group_id)

    assert all(len(group_ids) == 1 for group_ids in groups.values())


def test_each_receipt_has_expected_movement_types(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    grouped: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for movement in inventory_movements:
        grouped[movement.source_reference_id].add(movement.movement_type)

    expected = {
        "RECEIPT",
        "PUTAWAY_OUT",
        "PUTAWAY_IN",
    }

    assert all(types == expected for types in grouped.values())


def test_receipt_movements_are_positive(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    assert all(
        movement.quantity_delta > 0
        for movement in inventory_movements
        if (movement.movement_type == "RECEIPT")
    )


def test_putaway_out_movements_are_negative(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    assert all(
        movement.quantity_delta < 0
        for movement in inventory_movements
        if (movement.movement_type == "PUTAWAY_OUT")
    )


def test_putaway_in_movements_are_positive(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    assert all(
        movement.quantity_delta > 0
        for movement in inventory_movements
        if (movement.movement_type == "PUTAWAY_IN")
    )


def test_receipt_movements_target_receiving(
    inventory_movements: tuple[InventoryMovement, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    locations_by_id = {location.inventory_location_id: location for location in inventory_locations}

    for movement in inventory_movements:
        if movement.movement_type != "RECEIPT":
            continue

        location = locations_by_id[movement.inventory_location_id]

        assert location.location_type == "RECEIVING"


def test_putaway_in_targets_bulk_storage(
    inventory_movements: tuple[InventoryMovement, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    locations_by_id = {location.inventory_location_id: location for location in inventory_locations}

    for movement in inventory_movements:
        if movement.movement_type != "PUTAWAY_IN":
            continue

        location = locations_by_id[movement.inventory_location_id]

        assert location.location_type == "BULK_STORAGE"


def test_movement_group_nets_to_received_quantity(
    inventory_movements: tuple[InventoryMovement, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    totals = Counter()

    for movement in inventory_movements:
        totals[movement.source_reference_id] += movement.quantity_delta

    for receipt in goods_receipts:
        assert totals[receipt.goods_receipt_id] == receipt.received_quantity


def test_receiving_nets_to_zero_after_putaway(
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    grouped: dict[
        str,
        list[InventoryMovement],
    ] = defaultdict(list)

    for movement in inventory_movements:
        grouped[movement.source_reference_id].append(movement)

    for rows in grouped.values():
        receiving_net = sum(
            row.quantity_delta
            for row in rows
            if (
                row.movement_type
                in {
                    "RECEIPT",
                    "PUTAWAY_OUT",
                }
            )
        )

        assert receiving_net == 0


def test_putaway_delay_is_zero_one_or_two_days(
    inventory_movements: tuple[InventoryMovement, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    receipt_dates = {receipt.goods_receipt_id: receipt.received_date for receipt in goods_receipts}

    for movement in inventory_movements:
        if movement.movement_type != "PUTAWAY_IN":
            continue

        delay = (movement.event_date - receipt_dates[movement.source_reference_id]).days

        assert delay in {
            0,
            1,
            2,
        }


def test_putaway_delay_distribution_exists(
    inventory_movements: tuple[InventoryMovement, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    receipt_dates = {receipt.goods_receipt_id: receipt.received_date for receipt in goods_receipts}

    delays = Counter(
        (movement.event_date - receipt_dates[movement.source_reference_id]).days
        for movement in inventory_movements
        if (movement.movement_type == "PUTAWAY_IN")
    )

    assert delays[0] > delays[1]
    assert delays[1] > delays[2]
    assert delays[2] > 0


def test_split_receipts_create_independent_groups(
    goods_receipts: tuple[GoodsReceipt, ...],
    inventory_movements: tuple[InventoryMovement, ...],
) -> None:
    receipts_by_line = Counter(receipt.purchase_order_line_id for receipt in goods_receipts)

    split_line = next(line_id for line_id, count in receipts_by_line.items() if count == 2)

    split_receipt_ids = {
        receipt.goods_receipt_id
        for receipt in goods_receipts
        if (receipt.purchase_order_line_id == split_line)
    }

    group_ids = {
        movement.movement_group_id
        for movement in inventory_movements
        if (movement.source_reference_id in split_receipt_ids)
    }

    assert len(group_ids) == 2


def test_receipt_input_order_independent(
    wms_context: SimulationContext,
    goods_receipts: tuple[GoodsReceipt, ...],
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    first = generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        inventory_locations,
    )

    second = generate_inventory_movements(
        wms_context,
        tuple(reversed(goods_receipts)),
        inbound_routes,
        inventory_locations,
    )

    assert first == second


def test_route_input_order_independent(
    wms_context: SimulationContext,
    goods_receipts: tuple[GoodsReceipt, ...],
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    first = generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        inventory_locations,
    )

    second = generate_inventory_movements(
        wms_context,
        goods_receipts,
        tuple(reversed(inbound_routes)),
        inventory_locations,
    )

    assert first == second


def test_location_input_order_independent(
    wms_context: SimulationContext,
    goods_receipts: tuple[GoodsReceipt, ...],
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    first = generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        inventory_locations,
    )

    second = generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        tuple(reversed(inventory_locations)),
    )

    assert first == second
