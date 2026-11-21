from dataclasses import dataclass, replace
from datetime import date
from typing import cast

import pytest

from mercatura.source.systems.fulfilment.outbound_generator import (
    generate_outbound_fulfilment,
)
from mercatura.source.systems.fulfilment.outbound_validation import (
    validate_outbound_fulfilment,
)
from mercatura.source.systems.fulfilment.reservation_model import (
    InventoryReservation,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)

RESERVED_DATE = date(
    2024,
    6,
    15,
)


@dataclass(
    frozen=True,
    slots=True,
)
class _LocationStub:
    inventory_location_id: str
    location_code: str
    warehouse_id: str
    location_type: str


def _location(
    *,
    inventory_location_id: str,
    location_code: str,
    warehouse_id: str = "wh_001",
    location_type: str,
) -> InventoryLocation:
    return cast(
        InventoryLocation,
        _LocationStub(
            inventory_location_id=(inventory_location_id),
            location_code=(location_code),
            warehouse_id=(warehouse_id),
            location_type=(location_type),
        ),
    )


def _locations() -> tuple[
    InventoryLocation,
    ...,
]:
    return (
        _location(
            inventory_location_id="bulk_001",
            location_code="GB-WH-001-BULK",
            location_type="BULK_STORAGE",
        ),
        _location(
            inventory_location_id="pick_001",
            location_code="GB-WH-001-PICK",
            location_type="PICK_FACE",
        ),
    )


def _reservation(
    *,
    reservation_id: str = "res_001",
    allocation_id: str = "alloc_001",
    fulfilment_request_id: str = "req_001",
    order_id: str = "ord_001",
    order_item_id: str = "itm_001",
    reserved_quantity: int = 4,
) -> InventoryReservation:
    return InventoryReservation(
        reservation_id=reservation_id,
        allocation_id=allocation_id,
        fulfilment_request_id=(fulfilment_request_id),
        order_id=order_id,
        order_item_id=order_item_id,
        market_code="GB",
        warehouse_assortment_id="was_001",
        warehouse_id="wh_001",
        warehouse_code="GB-WH-001",
        assortment_id="ast_001",
        product_id="prd_001",
        sku="SKU-001",
        reserved_quantity=(reserved_quantity),
        reservation_status="RESERVED",
        reserved_date=RESERVED_DATE,
        released_date=None,
        consumed_date=None,
    )


def _opening_stock(
    *,
    quantity: int = 10,
) -> InventoryMovement:
    return InventoryMovement(
        movement_id="imv_opening",
        movement_group_id="img_opening",
        movement_sequence=1,
        movement_type="OPENING_BALANCE",
        source_reference_type=("OPENING_BALANCE"),
        source_reference_id="opening_001",
        market_code="GB",
        warehouse_id="wh_001",
        warehouse_code="GB-WH-001",
        inventory_location_id="bulk_001",
        location_code="GB-WH-001-BULK",
        assortment_id="ast_001",
        product_id="prd_001",
        sku="SKU-001",
        quantity_delta=quantity,
        event_date=date(
            2024,
            1,
            1,
        ),
    )


def test_one_reservation_creates_one_shipment() -> None:
    reservations = (_reservation(),)

    (
        consumed,
        shipments,
        movements,
    ) = generate_outbound_fulfilment(
        reservations,
        (_opening_stock(),),
        _locations(),
    )

    assert len(consumed) == 1
    assert len(shipments) == 1
    assert len(movements) == 3


def test_reservation_is_consumed_at_dispatch() -> None:
    (
        consumed,
        shipments,
        _,
    ) = generate_outbound_fulfilment(
        (_reservation(),),
        (_opening_stock(),),
        _locations(),
    )

    reservation = consumed[0]
    shipment = shipments[0]

    assert reservation.reservation_status == "CONSUMED"

    assert reservation.consumed_date == shipment.dispatched_date

    assert reservation.released_date is None


def test_shipment_quantity_matches_reservation() -> None:
    (
        _,
        shipments,
        _,
    ) = generate_outbound_fulfilment(
        (
            _reservation(
                reserved_quantity=7,
            ),
        ),
        (
            _opening_stock(
                quantity=10,
            ),
        ),
        _locations(),
    )

    assert shipments[0].shipped_quantity == 7


