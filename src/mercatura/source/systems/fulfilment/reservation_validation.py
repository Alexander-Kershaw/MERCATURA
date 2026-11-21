from collections import Counter

from mercatura.source.systems.fulfilment.model import (
    FulfilmentAllocation,
)
from mercatura.source.systems.fulfilment.reservation_model import (
    RESERVATION_STATUSES,
    InventoryReservation,
)


def validate_inventory_reservations(
    reservations: tuple[
        InventoryReservation,
        ...,
    ],
    allocations: tuple[
        FulfilmentAllocation,
        ...,
    ],
) -> None:
    _validate_unique_ids(reservations)

    allocations_by_id = {allocation.allocation_id: allocation for allocation in allocations}

    _validate_allocation_coverage(
        reservations,
        allocations,
    )

    for reservation in reservations:
        allocation = allocations_by_id.get(reservation.allocation_id)

        if allocation is None:
            raise ValueError("inventory reservation references unknown allocation")

        _validate_reservation(
            reservation,
            allocation,
        )

    reserved_units = sum(reservation.reserved_quantity for reservation in reservations)

    allocated_units = sum(allocation.allocated_quantity for allocation in allocations)

    if reserved_units != allocated_units:
        raise ValueError("reserved quantity does not reconcile to allocated quantity")


def _validate_unique_ids(
    reservations: tuple[
        InventoryReservation,
        ...,
    ],
) -> None:
    reservation_ids = [reservation.reservation_id for reservation in reservations]

    if len(reservation_ids) != len(set(reservation_ids)):
        raise ValueError("duplicate reservation_id detected")


def _validate_allocation_coverage(
    reservations: tuple[
        InventoryReservation,
        ...,
    ],
    allocations: tuple[
        FulfilmentAllocation,
        ...,
    ],
) -> None:
    reservation_counts = Counter(reservation.allocation_id for reservation in reservations)

    allocation_ids = {allocation.allocation_id for allocation in allocations}

    reservation_allocation_ids = set(reservation_counts)

    if reservation_allocation_ids != allocation_ids:
        raise ValueError("reservations do not cover every allocation exactly")

    if any(count != 1 for count in reservation_counts.values()):
        raise ValueError("each allocation must have exactly one reservation")


def _validate_reservation(
    reservation: InventoryReservation,
    allocation: FulfilmentAllocation,
) -> None:
    if reservation.reservation_status not in RESERVATION_STATUSES:
        raise ValueError("inventory reservation has invalid status")

    if reservation.reserved_quantity <= 0:
        raise ValueError("inventory reservation quantity must be positive")

    if reservation.reserved_quantity != allocation.allocated_quantity:
        raise ValueError("reservation quantity does not match allocation quantity")

    if reservation.fulfilment_request_id != allocation.fulfilment_request_id:
        raise ValueError("reservation fulfilment request does not match allocation")

    if reservation.order_id != allocation.order_id:
        raise ValueError("reservation order does not match allocation")

    if reservation.order_item_id != allocation.order_item_id:
        raise ValueError("reservation order item does not match allocation")

    if reservation.market_code != allocation.market_code:
        raise ValueError("reservation market does not match allocation")

    if reservation.warehouse_assortment_id != allocation.warehouse_assortment_id:
        raise ValueError("reservation warehouse assortment does not match allocation")

    if reservation.warehouse_id != allocation.warehouse_id:
        raise ValueError("reservation warehouse does not match allocation")

    if reservation.warehouse_code != allocation.warehouse_code:
        raise ValueError("reservation warehouse code does not match allocation")

    if reservation.assortment_id != allocation.assortment_id:
        raise ValueError("reservation assortment does not match allocation")

    if reservation.product_id != allocation.product_id:
        raise ValueError("reservation product does not match allocation")

    if reservation.sku != allocation.sku:
        raise ValueError("reservation SKU does not match allocation")

    if reservation.reserved_date != allocation.allocation_date:
        raise ValueError("reservation date does not match allocation date")

    _validate_status_dates(reservation)


def _validate_status_dates(
    reservation: InventoryReservation,
) -> None:
    if reservation.reservation_status == "RESERVED":
        if reservation.released_date is not None:
            raise ValueError("reserved reservation cannot have released_date")

        if reservation.consumed_date is not None:
            raise ValueError("reserved reservation cannot have consumed_date")

        return

    if reservation.reservation_status == "RELEASED":
        if reservation.released_date is None:
            raise ValueError("released reservation must have released_date")

        if reservation.consumed_date is not None:
            raise ValueError("released reservation cannot also be consumed")

        if reservation.released_date < reservation.reserved_date:
            raise ValueError("reservation cannot be released before it was reserved")

        return

    if reservation.reservation_status == "CONSUMED":
        if reservation.consumed_date is None:
            raise ValueError("consumed reservation must have consumed_date")

        if reservation.released_date is not None:
            raise ValueError("consumed reservation cannot also be released")

        if reservation.consumed_date < reservation.reserved_date:
            raise ValueError("reservation cannot be consumed before it was reserved")
