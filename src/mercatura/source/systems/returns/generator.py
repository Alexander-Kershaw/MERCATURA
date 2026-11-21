import hashlib
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from mercatura.source.systems.fulfilment.shipment_model import (
    OutboundShipment,
)
from mercatura.source.systems.returns.config import (
    DEFAULT_RETURNS_CONFIG,
    ReturnsSimulationConfig,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
    ReturnReason,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)


def generate_customer_returns(
    shipments: tuple[
        OutboundShipment,
        ...,
    ],
    locations: tuple[
        InventoryLocation,
        ...,
    ],
    *,
    config: ReturnsSimulationConfig = (DEFAULT_RETURNS_CONFIG),
) -> tuple[
    tuple[
        CustomerReturn,
        ...,
    ],
    tuple[
        InventoryMovement,
        ...,
    ],
]:
    return_locations = _return_locations_by_warehouse(locations)

    returns: list[CustomerReturn] = []

    movements: list[InventoryMovement] = []

    ordered_shipments = sorted(
        shipments,
        key=lambda shipment: (
            shipment.dispatched_date,
            shipment.order_id,
            shipment.order_item_id,
            shipment.shipment_id,
        ),
    )

    for shipment in ordered_shipments:
        if shipment.shipment_status != "DISPATCHED":
            continue

        if (
            _unit_interval(
                shipment.shipment_id,
                "return-decision",
            )
            >= config.return_probability
        ):
            continue

        return_location = return_locations.get(shipment.warehouse_id)

        if return_location is None:
            raise ValueError("shipment warehouse has no RETURNS location")

        returned_quantity = _returned_quantity(
            shipment,
            config,
        )

        delay_days = _return_delay_days(
            shipment,
            config,
        )

        return_date = shipment.dispatched_date + timedelta(days=delay_days)

        return_id = _stable_id(
            prefix="ret",
            value=shipment.shipment_id,
        )

        reason = _return_reason(shipment.shipment_id)

        customer_return = CustomerReturn(
            return_id=return_id,
            shipment_id=(shipment.shipment_id),
            reservation_id=(shipment.reservation_id),
            allocation_id=(shipment.allocation_id),
            fulfilment_request_id=(shipment.fulfilment_request_id),
            order_id=(shipment.order_id),
            order_item_id=(shipment.order_item_id),
            market_code=(shipment.market_code),
            warehouse_assortment_id=(shipment.warehouse_assortment_id),
            warehouse_id=(shipment.warehouse_id),
            warehouse_code=(shipment.warehouse_code),
            assortment_id=(shipment.assortment_id),
            product_id=(shipment.product_id),
            sku=shipment.sku,
            returned_quantity=(returned_quantity),
            return_reason=reason,
            return_status="RECEIVED",
            return_date=return_date,
        )

        movement = InventoryMovement(
            movement_id=_stable_id(
                prefix="imv",
                value=(f"{return_id}:RETURN_RECEIPT"),
            ),
            movement_group_id=_stable_id(
                prefix="img",
                value=return_id,
            ),
            movement_sequence=1,
            movement_type=("RETURN_RECEIPT"),
            source_reference_type=("CUSTOMER_RETURN"),
            source_reference_id=(return_id),
            market_code=(shipment.market_code),
            warehouse_id=(shipment.warehouse_id),
            warehouse_code=(shipment.warehouse_code),
            inventory_location_id=(return_location.inventory_location_id),
            location_code=(return_location.location_code),
            assortment_id=(shipment.assortment_id),
            product_id=(shipment.product_id),
            sku=shipment.sku,
            quantity_delta=(returned_quantity),
            event_date=(return_date),
        )

        returns.append(customer_return)

        movements.append(movement)

    return (
        tuple(returns),
        tuple(movements),
    )


def _return_locations_by_warehouse(
    locations: tuple[
        InventoryLocation,
        ...,
    ],
) -> dict[
    str,
    InventoryLocation,
]:
    result: dict[
        str,
        InventoryLocation,
    ] = {}

    for location in locations:
        if location.location_type != "RETURNS":
            continue

        if location.warehouse_id in result:
            raise ValueError("warehouse has multiple RETURNS locations")

        result[location.warehouse_id] = location

    return result


def _returned_quantity(
    shipment: OutboundShipment,
    config: ReturnsSimulationConfig,
) -> int:
    shipped_quantity = shipment.shipped_quantity

    if shipped_quantity <= 0:
        raise ValueError("shipment quantity must be positive")

    if shipped_quantity == 1:
        return 1

    partial = (
        _unit_interval(
            shipment.shipment_id,
            "partial-return",
        )
        < config.partial_return_probability
    )

    if not partial:
        return shipped_quantity

    available_partial_values = shipped_quantity - 1

    roll = _unit_interval(
        shipment.shipment_id,
        "partial-return-quantity",
    )

    quantity = 1 + int(roll * available_partial_values)

    return min(
        quantity,
        shipped_quantity - 1,
    )


def _return_delay_days(
    shipment: OutboundShipment,
    config: ReturnsSimulationConfig,
) -> int:
    minimum = config.minimum_return_delay_days

    maximum = config.maximum_return_delay_days

    span = maximum - minimum + 1

    roll = _unit_interval(
        shipment.shipment_id,
        "return-delay",
    )

    offset = int(roll * span)

    return min(
        minimum + offset,
        maximum,
    )


def _return_reason(
    shipment_id: str,
) -> ReturnReason:
    roll = _unit_interval(
        shipment_id,
        "return-reason",
    )

    if roll < 0.40:
        return "UNWANTED"

    if roll < 0.62:
        return "WRONG_SIZE_OR_FIT"

    if roll < 0.77:
        return "DAMAGED"

    if roll < 0.90:
        return "FAULTY"

    return "NOT_AS_DESCRIBED"


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
