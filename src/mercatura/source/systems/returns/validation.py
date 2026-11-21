from collections import Counter

from mercatura.source.systems.fulfilment.shipment_model import (
    OutboundShipment,
)
from mercatura.source.systems.returns.model import (
    RETURN_REASONS,
    RETURN_STATUSES,
    CustomerReturn,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)


def validate_customer_returns(
    returns: tuple[
        CustomerReturn,
        ...,
    ],
    return_movements: tuple[
        InventoryMovement,
        ...,
    ],
    shipments: tuple[
        OutboundShipment,
        ...,
    ],
    locations: tuple[
        InventoryLocation,
        ...,
    ],
) -> None:
    shipments_by_id = {shipment.shipment_id: shipment for shipment in shipments}

    locations_by_id = {location.inventory_location_id: location for location in locations}

    _validate_unique_ids(
        returns,
        return_movements,
    )

    movements_by_return = {movement.source_reference_id: movement for movement in return_movements}

    if len(movements_by_return) != len(return_movements):
        raise ValueError("customer return must produce exactly one return movement")

    if set(movements_by_return) != {row.return_id for row in returns}:
        raise ValueError("return movements do not cover every customer return")

    return_counts = Counter(row.shipment_id for row in returns)

    for (
        shipment_id,
        count,
    ) in return_counts.items():
        if count > 1:
            raise ValueError("shipment produced more than one customer return")

        if shipment_id not in shipments_by_id:
            raise ValueError("customer return references unknown shipment")

    for customer_return in returns:
        shipment = shipments_by_id[customer_return.shipment_id]

        movement = movements_by_return[customer_return.return_id]

        _validate_return(
            customer_return,
            shipment,
        )

        _validate_return_movement(
            customer_return,
            movement,
            locations_by_id,
        )


def _validate_unique_ids(
    returns: tuple[
        CustomerReturn,
        ...,
    ],
    movements: tuple[
        InventoryMovement,
        ...,
    ],
) -> None:
    return_ids = [row.return_id for row in returns]

    movement_ids = [movement.movement_id for movement in movements]

    if len(return_ids) != len(set(return_ids)):
        raise ValueError("duplicate return_id detected")

    if len(movement_ids) != len(set(movement_ids)):
        raise ValueError("duplicate return movement_id detected")


def _validate_return(
    customer_return: CustomerReturn,
    shipment: OutboundShipment,
) -> None:
    if customer_return.return_status not in RETURN_STATUSES:
        raise ValueError("invalid customer return status")

    if customer_return.return_reason not in RETURN_REASONS:
        raise ValueError("invalid customer return reason")

    if customer_return.returned_quantity <= 0:
        raise ValueError("returned quantity must be positive")

    if customer_return.returned_quantity > shipment.shipped_quantity:
        raise ValueError("returned quantity exceeds shipped quantity")

    if customer_return.return_date < shipment.dispatched_date:
        raise ValueError("return cannot occur before shipment dispatch")

    fields = (
        (
            customer_return.reservation_id,
            shipment.reservation_id,
            "reservation",
        ),
        (
            customer_return.allocation_id,
            shipment.allocation_id,
            "allocation",
        ),
        (
            customer_return.fulfilment_request_id,
            shipment.fulfilment_request_id,
            "fulfilment request",
        ),
        (
            customer_return.order_id,
            shipment.order_id,
            "order",
        ),
        (
            customer_return.order_item_id,
            shipment.order_item_id,
            "order item",
        ),
        (
            customer_return.market_code,
            shipment.market_code,
            "market",
        ),
        (
            customer_return.warehouse_id,
            shipment.warehouse_id,
            "warehouse",
        ),
        (
            customer_return.assortment_id,
            shipment.assortment_id,
            "assortment",
        ),
        (
            customer_return.product_id,
            shipment.product_id,
            "product",
        ),
        (
            customer_return.sku,
            shipment.sku,
            "SKU",
        ),
    )

    for actual, expected, label in fields:
        if actual != expected:
            raise ValueError(f"customer return {label} does not match shipment")


def _validate_return_movement(
    customer_return: CustomerReturn,
    movement: InventoryMovement,
    locations_by_id: dict[
        str,
        InventoryLocation,
    ],
) -> None:
    if movement.movement_type != "RETURN_RECEIPT":
        raise ValueError("customer return must produce RETURN_RECEIPT movement")

    if movement.source_reference_type != "CUSTOMER_RETURN":
        raise ValueError("return movement has invalid source reference type")

    if movement.quantity_delta != customer_return.returned_quantity:
        raise ValueError("return movement quantity does not match returned quantity")

    if movement.event_date != customer_return.return_date:
        raise ValueError("return movement date does not match return date")

    location = locations_by_id.get(movement.inventory_location_id)

    if location is None:
        raise ValueError("return movement references unknown inventory location")

    if location.location_type != "RETURNS":
        raise ValueError("RETURN_RECEIPT must target RETURNS location")

    if movement.warehouse_id != customer_return.warehouse_id:
        raise ValueError("return movement warehouse does not match customer return")

    if location.warehouse_id != customer_return.warehouse_id:
        raise ValueError("RETURNS location belongs to wrong warehouse")

    if (
        movement.assortment_id != customer_return.assortment_id
        or movement.product_id != customer_return.product_id
        or movement.sku != customer_return.sku
    ):
        raise ValueError("return movement product metadata does not match customer return")
