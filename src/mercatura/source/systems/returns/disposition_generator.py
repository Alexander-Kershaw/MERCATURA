import hashlib
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from mercatura.source.systems.returns.disposition_model import (
    ReturnDisposition,
    ReturnDispositionType,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
)
from mercatura.source.systems.wms.inventory_model import InventoryMovement, InventoryMovementType
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)


def generate_return_dispositions(
    customer_returns: tuple[
        CustomerReturn,
        ...,
    ],
    locations: tuple[
        InventoryLocation,
        ...,
    ],
) -> tuple[
    tuple[
        ReturnDisposition,
        ...,
    ],
    tuple[
        InventoryMovement,
        ...,
    ],
]:

    returns_locations = _index_locations(
        locations,
        "RETURNS",
    )

    bulk_locations = _index_locations(
        locations,
        "BULK_STORAGE",
    )

    quarantine_locations = _index_locations(
        locations,
        "QUARANTINE",
    )

    dispositions: list[ReturnDisposition] = []

    movements: list[InventoryMovement] = []

    ordered_returns = sorted(
        customer_returns,
        key=lambda customer_return: (
            customer_return.return_date,
            customer_return.order_id,
            customer_return.order_item_id,
            customer_return.return_id,
        ),
    )

    for customer_return in ordered_returns:
        if customer_return.return_status != "RECEIVED":
            raise ValueError("return disposition requires RECEIVED customer returns")

        if customer_return.returned_quantity <= 0:
            raise ValueError("return disposition quantity must be positive")

        returns_location = _required_location(
            returns_locations,
            customer_return.warehouse_id,
            "RETURNS",
        )

        disposition_type = _choose_disposition(customer_return)

        disposition_date = customer_return.return_date + timedelta(
            days=_inspection_delay_days(customer_return.return_id)
        )

        disposition_id = _stable_id(
            prefix="dsp",
            value=customer_return.return_id,
        )

        disposition = ReturnDisposition(
            disposition_id=(disposition_id),
            return_id=(customer_return.return_id),
            shipment_id=(customer_return.shipment_id),
            order_id=(customer_return.order_id),
            order_item_id=(customer_return.order_item_id),
            market_code=(customer_return.market_code),
            warehouse_assortment_id=(customer_return.warehouse_assortment_id),
            warehouse_id=(customer_return.warehouse_id),
            warehouse_code=(customer_return.warehouse_code),
            assortment_id=(customer_return.assortment_id),
            product_id=(customer_return.product_id),
            sku=customer_return.sku,
            disposition_quantity=(customer_return.returned_quantity),
            disposition_type=(disposition_type),
            disposition_date=(disposition_date),
        )

        disposition_movements = _build_movements(
            disposition,
            returns_location,
            bulk_locations,
            quarantine_locations,
        )

        dispositions.append(disposition)

        movements.extend(disposition_movements)

    return (
        tuple(dispositions),
        tuple(movements),
    )


def _build_movements(
    disposition: ReturnDisposition,
    returns_location: InventoryLocation,
    bulk_locations: dict[
        str,
        InventoryLocation,
    ],
    quarantine_locations: dict[
        str,
        InventoryLocation,
    ],
) -> tuple[
    InventoryMovement,
    ...,
]:
    quantity = disposition.disposition_quantity

    if disposition.disposition_type == "WRITE_OFF":
        return (
            _movement(
                disposition=disposition,
                movement_type="WRITE_OFF",
                sequence=1,
                location=returns_location,
                quantity_delta=-quantity,
            ),
        )

    transfer_out = _movement(
        disposition=disposition,
        movement_type=("RETURN_TRANSFER_OUT"),
        sequence=1,
        location=returns_location,
        quantity_delta=-quantity,
    )

    if disposition.disposition_type == "RESTOCK":
        destination = _required_location(
            bulk_locations,
            disposition.warehouse_id,
            "BULK_STORAGE",
        )

        transfer_in = _movement(
            disposition=disposition,
            movement_type="RESTOCK_IN",
            sequence=2,
            location=destination,
            quantity_delta=quantity,
        )

        return (
            transfer_out,
            transfer_in,
        )

    if disposition.disposition_type == "QUARANTINE":
        destination = _required_location(
            quarantine_locations,
            disposition.warehouse_id,
            "QUARANTINE",
        )

        transfer_in = _movement(
            disposition=disposition,
            movement_type="QUARANTINE_IN",
            sequence=2,
            location=destination,
            quantity_delta=quantity,
        )

        return (
            transfer_out,
            transfer_in,
        )

    raise ValueError("unknown return disposition type")


