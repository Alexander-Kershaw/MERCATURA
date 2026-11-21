from collections import defaultdict
from datetime import date

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.fulfilment.model import (
    FulfilmentAllocation,
    FulfilmentAllocationStatus,
    FulfilmentRequest,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderItem,
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

WAREHOUSE_FULFILLED_CHANNELS: set[str] = {
    "WEB",
    "MOBILE",
}


def generate_fulfilment_allocations(
    context: SimulationContext,
    orders: tuple[Order, ...],
    order_items: tuple[OrderItem, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_movements: tuple[InventoryMovement, ...],
    locations: tuple[InventoryLocation, ...],
) -> tuple[
    tuple[FulfilmentRequest, ...],
    tuple[FulfilmentAllocation, ...],
]:
    orders_by_id: dict[str, Order] = {order.order_id: order for order in orders}

    sellable_location_ids: set[str] = {
        location.inventory_location_id for location in locations if location.is_sellable
    }

    eligible_warehouse_assortments: dict[str, tuple[WarehouseAssortment, ...]] = (
        _build_warehouse_assortment_index(warehouse_assortments)
    )

    sellable_movements: list[InventoryMovement] = sorted(
        (
            movement
            for movement in inventory_movements
            if (movement.inventory_location_id in sellable_location_ids)
        ),
        key=lambda movement: (
            movement.event_date,
            movement.movement_id,
        ),
    )

    eligible_items: list[OrderItem] = sorted(
        (
            item
            for item in order_items
            if _is_warehouse_fulfilled_item(
                item=item,
                orders_by_id=orders_by_id,
            )
        ),
        key=lambda item: (
            orders_by_id[item.order_id].order_date,
            orders_by_id[item.order_id].order_number,
            item.line_number,
        ),
    )

    available_balance: dict[
        tuple[
            str,
            str,
        ],
        int,
    ] = defaultdict(int)

    movement_index = 0

    requests: list[FulfilmentRequest] = []

    allocations: list[FulfilmentAllocation] = []

    for item in eligible_items:
        order: Order = orders_by_id[item.order_id]

        movement_index: int = _apply_sellable_movements_through_date(
            movements=(sellable_movements),
            movement_index=(movement_index),
            through_date=(order.order_date),
            balances=(available_balance),
        )

        (
            request,
            item_allocations,
        ) = _allocate_order_item(
            context=context,
            order=order,
            item=item,
            warehouse_assortments=(
                eligible_warehouse_assortments.get(
                    item.assortment_id,
                    (),
                )
            ),
            balances=available_balance,
        )

        requests.append(request)

        allocations.extend(item_allocations)

    return (
        tuple(requests),
        tuple(allocations),
    )


def _is_warehouse_fulfilled_item(
    *,
    item: OrderItem,
    orders_by_id: dict[
        str,
        Order,
    ],
) -> bool:
    order: Order | None = orders_by_id.get(item.order_id)

    if order is None:
        raise ValueError("order item references unknown order")

    return order.order_status == "CONFIRMED" and order.channel in WAREHOUSE_FULFILLED_CHANNELS


def _build_warehouse_assortment_index(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> dict[
    str,
    tuple[WarehouseAssortment, ...],
]:
    grouped: dict[
        str,
        list[WarehouseAssortment],
    ] = defaultdict(list)

    for row in warehouse_assortments:
        grouped[row.assortment_id].append(row)

    return {
        assortment_id: tuple(
            sorted(
                rows,
                key=lambda row: (
                    row.stocking_priority,
                    row.warehouse_code,
                ),
            )
        )
        for (
            assortment_id,
            rows,
        ) in grouped.items()
    }


def _apply_sellable_movements_through_date(
    *,
    movements: list[InventoryMovement],
    movement_index: int,
    through_date: date,
    balances: dict[
        tuple[
            str,
            str,
        ],
        int,
    ],
) -> int:
    index: int = movement_index

    while index < len(movements):
        movement: InventoryMovement = movements[index]

        if movement.event_date > through_date:
            break

        key: tuple[str, str] = (
            movement.warehouse_id,
            movement.assortment_id,
        )

        balances[key] += movement.quantity_delta

        index += 1

    return index


def _allocate_order_item(
    *,
    context: SimulationContext,
    order: Order,
    item: OrderItem,
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    balances: dict[
        tuple[
            str,
            str,
        ],
        int,
    ],
) -> tuple[
    FulfilmentRequest,
    tuple[FulfilmentAllocation, ...],
]:
    request_id: str = context.ids.id_for(
        namespace="fulfilment_request",
        key=item.order_item_id,
        prefix="ful",
    )

    remaining: int = item.quantity

    allocations: list[FulfilmentAllocation] = []

    allocation_sequence = 1

    for warehouse_assortment in warehouse_assortments:
        if not _warehouse_assortment_active_on(
            warehouse_assortment,
            value=order.order_date,
        ):
            continue

        if warehouse_assortment.market_code != order.market_code:
            continue

        balance_key: tuple[str, str] = (
            warehouse_assortment.warehouse_id,
            item.assortment_id,
        )

        available: int = balances.get(
            balance_key,
            0,
        )

        if available <= 0:
            continue

        allocated_quantity: int = min(
            remaining,
            available,
        )

        allocation_id: str = context.ids.id_for(
            namespace="fulfilment_allocation",
            key=(f"{item.order_item_id}:{allocation_sequence}:{warehouse_assortment.warehouse_id}"),
            prefix="all",
        )

        allocations.append(
            FulfilmentAllocation(
                allocation_id=(allocation_id),
                fulfilment_request_id=(request_id),
                order_id=(order.order_id),
                order_item_id=(item.order_item_id),
                allocation_sequence=(allocation_sequence),
                market_code=(order.market_code),
                warehouse_assortment_id=(warehouse_assortment.warehouse_assortment_id),
                warehouse_id=(warehouse_assortment.warehouse_id),
                warehouse_code=(warehouse_assortment.warehouse_code),
                assortment_id=(item.assortment_id),
                product_id=(item.product_id),
                sku=item.sku,
                allocated_quantity=(allocated_quantity),
                allocation_date=(order.order_date),
            )
        )

        balances[balance_key] = available - allocated_quantity

        remaining -= allocated_quantity

        allocation_sequence += 1

        if remaining == 0:
            break

    allocated_quantity = item.quantity - remaining

    status = _allocation_status(
        requested_quantity=(item.quantity),
        allocated_quantity=(allocated_quantity),
    )

    request = FulfilmentRequest(
        fulfilment_request_id=(request_id),
        order_id=order.order_id,
        order_number=(order.order_number),
        order_item_id=(item.order_item_id),
        line_number=(item.line_number),
        market_code=(order.market_code),
        channel=order.channel,
        assortment_id=(item.assortment_id),
        product_id=(item.product_id),
        sku=item.sku,
        requested_quantity=(item.quantity),
        allocated_quantity=(allocated_quantity),
        unallocated_quantity=(remaining),
        allocation_status=(status),
        allocation_date=(order.order_date),
    )

    return (
        request,
        tuple(allocations),
    )


def _warehouse_assortment_active_on(
    warehouse_assortment: WarehouseAssortment,
    value: date,
) -> bool:
    if value < warehouse_assortment.stocked_from:
        return False

    stocked_to: date | None = warehouse_assortment.stocked_to

    return stocked_to is None or value < stocked_to


def _allocation_status(
    *,
    requested_quantity: int,
    allocated_quantity: int,
) -> FulfilmentAllocationStatus:
    if allocated_quantity == requested_quantity:
        return "ALLOCATED"

    if allocated_quantity == 0:
        return "BACKORDERED"

    return "PARTIALLY_ALLOCATED"
