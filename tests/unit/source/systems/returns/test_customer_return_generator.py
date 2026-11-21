from dataclasses import dataclass, replace
from datetime import date
from typing import cast

import pytest

from mercatura.source.systems.fulfilment.shipment_model import (
    OutboundShipment,
)
from mercatura.source.systems.returns.config import (
    ReturnsSimulationConfig,
)
from mercatura.source.systems.returns.generator import (
    generate_customer_returns,
)
from mercatura.source.systems.returns.validation import (
    validate_customer_returns,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)

DISPATCHED_DATE = date(
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
    inventory_location_id: str = "retloc_001",
    location_code: str = "GB-WH-001-RET",
    warehouse_id: str = "wh_001",
    location_type: str = "RETURNS",
) -> InventoryLocation:
    return cast(
        InventoryLocation,
        _LocationStub(
            inventory_location_id=(inventory_location_id),
            location_code=location_code,
            warehouse_id=warehouse_id,
            location_type=location_type,
        ),
    )


def _shipment(
    *,
    shipment_id: str = "shp_001",
    reservation_id: str = "res_001",
    allocation_id: str = "alloc_001",
    fulfilment_request_id: str = "req_001",
    order_id: str = "ord_001",
    order_item_id: str = "itm_001",
    warehouse_id: str = "wh_001",
    warehouse_code: str = "GB-WH-001",
    shipped_quantity: int = 4,
    dispatched_date: date = DISPATCHED_DATE,
) -> OutboundShipment:
    return OutboundShipment(
        shipment_id=shipment_id,
        reservation_id=reservation_id,
        allocation_id=allocation_id,
        fulfilment_request_id=(fulfilment_request_id),
        order_id=order_id,
        order_item_id=order_item_id,
        market_code="GB",
        warehouse_assortment_id="was_001",
        warehouse_id=warehouse_id,
        warehouse_code=warehouse_code,
        assortment_id="ast_001",
        product_id="prd_001",
        sku="SKU-001",
        shipped_quantity=shipped_quantity,
        picked_date=date(
            2024,
            6,
            14,
        ),
        dispatched_date=dispatched_date,
        shipment_status="DISPATCHED",
    )


def _config(
    *,
    return_probability: float = 1.0,
    partial_return_probability: float = 0.0,
    minimum_return_delay_days: int = 2,
    maximum_return_delay_days: int = 2,
) -> ReturnsSimulationConfig:
    return ReturnsSimulationConfig(
        return_probability=(return_probability),
        partial_return_probability=(partial_return_probability),
        minimum_return_delay_days=(minimum_return_delay_days),
        maximum_return_delay_days=(maximum_return_delay_days),
    )


def test_return_probability_zero_creates_no_returns() -> None:
    customer_returns, movements = generate_customer_returns(
        (_shipment(),),
        (_location(),),
        config=_config(
            return_probability=0.0,
        ),
    )

    assert customer_returns == ()
    assert movements == ()


def test_return_probability_one_creates_return() -> None:
    customer_returns, movements = generate_customer_returns(
        (_shipment(),),
        (_location(),),
        config=_config(),
    )

    assert len(customer_returns) == 1
    assert len(movements) == 1


def test_full_return_matches_shipped_quantity() -> None:
    customer_returns, _ = generate_customer_returns(
        (
            _shipment(
                shipped_quantity=4,
            ),
        ),
        (_location(),),
        config=_config(
            partial_return_probability=0.0,
        ),
    )

    assert customer_returns[0].returned_quantity == 4


def test_partial_return_is_less_than_shipped_quantity() -> None:
    customer_returns, _ = generate_customer_returns(
        (
            _shipment(
                shipped_quantity=5,
            ),
        ),
        (_location(),),
        config=_config(
            partial_return_probability=1.0,
        ),
    )

    returned_quantity = customer_returns[0].returned_quantity

    assert returned_quantity >= 1
    assert returned_quantity < 5


def test_single_unit_shipment_returns_single_unit() -> None:
    customer_returns, _ = generate_customer_returns(
        (
            _shipment(
                shipped_quantity=1,
            ),
        ),
        (_location(),),
        config=_config(
            partial_return_probability=1.0,
        ),
    )

    assert customer_returns[0].returned_quantity == 1


