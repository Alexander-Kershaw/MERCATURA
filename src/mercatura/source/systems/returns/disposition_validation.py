from collections import Counter, defaultdict

from mercatura.source.systems.returns.disposition_model import (
    RETURN_DISPOSITION_TYPES,
    ReturnDisposition,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)


def validate_return_dispositions(
    dispositions: tuple[
        ReturnDisposition,
        ...,
    ],
    customer_returns: tuple[
        CustomerReturn,
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
    returns_by_id = {
        customer_return.return_id: customer_return for customer_return in customer_returns
    }

    locations_by_id = {location.inventory_location_id: location for location in locations}

    _validate_unique_ids(
        dispositions,
        movements,
    )

    disposition_counts = Counter(disposition.return_id for disposition in dispositions)

    if set(disposition_counts) != set(returns_by_id):
        raise ValueError("dispositions do not cover every customer return")

    if any(count != 1 for count in disposition_counts.values()):
        raise ValueError("each customer return must have exactly one disposition")

    movements_by_disposition: dict[
        str,
        list[InventoryMovement],
    ] = defaultdict(list)

    for movement in movements:
        if movement.source_reference_type != "RETURN_DISPOSITION":
            raise ValueError("return disposition movement has invalid source type")

        movements_by_disposition[movement.source_reference_id].append(movement)

    if set(movements_by_disposition) != {
        disposition.disposition_id for disposition in dispositions
    }:
        raise ValueError("movement groups do not cover every return disposition")

    for disposition in dispositions:
        customer_return = returns_by_id[disposition.return_id]

        _validate_disposition(
            disposition,
            customer_return,
        )

        _validate_movements(
            disposition,
            movements_by_disposition[disposition.disposition_id],
            locations_by_id,
        )


def _validate_unique_ids(
    dispositions: tuple[
        ReturnDisposition,
        ...,
    ],
    movements: tuple[
        InventoryMovement,
        ...,
    ],
) -> None:
    disposition_ids = [disposition.disposition_id for disposition in dispositions]

    movement_ids = [movement.movement_id for movement in movements]

    if len(disposition_ids) != len(set(disposition_ids)):
        raise ValueError("duplicate disposition_id detected")

    if len(movement_ids) != len(set(movement_ids)):
        raise ValueError("duplicate disposition movement_id detected")


def _validate_disposition(
    disposition: ReturnDisposition,
    customer_return: CustomerReturn,
) -> None:
    if disposition.disposition_type not in RETURN_DISPOSITION_TYPES:
        raise ValueError("invalid return disposition type")

    if disposition.disposition_quantity <= 0:
        raise ValueError("disposition quantity must be positive")

    if disposition.disposition_quantity != customer_return.returned_quantity:
        raise ValueError("disposition quantity does not match returned quantity")

    if disposition.disposition_date < customer_return.return_date:
        raise ValueError("disposition cannot occur before customer return receipt")

    comparisons = (
        (
            disposition.shipment_id,
            customer_return.shipment_id,
            "shipment",
        ),
        (
            disposition.order_id,
            customer_return.order_id,
            "order",
        ),
        (
            disposition.order_item_id,
            customer_return.order_item_id,
            "order item",
        ),
        (
            disposition.market_code,
            customer_return.market_code,
            "market",
        ),
        (
            disposition.warehouse_assortment_id,
            customer_return.warehouse_assortment_id,
            "warehouse assortment",
        ),
        (
            disposition.warehouse_id,
            customer_return.warehouse_id,
            "warehouse",
        ),
        (
            disposition.warehouse_code,
            customer_return.warehouse_code,
            "warehouse code",
        ),
        (
            disposition.assortment_id,
            customer_return.assortment_id,
            "assortment",
        ),
        (
            disposition.product_id,
            customer_return.product_id,
            "product",
        ),
        (
            disposition.sku,
            customer_return.sku,
            "SKU",
        ),
    )

    for actual, expected, label in comparisons:
        if actual != expected:
            raise ValueError(f"return disposition {label} does not match customer return")


def _validate_movements(
    disposition: ReturnDisposition,
    movements: list[InventoryMovement],
    locations_by_id: dict[
        str,
        InventoryLocation,
    ],
) -> None:
    ordered = sorted(
        movements,
        key=lambda movement: movement.movement_sequence,
    )

    quantity = disposition.disposition_quantity

    if disposition.disposition_type == "WRITE_OFF":
        if len(ordered) != 1:
            raise ValueError("WRITE_OFF must produce exactly one inventory movement")

        movement = ordered[0]

        if movement.movement_type != "WRITE_OFF" or movement.quantity_delta != -quantity:
            raise ValueError("invalid WRITE_OFF movement")

        location = locations_by_id[movement.inventory_location_id]

        if location.location_type != "RETURNS":
            raise ValueError("WRITE_OFF must leave RETURNS location")

        return

    if len(ordered) != 2:
        raise ValueError("transfer disposition must produce exactly two inventory movements")

    transfer_out = ordered[0]
    transfer_in = ordered[1]

    if (
        transfer_out.movement_type != "RETURN_TRANSFER_OUT"
        or transfer_out.quantity_delta != -quantity
    ):
        raise ValueError("invalid RETURN_TRANSFER_OUT movement")

    source_location = locations_by_id[transfer_out.inventory_location_id]

    if source_location.location_type != "RETURNS":
        raise ValueError("RETURN_TRANSFER_OUT must leave RETURNS location")

    if disposition.disposition_type == "RESTOCK":
        expected_type = "RESTOCK_IN"
        expected_location = "BULK_STORAGE"

    else:
        expected_type = "QUARANTINE_IN"
        expected_location = "QUARANTINE"

    if transfer_in.movement_type != expected_type or transfer_in.quantity_delta != quantity:
        raise ValueError("invalid disposition inbound movement")

    destination_location = locations_by_id[transfer_in.inventory_location_id]

    if destination_location.location_type != expected_location:
        raise ValueError("disposition movement targets wrong destination location")

    if sum(movement.quantity_delta for movement in ordered) != 0:
        raise ValueError("return transfer movements must net to zero")
