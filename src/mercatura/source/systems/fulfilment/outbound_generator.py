from collections import defaultdict
from dataclasses import replace
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

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


def generate_outbound_fulfilment(
    reservations: tuple[
        InventoryReservation,
        ...,
    ],
    inventory_movements: tuple[
        InventoryMovement,
        ...,
    ],
    locations: tuple[
        InventoryLocation,
        ...,
    ],
) -> tuple[
    tuple[
        InventoryReservation,
        ...,
    ],
    tuple[
        OutboundShipment,
        ...,
    ],
    tuple[
        InventoryMovement,
        ...,
    ],
]:

    locations_by_id = {location.inventory_location_id: location for location in locations}

    bulk_locations = _index_locations(
        locations,
        location_type="BULK_STORAGE",
    )

    pick_face_locations = _index_locations(
        locations,
        location_type="PICK_FACE",
    )

    relevant_movements = sorted(
        inventory_movements,
        key=lambda movement: (
            movement.event_date,
            movement.movement_sequence,
            movement.movement_id,
        ),
    )

    bulk_balance: dict[
        tuple[
            str,
            str,
        ],
        int,
    ] = defaultdict(int)

    movement_index = 0

    ordered_reservations = sorted(
        reservations,
        key=lambda reservation: (
            reservation.reserved_date,
            reservation.order_id,
            reservation.order_item_id,
            reservation.allocation_id,
            reservation.reservation_id,
        ),
    )

    consumed_reservations: list[InventoryReservation] = []

    shipments: list[OutboundShipment] = []

    outbound_movements: list[InventoryMovement] = []

    for reservation in ordered_reservations:
        if reservation.reservation_status != "RESERVED":
            raise ValueError("outbound fulfilment requires RESERVED reservations")

        if reservation.reserved_quantity <= 0:
            raise ValueError("reservation quantity must be positive")

        while (
            movement_index < len(relevant_movements)
            and relevant_movements[movement_index].event_date <= reservation.reserved_date
        ):
            movement = relevant_movements[movement_index]

            location = locations_by_id.get(movement.inventory_location_id)

            if location is not None and location.location_type == "BULK_STORAGE":
                key = (
                    movement.warehouse_id,
                    movement.assortment_id,
                )

                bulk_balance[key] += movement.quantity_delta

            movement_index += 1

        bulk_location = _single_warehouse_location(
            warehouse_id=(reservation.warehouse_id),
            locations_by_warehouse=(bulk_locations),
            location_type=("BULK_STORAGE"),
        )

        pick_face_location = _single_warehouse_location(
            warehouse_id=(reservation.warehouse_id),
            locations_by_warehouse=(pick_face_locations),
            location_type="PICK_FACE",
        )

        inventory_key = (
            reservation.warehouse_id,
            reservation.assortment_id,
        )

        available_quantity = bulk_balance[inventory_key]

        required_quantity = reservation.reserved_quantity

        if available_quantity < required_quantity:
            raise ValueError("reservation exceeds available BULK_STORAGE inventory")

        picked_date = reservation.reserved_date

        dispatched_date = picked_date + timedelta(days=1)

        shipment_id = _stable_id(
            prefix="shp",
            value=(reservation.reservation_id),
        )

        movement_group_id = _stable_id(
            prefix="img",
            value=shipment_id,
        )

        shipment = OutboundShipment(
            shipment_id=shipment_id,
            reservation_id=(reservation.reservation_id),
            allocation_id=(reservation.allocation_id),
            fulfilment_request_id=(reservation.fulfilment_request_id),
            order_id=(reservation.order_id),
            order_item_id=(reservation.order_item_id),
            market_code=(reservation.market_code),
            warehouse_assortment_id=(reservation.warehouse_assortment_id),
            warehouse_id=(reservation.warehouse_id),
            warehouse_code=(reservation.warehouse_code),
            assortment_id=(reservation.assortment_id),
            product_id=(reservation.product_id),
            sku=reservation.sku,
            shipped_quantity=(required_quantity),
            picked_date=(picked_date),
            dispatched_date=(dispatched_date),
            shipment_status=("DISPATCHED"),
        )

        pick_out = InventoryMovement(
            movement_id=(
                _movement_id(
                    shipment_id,
                    "PICK_OUT",
                )
            ),
            movement_group_id=(movement_group_id),
            movement_sequence=1,
            movement_type="PICK_OUT",
            source_reference_type=("FULFILMENT_SHIPMENT"),
            source_reference_id=(shipment_id),
            market_code=(reservation.market_code),
            warehouse_id=(reservation.warehouse_id),
            warehouse_code=(reservation.warehouse_code),
            inventory_location_id=(bulk_location.inventory_location_id),
            location_code=(bulk_location.location_code),
            assortment_id=(reservation.assortment_id),
            product_id=(reservation.product_id),
            sku=reservation.sku,
            quantity_delta=(-required_quantity),
            event_date=(picked_date),
        )

        pick_in = InventoryMovement(
            movement_id=(
                _movement_id(
                    shipment_id,
                    "PICK_IN",
                )
            ),
            movement_group_id=(movement_group_id),
            movement_sequence=2,
            movement_type="PICK_IN",
            source_reference_type=("FULFILMENT_SHIPMENT"),
            source_reference_id=(shipment_id),
            market_code=(reservation.market_code),
            warehouse_id=(reservation.warehouse_id),
            warehouse_code=(reservation.warehouse_code),
            inventory_location_id=(pick_face_location.inventory_location_id),
            location_code=(pick_face_location.location_code),
            assortment_id=(reservation.assortment_id),
            product_id=(reservation.product_id),
            sku=reservation.sku,
            quantity_delta=(required_quantity),
            event_date=(picked_date),
        )

        dispatch = InventoryMovement(
            movement_id=(
                _movement_id(
                    shipment_id,
                    "DISPATCH",
                )
            ),
            movement_group_id=(movement_group_id),
            movement_sequence=3,
            movement_type="DISPATCH",
            source_reference_type=("FULFILMENT_SHIPMENT"),
            source_reference_id=(shipment_id),
            market_code=(reservation.market_code),
            warehouse_id=(reservation.warehouse_id),
            warehouse_code=(reservation.warehouse_code),
            inventory_location_id=(pick_face_location.inventory_location_id),
            location_code=(pick_face_location.location_code),
            assortment_id=(reservation.assortment_id),
            product_id=(reservation.product_id),
            sku=reservation.sku,
            quantity_delta=(-required_quantity),
            event_date=(dispatched_date),
        )

        bulk_balance[inventory_key] -= required_quantity

        consumed_reservation = replace(
            reservation,
            reservation_status=("CONSUMED"),
            consumed_date=(dispatched_date),
            released_date=None,
        )

        shipments.append(shipment)

        outbound_movements.extend(
            (
                pick_out,
                pick_in,
                dispatch,
            )
        )

        consumed_reservations.append(consumed_reservation)

    return (
        tuple(consumed_reservations),
        tuple(shipments),
        tuple(outbound_movements),
    )


