from dataclasses import replace
from datetime import date

import pytest

from mercatura.source.systems.fulfilment.model import (
    FulfilmentAllocation,
)
from mercatura.source.systems.fulfilment.reservation_generator import (
    generate_inventory_reservations,
)
from mercatura.source.systems.fulfilment.reservation_validation import (
    validate_inventory_reservations,
)

ALLOCATION_DATE = date(
    2024,
    6,
    15,
)


def _allocation(
    *,
    allocation_id: str = "alloc_001",
    fulfilment_request_id: str = "req_001",
    order_id: str = "ord_001",
    order_item_id: str = "itm_001",
    allocation_sequence: int = 1,
    market_code: str = "GB",
    warehouse_assortment_id: str = "was_001",
    warehouse_id: str = "wh_001",
    warehouse_code: str = "GB-WH-001",
    assortment_id: str = "ast_001",
    product_id: str = "prd_001",
    sku: str = "SKU-001",
    allocated_quantity: int = 4,
    allocation_date: date = ALLOCATION_DATE,
) -> FulfilmentAllocation:
    return FulfilmentAllocation(
        allocation_id=allocation_id,
        fulfilment_request_id=(fulfilment_request_id),
        order_id=order_id,
        order_item_id=order_item_id,
        allocation_sequence=(allocation_sequence),
        market_code=market_code,
        warehouse_assortment_id=(warehouse_assortment_id),
        warehouse_id=warehouse_id,
        warehouse_code=warehouse_code,
        assortment_id=assortment_id,
        product_id=product_id,
        sku=sku,
        allocated_quantity=(allocated_quantity),
        allocation_date=allocation_date,
    )


def test_one_reservation_is_created_per_allocation() -> None:
    allocations = (
        _allocation(),
        _allocation(
            allocation_id="alloc_002",
            allocation_sequence=2,
            warehouse_assortment_id="was_002",
            warehouse_id="wh_002",
            warehouse_code="GB-WH-002",
            allocated_quantity=2,
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    assert len(reservations) == 2

    assert {reservation.allocation_id for reservation in reservations} == {
        "alloc_001",
        "alloc_002",
    }


def test_reservation_quantity_matches_allocation() -> None:
    allocations = (
        _allocation(
            allocated_quantity=7,
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    assert reservations[0].reserved_quantity == 7


def test_reservation_starts_reserved() -> None:
    reservations = generate_inventory_reservations((_allocation(),))

    reservation = reservations[0]

    assert reservation.reservation_status == "RESERVED"

    assert reservation.reserved_date == ALLOCATION_DATE

    assert reservation.released_date is None

    assert reservation.consumed_date is None


def test_metadata_is_preserved_from_allocation() -> None:
    allocation = _allocation()

    reservation = generate_inventory_reservations((allocation,))[0]

    assert reservation.fulfilment_request_id == allocation.fulfilment_request_id

    assert reservation.order_id == allocation.order_id

    assert reservation.order_item_id == allocation.order_item_id

    assert reservation.market_code == allocation.market_code

    assert reservation.warehouse_assortment_id == allocation.warehouse_assortment_id

    assert reservation.warehouse_id == allocation.warehouse_id

    assert reservation.warehouse_code == allocation.warehouse_code

    assert reservation.assortment_id == allocation.assortment_id

    assert reservation.product_id == allocation.product_id

    assert reservation.sku == allocation.sku


def test_no_allocation_produces_no_reservation() -> None:
    reservations = generate_inventory_reservations(())

    assert reservations == ()


def test_split_allocation_produces_multiple_reservations() -> None:
    allocations = (
        _allocation(
            allocation_id="alloc_001",
            allocation_sequence=1,
            allocated_quantity=3,
        ),
        _allocation(
            allocation_id="alloc_002",
            allocation_sequence=2,
            warehouse_assortment_id="was_002",
            warehouse_id="wh_002",
            warehouse_code="GB-WH-002",
            allocated_quantity=2,
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    assert len(reservations) == 2

    assert sum(reservation.reserved_quantity for reservation in reservations) == 5


def test_total_reserved_units_equal_total_allocated_units() -> None:
    allocations = (
        _allocation(
            allocation_id="alloc_001",
            allocated_quantity=4,
        ),
        _allocation(
            allocation_id="alloc_002",
            order_id="ord_002",
            order_item_id="itm_002",
            fulfilment_request_id="req_002",
            allocated_quantity=1,
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    allocated_units = sum(allocation.allocated_quantity for allocation in allocations)

    reserved_units = sum(reservation.reserved_quantity for reservation in reservations)

    assert reserved_units == allocated_units


def test_reservation_ids_are_unique() -> None:
    allocations = (
        _allocation(
            allocation_id="alloc_001",
        ),
        _allocation(
            allocation_id="alloc_002",
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    ids = [reservation.reservation_id for reservation in reservations]

    assert len(ids) == len(set(ids))


def test_generation_is_deterministic() -> None:
    allocations = (
        _allocation(
            allocation_id="alloc_001",
        ),
        _allocation(
            allocation_id="alloc_002",
        ),
    )

    first = generate_inventory_reservations(allocations)

    second = generate_inventory_reservations(allocations)

    assert first == second


def test_input_order_does_not_change_results() -> None:
    allocations = (
        _allocation(
            allocation_id="alloc_001",
            allocation_sequence=1,
        ),
        _allocation(
            allocation_id="alloc_002",
            allocation_sequence=2,
        ),
    )

    first = generate_inventory_reservations(allocations)

    second = generate_inventory_reservations(tuple(reversed(allocations)))

    assert first == second


def test_generated_reservations_pass_validation() -> None:
    allocations = (
        _allocation(
            allocation_id="alloc_001",
            allocated_quantity=3,
        ),
        _allocation(
            allocation_id="alloc_002",
            allocation_sequence=2,
            allocated_quantity=2,
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    validate_inventory_reservations(
        reservations,
        allocations,
    )


def test_validation_rejects_wrong_quantity() -> None:
    allocations = (
        _allocation(
            allocated_quantity=4,
        ),
    )

    reservations = generate_inventory_reservations(allocations)

    invalid = (
        replace(
            reservations[0],
            reserved_quantity=5,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("reservation quantity does not match allocation quantity"),
    ):
        validate_inventory_reservations(
            invalid,
            allocations,
        )


def test_validation_rejects_wrong_warehouse() -> None:
    allocations = (_allocation(),)

    reservations = generate_inventory_reservations(allocations)

    invalid = (
        replace(
            reservations[0],
            warehouse_id="wh_wrong",
        ),
    )

    with pytest.raises(
        ValueError,
        match=("reservation warehouse does not match allocation"),
    ):
        validate_inventory_reservations(
            invalid,
            allocations,
        )


def test_generator_rejects_non_positive_allocation() -> None:
    allocation = _allocation(
        allocated_quantity=0,
    )

    with pytest.raises(
        ValueError,
        match=("cannot reserve a non-positive allocation quantity"),
    ):
        generate_inventory_reservations((allocation,))