def test_return_occurs_after_dispatch() -> None:
    customer_returns, _ = generate_customer_returns(
        (_shipment(),),
        (_location(),),
        config=_config(
            minimum_return_delay_days=5,
            maximum_return_delay_days=5,
        ),
    )

    customer_return = customer_returns[0]

    assert customer_return.return_date == date(
        2024,
        6,
        20,
    )


def test_return_delay_is_within_configured_bounds() -> None:
    customer_returns, _ = generate_customer_returns(
        (_shipment(),),
        (_location(),),
        config=_config(
            minimum_return_delay_days=3,
            maximum_return_delay_days=14,
        ),
    )

    delay = (customer_returns[0].return_date - DISPATCHED_DATE).days

    assert 3 <= delay <= 14


def test_return_metadata_matches_shipment() -> None:
    shipment = _shipment()

    customer_return = generate_customer_returns(
        (shipment,),
        (_location(),),
        config=_config(),
    )[0][0]

    assert customer_return.shipment_id == shipment.shipment_id

    assert customer_return.reservation_id == shipment.reservation_id

    assert customer_return.allocation_id == shipment.allocation_id

    assert customer_return.fulfilment_request_id == shipment.fulfilment_request_id

    assert customer_return.order_id == shipment.order_id

    assert customer_return.order_item_id == shipment.order_item_id

    assert customer_return.market_code == shipment.market_code

    assert customer_return.warehouse_id == shipment.warehouse_id

    assert customer_return.assortment_id == shipment.assortment_id

    assert customer_return.product_id == shipment.product_id

    assert customer_return.sku == shipment.sku


def test_return_receipt_targets_returns_location() -> None:
    _, movements = generate_customer_returns(
        (_shipment(),),
        (_location(),),
        config=_config(),
    )

    movement = movements[0]

    assert movement.movement_type == "RETURN_RECEIPT"

    assert movement.source_reference_type == "CUSTOMER_RETURN"

    assert movement.inventory_location_id == "retloc_001"


def test_return_receipt_is_positive_inventory() -> None:
    customer_returns, movements = generate_customer_returns(
        (
            _shipment(
                shipped_quantity=4,
            ),
        ),
        (_location(),),
        config=_config(),
    )

    customer_return = customer_returns[0]

    movement = movements[0]

    assert movement.quantity_delta > 0

    assert movement.quantity_delta == customer_return.returned_quantity


def test_return_receipt_uses_return_date() -> None:
    customer_returns, movements = generate_customer_returns(
        (_shipment(),),
        (_location(),),
        config=_config(),
    )

    assert movements[0].event_date == customer_returns[0].return_date


def test_return_receipt_is_not_sellable_location() -> None:
    location = _location()

    _, movements = generate_customer_returns(
        (_shipment(),),
        (location,),
        config=_config(),
    )

    assert movements[0].inventory_location_id == location.inventory_location_id

    assert location.location_type == "RETURNS"


def test_missing_returns_location_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("shipment warehouse has no RETURNS location"),
    ):
        generate_customer_returns(
            (_shipment(),),
            (
                _location(
                    location_type=("BULK_STORAGE"),
                ),
            ),
            config=_config(),
        )