def test_outbound_movement_chain_is_correct() -> None:
    (
        _,
        _,
        movements,
    ) = generate_outbound_fulfilment(
        (
            _reservation(
                reserved_quantity=4,
            ),
        ),
        (
            _opening_stock(
                quantity=10,
            ),
        ),
        _locations(),
    )

    by_type = {movement.movement_type: movement for movement in movements}

    assert by_type["PICK_OUT"].quantity_delta == -4

    assert by_type["PICK_IN"].quantity_delta == 4

    assert by_type["DISPATCH"].quantity_delta == -4

    assert sum(movement.quantity_delta for movement in movements) == -4


def test_pick_out_leaves_bulk_storage() -> None:
    (
        _,
        _,
        movements,
    ) = generate_outbound_fulfilment(
        (_reservation(),),
        (_opening_stock(),),
        _locations(),
    )

    pick_out = next(movement for movement in movements if (movement.movement_type == "PICK_OUT"))

    assert pick_out.inventory_location_id == "bulk_001"


def test_pick_in_and_dispatch_use_pick_face() -> None:
    (
        _,
        _,
        movements,
    ) = generate_outbound_fulfilment(
        (_reservation(),),
        (_opening_stock(),),
        _locations(),
    )

    by_type = {movement.movement_type: movement for movement in movements}

    assert by_type["PICK_IN"].inventory_location_id == "pick_001"

    assert by_type["DISPATCH"].inventory_location_id == "pick_001"


def test_dispatch_occurs_after_pick() -> None:
    (
        _,
        shipments,
        _,
    ) = generate_outbound_fulfilment(
        (_reservation(),),
        (_opening_stock(),),
        _locations(),
    )

    shipment = shipments[0]

    assert shipment.dispatched_date > shipment.picked_date

    assert (shipment.dispatched_date - shipment.picked_date).days == 1


def test_two_reservations_cannot_pick_same_stock() -> None:
    reservations = (
        _reservation(
            reservation_id="res_001",
            allocation_id="alloc_001",
            order_id="ord_001",
            order_item_id="itm_001",
            reserved_quantity=4,
        ),
        _reservation(
            reservation_id="res_002",
            allocation_id="alloc_002",
            fulfilment_request_id="req_002",
            order_id="ord_002",
            order_item_id="itm_002",
            reserved_quantity=4,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("reservation exceeds available BULK_STORAGE inventory"),
    ):
        generate_outbound_fulfilment(
            reservations,
            (
                _opening_stock(
                    quantity=5,
                ),
            ),
            _locations(),
        )


def test_exact_stock_can_be_fully_consumed() -> None:
    reservations = (
        _reservation(
            reservation_id="res_001",
            allocation_id="alloc_001",
            reserved_quantity=4,
        ),
        _reservation(
            reservation_id="res_002",
            allocation_id="alloc_002",
            fulfilment_request_id="req_002",
            order_id="ord_002",
            order_item_id="itm_002",
            reserved_quantity=1,
        ),
    )

    (
        consumed,
        shipments,
        movements,
    ) = generate_outbound_fulfilment(
        reservations,
        (
            _opening_stock(
                quantity=5,
            ),
        ),
        _locations(),
    )

    assert len(consumed) == 2
    assert len(shipments) == 2

    assert sum(shipment.shipped_quantity for shipment in shipments) == 5

    assert sum(movement.quantity_delta for movement in movements) == -5


def test_non_reserved_reservation_is_rejected() -> None:
    reservation = replace(
        _reservation(),
        reservation_status="CONSUMED",
        consumed_date=RESERVED_DATE,
    )

    with pytest.raises(
        ValueError,
        match=("outbound fulfilment requires RESERVED reservations"),
    ):
        generate_outbound_fulfilment(
            (reservation,),
            (_opening_stock(),),
            _locations(),
        )


def test_generation_is_deterministic() -> None:
    arguments = (
        (_reservation(),),
        (_opening_stock(),),
        _locations(),
    )

    first = generate_outbound_fulfilment(*arguments)

    second = generate_outbound_fulfilment(*arguments)

    assert first == second


def test_generated_outbound_data_passes_validation() -> None:
    original = (
        _reservation(
            reserved_quantity=4,
        ),
    )

    (
        consumed,
        shipments,
        movements,
    ) = generate_outbound_fulfilment(
        original,
        (_opening_stock(),),
        _locations(),
    )

    validate_outbound_fulfilment(
        original,
        consumed,
        shipments,
        movements,
        _locations(),
    )
