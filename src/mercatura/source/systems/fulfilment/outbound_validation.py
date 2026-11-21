from collections import Counter, defaultdict

from mercatura.source.systems.fulfilment.reservation_model import (
    InventoryReservation,
)
from mercatura.source.systems.fulfilment.shipment_model import (
    OutboundShipment,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)

OUTBOUND_MOVEMENT_TYPES = {
    "PICK_OUT",
    "PICK_IN",
    "DISPATCH",
}


def validate_outbound_fulfilment(
    original_reservations: tuple[
        InventoryReservation,
        ...,
    ],
    consumed_reservations: tuple[
        InventoryReservation,
        ...,
    ],
    shipments: tuple[
        OutboundShipment,
        ...,
    ],
    movements: tuple[
        InventoryMovement,
        ...,
    ],
    locations: tuple[
        InventoryLocation,
        ...,
    ],
) -> None:
    _validate_unique_ids(
        consumed_reservations,
        shipments,
        movements,
    )

    original_by_id = {
        reservation.reservation_id: reservation for reservation in original_reservations
    }

    consumed_by_id = {
        reservation.reservation_id: reservation for reservation in consumed_reservations
    }

    shipment_by_reservation = {shipment.reservation_id: shipment for shipment in shipments}

    locations_by_id = {location.inventory_location_id: location for location in locations}

    if set(original_by_id) != set(consumed_by_id):
        raise ValueError("consumed reservation coverage does not match original reservations")

    shipment_counts = Counter(shipment.reservation_id for shipment in shipments)

    if set(shipment_counts) != set(original_by_id):
        raise ValueError("shipments do not cover every reservation")

    if any(count != 1 for count in shipment_counts.values()):
        raise ValueError("each reservation must produce exactly one shipment")

    grouped_movements: dict[
        str,
        list[InventoryMovement],
    ] = defaultdict(list)

    for movement in movements:
        if movement.source_reference_type != "FULFILMENT_SHIPMENT":
            raise ValueError("outbound movement has invalid source reference type")

        grouped_movements[movement.source_reference_id].append(movement)

    for reservation_id, original in original_by_id.items():
        consumed = consumed_by_id[reservation_id]

        shipment = shipment_by_reservation[reservation_id]

        _validate_reservation_transition(
            original,
            consumed,
        )

        _validate_shipment(
            consumed,
            shipment,
        )

        shipment_movements = grouped_movements.get(
            shipment.shipment_id,
            [],
        )

        _validate_movement_group(
            shipment,
            shipment_movements,
            locations_by_id,
        )

    expected_shipment_ids = {shipment.shipment_id for shipment in shipments}

    if set(grouped_movements) != expected_shipment_ids:
        raise ValueError("outbound movements do not cover every shipment")

    shipped_units = sum(shipment.shipped_quantity for shipment in shipments)

    consumed_units = sum(reservation.reserved_quantity for reservation in consumed_reservations)

    physical_net = sum(movement.quantity_delta for movement in movements)

    if shipped_units != consumed_units:
        raise ValueError("shipment quantities do not reconcile to consumed reservations")

    if physical_net != -shipped_units:
        raise ValueError("outbound physical inventory net does not equal shipped quantity")


def _validate_unique_ids(
    reservations: tuple[
        InventoryReservation,
        ...,
    ],
    shipments: tuple[
        OutboundShipment,
        ...,
    ],
    movements: tuple[
        InventoryMovement,
        ...,
    ],
) -> None:
    reservation_ids = [reservation.reservation_id for reservation in reservations]

    shipment_ids = [shipment.shipment_id for shipment in shipments]

    movement_ids = [movement.movement_id for movement in movements]

    if len(reservation_ids) != len(set(reservation_ids)):
        raise ValueError("duplicate reservation_id detected")

    if len(shipment_ids) != len(set(shipment_ids)):
        raise ValueError("duplicate shipment_id detected")

    if len(movement_ids) != len(set(movement_ids)):
        raise ValueError("duplicate outbound movement_id detected")


def _validate_reservation_transition(
    original: InventoryReservation,
    consumed: InventoryReservation,
) -> None:
    if original.reservation_status != "RESERVED":
        raise ValueError("original reservation must be RESERVED")

    if consumed.reservation_status != "CONSUMED":
        raise ValueError("fulfilled reservation must be CONSUMED")

    if consumed.reserved_quantity != original.reserved_quantity:
        raise ValueError("reservation quantity changed during fulfilment")

    if consumed.reserved_date != original.reserved_date:
        raise ValueError("reservation date changed during fulfilment")

    if consumed.released_date is not None:
        raise ValueError("consumed reservation cannot also be released")

    if consumed.consumed_date is None:
        raise ValueError("consumed reservation requires consumed_date")

    if consumed.consumed_date < consumed.reserved_date:
        raise ValueError("reservation cannot be consumed before reservation")