def _index_locations(
    locations: tuple[
        InventoryLocation,
        ...,
    ],
    *,
    location_type: str,
) -> dict[
    str,
    list[InventoryLocation],
]:
    result: dict[
        str,
        list[InventoryLocation],
    ] = defaultdict(list)

    for location in locations:
        if location.location_type == location_type:
            result[location.warehouse_id].append(location)

    for rows in result.values():
        rows.sort(key=lambda location: location.location_code)

    return dict(result)


def _single_warehouse_location(
    *,
    warehouse_id: str,
    locations_by_warehouse: dict[
        str,
        list[InventoryLocation],
    ],
    location_type: str,
) -> InventoryLocation:
    candidates = locations_by_warehouse.get(
        warehouse_id,
        [],
    )

    if len(candidates) != 1:
        raise ValueError(f"warehouse {warehouse_id} must have exactly one {location_type} location")

    return candidates[0]


def _stable_id(
    *,
    prefix: str,
    value: str,
) -> str:
    generated = uuid5(
        NAMESPACE_URL,
        (f"mercatura:{prefix}:{value}"),
    )

    return f"{prefix}_{generated.hex[:20]}"


def _movement_id(
    shipment_id: str,
    movement_type: str,
) -> str:
    return _stable_id(
        prefix="imv",
        value=(f"{shipment_id}:{movement_type}"),
    )
