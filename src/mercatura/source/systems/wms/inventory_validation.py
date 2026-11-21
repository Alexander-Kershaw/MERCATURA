from collections import defaultdict

from mercatura.source.systems.procurement.fulfilment_model import (
    GoodsReceipt,
)
from mercatura.source.systems.wms.inventory_config import (
    DEFAULT_INVENTORY_MOVEMENT_CONFIG,
    InventoryMovementSimulationConfig,
)
from mercatura.source.systems.wms.inventory_model import (
    INVENTORY_MOVEMENT_TYPES,
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)

GOODS_RECEIPT_MOVEMENT_TYPES: set[str] = {
    "RECEIPT",
    "PUTAWAY_OUT",
    "PUTAWAY_IN",
}


def validate_inventory_movements(
    movements: tuple[InventoryMovement, ...],
    receipts: tuple[GoodsReceipt, ...],
    routes: tuple[InboundReceiptRoute, ...],
    locations: tuple[InventoryLocation, ...],
    *,
    config: InventoryMovementSimulationConfig = (DEFAULT_INVENTORY_MOVEMENT_CONFIG),
) -> None:
    _validate_unique_movements(movements)

    _validate_known_movement_types(movements)

    goods_receipt_movements: tuple[InventoryMovement, ...] = tuple(
        movement for movement in movements if (movement.source_reference_type == "GOODS_RECEIPT")
    )

    _validate_receipt_coverage(
        goods_receipt_movements,
        receipts,
    )

    _validate_groups(
        goods_receipt_movements,
        receipts,
        routes,
        locations,
        config,
    )


def _validate_unique_movements(
    movements: tuple[InventoryMovement, ...],
) -> None:
    movement_ids: list[str] = [movement.movement_id for movement in movements]

    if len(movement_ids) != len(set(movement_ids)):
        raise ValueError("duplicate inventory movement_id detected")


def _validate_known_movement_types(
    movements: tuple[InventoryMovement, ...],
) -> None:
    valid_types = set(INVENTORY_MOVEMENT_TYPES)

    for movement in movements:
        if movement.movement_type not in valid_types:
            raise ValueError("inventory movement has unknown movement type")


def _validate_receipt_coverage(
    movements: tuple[InventoryMovement, ...],
    receipts: tuple[GoodsReceipt, ...],
) -> None:
    receipts_by_id: dict[
        str,
        GoodsReceipt,
    ] = {receipt.goods_receipt_id: receipt for receipt in receipts}

    grouped: dict[
        str,
        list[InventoryMovement],
    ] = defaultdict(list)

    for movement in movements:
        if movement.source_reference_type != "GOODS_RECEIPT":
            raise ValueError("inventory movement has invalid source reference type")

        if movement.source_reference_id not in receipts_by_id:
            raise ValueError("inventory movement references unknown goods receipt")

        grouped[movement.source_reference_id].append(movement)

    actual_receipts: set[str] = set(grouped)

    expected_receipts: set[str] = set(receipts_by_id)

    if actual_receipts != expected_receipts:
        raise ValueError("inventory movements do not cover every goods receipt")

    for _receipt_id, rows in grouped.items():
        if len(rows) != 3:
            raise ValueError("invalid source reference type")


def _validate_groups(
    movements: tuple[InventoryMovement, ...],
    receipts: tuple[GoodsReceipt, ...],
    routes: tuple[InboundReceiptRoute, ...],
    locations: tuple[InventoryLocation, ...],
    config: (InventoryMovementSimulationConfig),
) -> None:
    receipts_by_id: dict[
        str,
        GoodsReceipt,
    ] = {receipt.goods_receipt_id: receipt for receipt in receipts}

    routes_by_line: dict[
        str,
        InboundReceiptRoute,
    ] = {route.purchase_order_line_id: route for route in routes}

    locations_by_id: dict[
        str,
        InventoryLocation,
    ] = {location.inventory_location_id: location for location in locations}

    grouped: dict[
        str,
        list[InventoryMovement],
    ] = defaultdict(list)

    for movement in movements:
        grouped[movement.source_reference_id].append(movement)

    for receipt_id, group in grouped.items():
        receipt: GoodsReceipt = receipts_by_id[receipt_id]

        route: InboundReceiptRoute | None = routes_by_line.get(receipt.purchase_order_line_id)

        if route is None:
            raise ValueError("goods receipt has no inbound route")

        _validate_group_identity(group)

        _validate_group_sequence(group)

        _validate_group_metadata(
            group=group,
            receipt=receipt,
            route=route,
            locations_by_id=(locations_by_id),
        )

        _validate_group_semantics(
            group=group,
            receipt=receipt,
            route=route,
            locations_by_id=(locations_by_id),
            config=config,
        )


def _validate_group_identity(
    group: list[InventoryMovement],
) -> None:
    group_ids: set[str] = {movement.movement_group_id for movement in group}

    if len(group_ids) != 1:
        raise ValueError("goods receipt movements must share one movement_group_id")