def _validate_shipment(
    reservation: InventoryReservation,
    shipment: OutboundShipment,
) -> None:
    if shipment.reservation_id != reservation.reservation_id:
        raise ValueError("shipment reservation does not match reservation")

    if shipment.allocation_id != reservation.allocation_id:
        raise ValueError("shipment allocation does not match reservation")

    if shipment.fulfilment_request_id != reservation.fulfilment_request_id:
        raise ValueError("shipment fulfilment request does not match reservation")

    if shipment.order_id != reservation.order_id:
        raise ValueError("shipment order does not match reservation")

    if shipment.order_item_id != reservation.order_item_id:
        raise ValueError("shipment order item does not match reservation")

    if shipment.market_code != reservation.market_code:
        raise ValueError("shipment market does not match reservation")

    if shipment.warehouse_id != reservation.warehouse_id:
        raise ValueError("shipment warehouse does not match reservation")

    if shipment.assortment_id != reservation.assortment_id:
        raise ValueError("shipment assortment does not match reservation")

    if shipment.product_id != reservation.product_id:
        raise ValueError("shipment product does not match reservation")

    if shipment.sku != reservation.sku:
        raise ValueError("shipment SKU does not match reservation")

    if shipment.shipped_quantity != reservation.reserved_quantity:
        raise ValueError("shipment quantity does not match reservation")

    if shipment.picked_date != reservation.reserved_date:
        raise ValueError("shipment pick date does not match reservation date")

    if shipment.dispatched_date != reservation.consumed_date:
        raise ValueError("shipment dispatch date does not match reservation consumption date")

    if shipment.dispatched_date < shipment.picked_date:
        raise ValueError("shipment cannot dispatch before picking")

    if shipment.shipment_status != "DISPATCHED":
        raise ValueError("shipment must be DISPATCHED")


def _validate_movement_group(
    shipment: OutboundShipment,
    group: list[InventoryMovement],
    locations_by_id: dict[
        str,
        InventoryLocation,
    ],
) -> None:
    if len(group) != 3:
        raise ValueError("shipment must produce exactly three outbound movements")

    group_ids = {movement.movement_group_id for movement in group}

    if len(group_ids) != 1:
        raise ValueError("shipment movements must share one movement_group_id")

    sequences = sorted(movement.movement_sequence for movement in group)

    if sequences != [
        1,
        2,
        3,
    ]:
        raise ValueError("outbound movement sequence must be 1, 2, 3")

    movement_types = {movement.movement_type for movement in group}

    if movement_types != OUTBOUND_MOVEMENT_TYPES:
        raise ValueError("shipment must produce PICK_OUT, PICK_IN and DISPATCH movements")

    by_type = {movement.movement_type: movement for movement in group}

    pick_out = by_type["PICK_OUT"]

    pick_in = by_type["PICK_IN"]

    dispatch = by_type["DISPATCH"]

    quantity = shipment.shipped_quantity

    for movement in group:
        if movement.market_code != shipment.market_code:
            raise ValueError("outbound movement market does not match shipment")

        if movement.warehouse_id != shipment.warehouse_id:
            raise ValueError("outbound movement warehouse does not match shipment")

        if movement.assortment_id != shipment.assortment_id:
            raise ValueError("outbound movement assortment does not match shipment")

        if movement.product_id != shipment.product_id:
            raise ValueError("outbound movement product does not match shipment")

        if movement.sku != shipment.sku:
            raise ValueError("outbound movement SKU does not match shipment")

        if movement.inventory_location_id not in locations_by_id:
            raise ValueError("outbound movement references unknown inventory location")

    bulk_location = locations_by_id[pick_out.inventory_location_id]

    pick_in_location = locations_by_id[pick_in.inventory_location_id]

    dispatch_location = locations_by_id[dispatch.inventory_location_id]

    if bulk_location.location_type != "BULK_STORAGE":
        raise ValueError("PICK_OUT must leave BULK_STORAGE")

    if pick_in_location.location_type != "PICK_FACE":
        raise ValueError("PICK_IN must target PICK_FACE")

    if dispatch_location.location_type != "PICK_FACE":
        raise ValueError("DISPATCH must leave PICK_FACE")

    if pick_in.inventory_location_id != dispatch.inventory_location_id:
        raise ValueError("DISPATCH must leave the same PICK_FACE used by PICK_IN")

    if pick_out.quantity_delta != -quantity:
        raise ValueError("PICK_OUT quantity does not match shipment")

    if pick_in.quantity_delta != quantity:
        raise ValueError("PICK_IN quantity does not match shipment")

    if dispatch.quantity_delta != -quantity:
        raise ValueError("DISPATCH quantity does not match shipment")

    if pick_out.event_date != shipment.picked_date or pick_in.event_date != shipment.picked_date:
        raise ValueError("pick movements do not match shipment picked_date")

    if dispatch.event_date != shipment.dispatched_date:
        raise ValueError("DISPATCH date does not match shipment dispatched_date")

    group_net = sum(movement.quantity_delta for movement in group)

    if group_net != -quantity:
        raise ValueError("outbound movement group net does not equal shipped quantity")
