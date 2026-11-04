import random
from collections import defaultdict
from datetime import date, timedelta

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.procurement.fulfilment_model import (
    GoodsReceipt,
)
from mercatura.source.systems.wms.inventory_config import (
    DEFAULT_INVENTORY_MOVEMENT_CONFIG,
    InventoryMovementSimulationConfig,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
    InventoryMovementType,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)


def generate_inventory_movements(
    context: SimulationContext,
    receipts: tuple[GoodsReceipt, ...],
    routes: tuple[InboundReceiptRoute, ...],
    locations: tuple[InventoryLocation, ...],
    *,
    config: InventoryMovementSimulationConfig = (DEFAULT_INVENTORY_MOVEMENT_CONFIG),
) -> tuple[InventoryMovement, ...]:
    routes_by_line: dict[str, InboundReceiptRoute] = {
        route.purchase_order_line_id: route for route in routes
    }

    locations_by_id: dict[str, InventoryLocation] = {
        location.inventory_location_id: location for location in locations
    }

    bulk_by_warehouse: dict[str, InventoryLocation] = _bulk_locations_by_warehouse(locations)

    movements: list[InventoryMovement] = []

    for receipt in sorted(
        receipts,
        key=lambda row: row.goods_receipt_id,
    ):
        route: InboundReceiptRoute | None = routes_by_line.get(receipt.purchase_order_line_id)

        if route is None:
            raise ValueError(
                f"no inbound route exists for goods receipt {receipt.goods_receipt_id}"
            )

        receiving: InventoryLocation | None = locations_by_id.get(route.inventory_location_id)

        if receiving is None:
            raise ValueError("inbound route references unknown receiving location")

        bulk: InventoryLocation | None = bulk_by_warehouse.get(route.warehouse_id)

        if bulk is None:
            raise ValueError(f"{route.warehouse_code} has no BULK_STORAGE location")

        movements.extend(
            _generate_receipt_movements(
                context=context,
                receipt=receipt,
                route=route,
                receiving=receiving,
                bulk=bulk,
                config=config,
            )
        )

    return tuple(movements)


def _bulk_locations_by_warehouse(
    locations: tuple[InventoryLocation, ...],
) -> dict[
    str,
    InventoryLocation,
]:
    grouped: dict[
        str,
        list[InventoryLocation],
    ] = defaultdict(list)

    for location in locations:
        if location.location_type == "BULK_STORAGE":
            grouped[location.warehouse_id].append(location)

    result: dict[
        str,
        InventoryLocation,
    ] = {}

    for warehouse_id, rows in grouped.items():
        if len(rows) != 1:
            raise ValueError(
                f"warehouse {warehouse_id} must have exactly one BULK_STORAGE location"
            )

        result[warehouse_id] = rows[0]

    return result


def _generate_receipt_movements(
    *,
    context: SimulationContext,
    receipt: GoodsReceipt,
    route: InboundReceiptRoute,
    receiving: InventoryLocation,
    bulk: InventoryLocation,
    config: InventoryMovementSimulationConfig,
) -> list[InventoryMovement]:
    group_id: str = context.ids.id_for(
        namespace="inventory_movement_group",
        key=receipt.goods_receipt_id,
        prefix="img",
    )

    putaway_delay: int = _select_putaway_delay(
        context=context,
        receipt=receipt,
        config=config,
    )

    putaway_date: date = receipt.received_date + timedelta(days=putaway_delay)

    quantity: int = receipt.received_quantity

    return [
        _build_movement(
            context=context,
            receipt=receipt,
            route=route,
            location=receiving,
            movement_group_id=group_id,
            sequence=1,
            movement_type="RECEIPT",
            quantity_delta=quantity,
            event_date=(receipt.received_date),
        ),
        _build_movement(
            context=context,
            receipt=receipt,
            route=route,
            location=receiving,
            movement_group_id=group_id,
            sequence=2,
            movement_type="PUTAWAY_OUT",
            quantity_delta=-quantity,
            event_date=putaway_date,
        ),
        _build_movement(
            context=context,
            receipt=receipt,
            route=route,
            location=bulk,
            movement_group_id=group_id,
            sequence=3,
            movement_type="PUTAWAY_IN",
            quantity_delta=quantity,
            event_date=putaway_date,
        ),
    ]


def _select_putaway_delay(
    *,
    context: SimulationContext,
    receipt: GoodsReceipt,
    config: InventoryMovementSimulationConfig,
) -> int:
    rng = random.Random(
        x=context.seed_for(namespace=(f"wms:putaway-delay:{receipt.goods_receipt_id}"))
    )

    return rng.choices(
        population=(
            0,
            1,
            2,
        ),
        weights=(
            config.same_day_putaway_probability,
            config.next_day_putaway_probability,
            config.two_day_putaway_probability,
        ),
        k=1,
    )[0]


def _build_movement(
    *,
    context: SimulationContext,
    receipt: GoodsReceipt,
    route: InboundReceiptRoute,
    location: InventoryLocation,
    movement_group_id: str,
    sequence: int,
    movement_type: InventoryMovementType,
    quantity_delta: int,
    event_date,
) -> InventoryMovement:
    stable_key: str = f"{receipt.goods_receipt_id}:{sequence}:{movement_type}"

    movement_id: str = context.ids.id_for(
        namespace="inventory_movement",
        key=stable_key,
        prefix="mov",
    )

    return InventoryMovement(
        movement_id=movement_id,
        movement_group_id=(movement_group_id),
        movement_sequence=sequence,
        movement_type=movement_type,
        source_reference_type=("GOODS_RECEIPT"),
        source_reference_id=(receipt.goods_receipt_id),
        market_code=(route.market_code),
        warehouse_id=(route.warehouse_id),
        warehouse_code=(route.warehouse_code),
        inventory_location_id=(location.inventory_location_id),
        location_code=(location.location_code),
        assortment_id=(route.assortment_id),
        product_id=(route.product_id),
        sku=route.sku,
        quantity_delta=(quantity_delta),
        event_date=event_date,
    )