def _validate_group_sequence(
    group: list[InventoryMovement],
) -> None:
    sequences: list[int] = sorted(movement.movement_sequence for movement in group)

    if sequences != [
        1,
        2,
        3,
    ]:
        raise ValueError("inventory movement sequence must be 1, 2, 3")

    movement_types: set[str] = {movement.movement_type for movement in group}

    if movement_types != GOODS_RECEIPT_MOVEMENT_TYPES:
        raise ValueError("goods receipt must produce RECEIPT, PUTAWAY_OUT and PUTAWAY_IN movements")


def _validate_group_metadata(
    *,
    group: list[InventoryMovement],
    receipt: GoodsReceipt,
    route: InboundReceiptRoute,
    locations_by_id: dict[
        str,
        InventoryLocation,
    ],
) -> None:
    for movement in group:
        if movement.market_code != route.market_code:
            raise ValueError("inventory movement market does not match route")

        if movement.warehouse_id != route.warehouse_id:
            raise ValueError("inventory movement warehouse does not match route")

        if movement.warehouse_code != route.warehouse_code:
            raise ValueError("inventory movement warehouse code does not match route")

        if movement.assortment_id != route.assortment_id:
            raise ValueError("inventory movement assortment does not match route")

        if movement.product_id != route.product_id:
            raise ValueError("inventory movement product does not match route")

        if movement.sku != route.sku:
            raise ValueError("inventory movement SKU does not match route")

        location: InventoryLocation | None = locations_by_id.get(movement.inventory_location_id)

        if location is None:
            raise ValueError("inventory movement references unknown inventory location")

        if movement.location_code != location.location_code:
            raise ValueError("inventory movement location code does not match location")

        if location.warehouse_id != movement.warehouse_id:
            raise ValueError("inventory movement location belongs to another warehouse")

    if receipt.market_code != route.market_code:
        raise ValueError("goods receipt market does not match inbound route")


def _validate_group_semantics(
    *,
    group: list[InventoryMovement],
    receipt: GoodsReceipt,
    route: InboundReceiptRoute,
    locations_by_id: dict[
        str,
        InventoryLocation,
    ],
    config: (InventoryMovementSimulationConfig),
) -> None:
    by_type: dict[
        str,
        InventoryMovement,
    ] = {movement.movement_type: movement for movement in group}

    receipt_movement: InventoryMovement = by_type["RECEIPT"]

    putaway_out: InventoryMovement = by_type["PUTAWAY_OUT"]

    putaway_in: InventoryMovement = by_type["PUTAWAY_IN"]

    quantity: int = receipt.received_quantity

    if receipt_movement.movement_sequence != 1:
        raise ValueError("RECEIPT movement must have sequence 1")

    if putaway_out.movement_sequence != 2:
        raise ValueError("PUTAWAY_OUT movement must have sequence 2")

    if putaway_in.movement_sequence != 3:
        raise ValueError("PUTAWAY_IN movement must have sequence 3")

    if receipt_movement.quantity_delta != quantity:
        raise ValueError("RECEIPT quantity does not match goods receipt")

    if putaway_out.quantity_delta != -quantity:
        raise ValueError("PUTAWAY_OUT quantity does not reverse receiving stock")

    if putaway_in.quantity_delta != quantity:
        raise ValueError("PUTAWAY_IN quantity does not match goods receipt")

    if receipt_movement.event_date != receipt.received_date:
        raise ValueError("RECEIPT event date does not match goods receipt date")

    if putaway_out.event_date != putaway_in.event_date:
        raise ValueError("putaway movements must occur on the same date")

    if putaway_out.event_date < receipt.received_date:
        raise ValueError("putaway cannot occur before goods receipt")

    maximum_delay: int = _maximum_configured_delay(config)

    delay: int = (putaway_out.event_date - receipt.received_date).days

    if delay > maximum_delay:
        raise ValueError("putaway delay exceeds configured maximum")

    receiving_location: InventoryLocation = locations_by_id[receipt_movement.inventory_location_id]

    if receiving_location.location_type != "RECEIVING":
        raise ValueError("RECEIPT movement must target RECEIVING")

    if not (receiving_location.accepts_receipts):
        raise ValueError("RECEIPT location does not accept receipts")

    if receipt_movement.inventory_location_id != route.inventory_location_id:
        raise ValueError("RECEIPT movement does not target routed receiving location")

    if putaway_out.inventory_location_id != route.inventory_location_id:
        raise ValueError("PUTAWAY_OUT must leave routed receiving location")

    bulk_location: InventoryLocation = locations_by_id[putaway_in.inventory_location_id]

    if bulk_location.location_type != "BULK_STORAGE":
        raise ValueError("PUTAWAY_IN must target BULK_STORAGE")

    if bulk_location.warehouse_id != route.warehouse_id:
        raise ValueError("PUTAWAY_IN bulk location must be in routed warehouse")

    receiving_net: int = receipt_movement.quantity_delta + putaway_out.quantity_delta

    if receiving_net != 0:
        raise ValueError("receiving movements do not net to zero after putaway")

    group_net: int = sum(movement.quantity_delta for movement in group)

    if group_net != quantity:
        raise ValueError("inventory movement group net does not equal received quantity")


def _maximum_configured_delay(
    config: (InventoryMovementSimulationConfig),
) -> int:
    if config.two_day_putaway_probability > 0.0:
        return 2

    if config.next_day_putaway_probability > 0.0:
        return 1

    return 0