def test_multiple_returns_locations_are_rejected() -> None:
    locations = (
        _location(
            inventory_location_id=("retloc_001"),
            location_code=("GB-WH-001-RET-1"),
        ),
        _location(
            inventory_location_id=("retloc_002"),
            location_code=("GB-WH-001-RET-2"),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("warehouse has multiple RETURNS locations"),
    ):
        generate_customer_returns(
            (_shipment(),),
            locations,
            config=_config(),
        )


def test_generation_is_deterministic() -> None:
    shipments = (_shipment(),)

    locations = (_location(),)

    config = _config(
        return_probability=1.0,
        partial_return_probability=1.0,
        minimum_return_delay_days=2,
        maximum_return_delay_days=30,
    )

    first = generate_customer_returns(
        shipments,
        locations,
        config=config,
    )

    second = generate_customer_returns(
        shipments,
        locations,
        config=config,
    )

    assert first == second


def test_shipment_input_order_does_not_change_results() -> None:
    shipments = (
        _shipment(
            shipment_id="shp_001",
            order_id="ord_001",
            order_item_id="itm_001",
        ),
        _shipment(
            shipment_id="shp_002",
            reservation_id="res_002",
            allocation_id="alloc_002",
            fulfilment_request_id="req_002",
            order_id="ord_002",
            order_item_id="itm_002",
        ),
    )

    locations = (_location(),)

    first = generate_customer_returns(
        shipments,
        locations,
        config=_config(),
    )

    second = generate_customer_returns(
        tuple(reversed(shipments)),
        locations,
        config=_config(),
    )

    assert first == second


def test_return_ids_are_unique() -> None:
    shipments = (
        _shipment(
            shipment_id="shp_001",
        ),
        _shipment(
            shipment_id="shp_002",
            reservation_id="res_002",
            allocation_id="alloc_002",
            fulfilment_request_id="req_002",
            order_id="ord_002",
            order_item_id="itm_002",
        ),
    )

    customer_returns, _ = generate_customer_returns(
        shipments,
        (_location(),),
        config=_config(),
    )

    return_ids = [customer_return.return_id for customer_return in customer_returns]

    assert len(return_ids) == len(set(return_ids))


def test_generated_returns_pass_validation() -> None:
    shipments = (_shipment(),)

    locations = (_location(),)

    customer_returns, movements = generate_customer_returns(
        shipments,
        locations,
        config=_config(),
    )

    validate_customer_returns(
        customer_returns,
        movements,
        shipments,
        locations,
    )


def test_validation_rejects_return_greater_than_shipment() -> None:
    shipments = (
        _shipment(
            shipped_quantity=4,
        ),
    )

    locations = (_location(),)

    customer_returns, movements = generate_customer_returns(
        shipments,
        locations,
        config=_config(),
    )

    invalid_returns = (
        replace(
            customer_returns[0],
            returned_quantity=5,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("returned quantity exceeds shipped quantity"),
    ):
        validate_customer_returns(
            invalid_returns,
            movements,
            shipments,
            locations,
        )


def test_validation_rejects_wrong_return_location() -> None:
    shipments = (_shipment(),)

    returns_location = _location()

    customer_returns, movements = generate_customer_returns(
        shipments,
        (returns_location,),
        config=_config(),
    )

    invalid_location = _location(
        inventory_location_id=(returns_location.inventory_location_id),
        location_code=(returns_location.location_code),
        location_type="BULK_STORAGE",
    )

    with pytest.raises(
        ValueError,
        match=("RETURN_RECEIPT must target RETURNS location"),
    ):
        validate_customer_returns(
            customer_returns,
            movements,
            shipments,
            (invalid_location,),
        )


def test_validation_rejects_wrong_movement_quantity() -> None:
    shipments = (_shipment(),)

    locations = (_location(),)

    customer_returns, movements = generate_customer_returns(
        shipments,
        locations,
        config=_config(),
    )

    invalid_movements = (
        replace(
            movements[0],
            quantity_delta=999,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("return movement quantity does not match returned quantity"),
    ):
        validate_customer_returns(
            customer_returns,
            invalid_movements,
            shipments,
            locations,
        )


@pytest.mark.parametrize(
    "return_probability",
    (
        -0.01,
        1.01,
    ),
)
def test_config_rejects_invalid_return_probability(
    return_probability: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="return_probability",
    ):
        ReturnsSimulationConfig(
            return_probability=(return_probability),
        )


@pytest.mark.parametrize(
    "partial_return_probability",
    (
        -0.01,
        1.01,
    ),
)
def test_config_rejects_invalid_partial_probability(
    partial_return_probability: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=("partial_return_probability"),
    ):
        ReturnsSimulationConfig(
            partial_return_probability=(partial_return_probability),
        )


def test_config_rejects_negative_minimum_delay() -> None:
    with pytest.raises(
        ValueError,
        match=("minimum return delay cannot be negative"),
    ):
        ReturnsSimulationConfig(
            minimum_return_delay_days=-1,
        )


def test_config_rejects_invalid_delay_range() -> None:
    with pytest.raises(
        ValueError,
        match=("maximum return delay cannot be less than minimum"),
    ):
        ReturnsSimulationConfig(
            minimum_return_delay_days=10,
            maximum_return_delay_days=5,
        )