def _movement(
    *,
    disposition: ReturnDisposition,
    movement_type: InventoryMovementType,
    sequence: int,
    location: InventoryLocation,
    quantity_delta: int,
) -> InventoryMovement:
    return InventoryMovement(
        movement_id=_stable_id(
            prefix="imv",
            value=(f"{disposition.disposition_id}:{movement_type}"),
        ),
        movement_group_id=_stable_id(
            prefix="img",
            value=(disposition.disposition_id),
        ),
        movement_sequence=sequence,
        movement_type=movement_type,
        source_reference_type=("RETURN_DISPOSITION"),
        source_reference_id=(disposition.disposition_id),
        market_code=(disposition.market_code),
        warehouse_id=(disposition.warehouse_id),
        warehouse_code=(disposition.warehouse_code),
        inventory_location_id=(location.inventory_location_id),
        location_code=(location.location_code),
        assortment_id=(disposition.assortment_id),
        product_id=(disposition.product_id),
        sku=disposition.sku,
        quantity_delta=quantity_delta,
        event_date=(disposition.disposition_date),
    )


def _choose_disposition(
    customer_return: CustomerReturn,
) -> ReturnDispositionType:

    roll = _unit_interval(
        customer_return.return_id,
        "disposition",
    )

    reason = customer_return.return_reason

    if reason == "UNWANTED":
        if roll < 0.88:
            return "RESTOCK"
        if roll < 0.97:
            return "QUARANTINE"
        return "WRITE_OFF"

    if reason == "WRONG_SIZE_OR_FIT":
        if roll < 0.92:
            return "RESTOCK"
        if roll < 0.98:
            return "QUARANTINE"
        return "WRITE_OFF"

    if reason == "DAMAGED":
        if roll < 0.20:
            return "RESTOCK"
        if roll < 0.70:
            return "QUARANTINE"
        return "WRITE_OFF"

    if reason == "FAULTY":
        if roll < 0.05:
            return "RESTOCK"
        if roll < 0.70:
            return "QUARANTINE"
        return "WRITE_OFF"

    if reason == "NOT_AS_DESCRIBED":
        if roll < 0.60:
            return "RESTOCK"
        if roll < 0.90:
            return "QUARANTINE"
        return "WRITE_OFF"

    raise ValueError("unknown customer return reason")


def _inspection_delay_days(
    return_id: str,
) -> int:

    roll = _unit_interval(
        return_id,
        "inspection-delay",
    )

    return min(
        int(roll * 3),
        2,
    )


def _index_locations(
    locations: tuple[
        InventoryLocation,
        ...,
    ],
    location_type: str,
) -> dict[
    str,
    InventoryLocation,
]:
    result: dict[
        str,
        InventoryLocation,
    ] = {}

    for location in locations:
        if location.location_type != location_type:
            continue

        if location.warehouse_id in result:
            raise ValueError(f"warehouse has multiple {location_type} locations")

        result[location.warehouse_id] = location

    return result


def _required_location(
    locations: dict[
        str,
        InventoryLocation,
    ],
    warehouse_id: str,
    location_type: str,
) -> InventoryLocation:
    location = locations.get(warehouse_id)

    if location is None:
        raise ValueError(f"warehouse has no {location_type} location")

    return location


def _unit_interval(
    value: str,
    label: str,
) -> float:
    digest = hashlib.sha256((f"{value}:{label}").encode()).digest()

    integer = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )

    return integer / float(2**64)


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
