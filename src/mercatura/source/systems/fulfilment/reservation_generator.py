from uuid import NAMESPACE_URL, UUID, uuid5

from mercatura.source.systems.fulfilment.model import (
    FulfilmentAllocation,
)
from mercatura.source.systems.fulfilment.reservation_model import (
    InventoryReservation,
)


def generate_inventory_reservations(
    allocations: tuple[
        FulfilmentAllocation,
        ...,
    ],
) -> tuple[
    InventoryReservation,
    ...,
]:

    ordered_allocations: list[FulfilmentAllocation] = sorted(
        allocations,
        key=lambda allocation: (
            allocation.allocation_date,
            allocation.order_id,
            allocation.order_item_id,
            allocation.allocation_sequence,
            allocation.allocation_id,
        ),
    )

    reservations: list[InventoryReservation] = []

    for allocation in ordered_allocations:
        if allocation.allocated_quantity <= 0:
            raise ValueError("cannot reserve a non-positive allocation quantity")

        reservation = InventoryReservation(
            reservation_id=(_reservation_id(allocation_id=allocation.allocation_id)),
            allocation_id=(allocation.allocation_id),
            fulfilment_request_id=(allocation.fulfilment_request_id),
            order_id=allocation.order_id,
            order_item_id=(allocation.order_item_id),
            market_code=(allocation.market_code),
            warehouse_assortment_id=(allocation.warehouse_assortment_id),
            warehouse_id=(allocation.warehouse_id),
            warehouse_code=(allocation.warehouse_code),
            assortment_id=(allocation.assortment_id),
            product_id=(allocation.product_id),
            sku=allocation.sku,
            reserved_quantity=(allocation.allocated_quantity),
            reservation_status="RESERVED",
            reserved_date=(allocation.allocation_date),
            released_date=None,
            consumed_date=None,
        )

        reservations.append(reservation)

    return tuple(reservations)


def _reservation_id(
    allocation_id: str,
) -> str:

    value: UUID = uuid5(
        namespace=NAMESPACE_URL,
        name=(f"mercatura:inventory-reservation:{allocation_id}"),
    )

    return f"res_{value.hex[:20]}"
