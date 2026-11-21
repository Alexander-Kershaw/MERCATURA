from dataclasses import dataclass, replace
from datetime import date
from typing import cast

import pytest

import mercatura.source.systems.returns.disposition_generator as generator_module
from mercatura.source.systems.returns.disposition_generator import (
    generate_return_dispositions,
)
from mercatura.source.systems.returns.disposition_validation import (
    validate_return_dispositions,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
    ReturnReason,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)

RETURN_DATE = date(
    2024,
    6,
    20,
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
    location_type: str,
    warehouse_id: str = "wh_001",
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


def _locations() -> tuple[
    InventoryLocation,
    ...,
]:
    return (
        _location(
            inventory_location_id="ret_001",
            location_code="GB-WH-001-RET",
            location_type="RETURNS",
        ),
        _location(
            inventory_location_id="bulk_001",
            location_code="GB-WH-001-BULK",
            location_type="BULK_STORAGE",
        ),
        _location(
            inventory_location_id="qua_001",
            location_code="GB-WH-001-QUA",
            location_type="QUARANTINE",
        ),
    )


def _return(
    *,
    return_id: str = "ret_evt_001",
    returned_quantity: int = 4,
    return_reason: ReturnReason = "UNWANTED",
) -> CustomerReturn:
    return CustomerReturn(
        return_id=return_id,
        shipment_id="shp_001",
        reservation_id="res_001",
        allocation_id="alloc_001",
        fulfilment_request_id="req_001",
        order_id="ord_001",
        order_item_id="itm_001",
        market_code="GB",
        warehouse_assortment_id="was_001",
        warehouse_id="wh_001",
        warehouse_code="GB-WH-001",
        assortment_id="ast_001",
        product_id="prd_001",
        sku="SKU-001",
        returned_quantity=(returned_quantity),
        return_reason=return_reason,
        return_status="RECEIVED",
        return_date=RETURN_DATE,
    )


def test_one_return_creates_one_disposition() -> None:
    dispositions, _ = generate_return_dispositions(
        (_return(),),
        _locations(),
    )

    assert len(dispositions) == 1


def test_disposition_quantity_matches_return() -> None:
    dispositions, _ = generate_return_dispositions(
        (
            _return(
                returned_quantity=7,
            ),
        ),
        _locations(),
    )

    assert dispositions[0].disposition_quantity == 7


def test_restock_moves_returns_to_bulk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator_module,
        "_choose_disposition",
        lambda _: "RESTOCK",
    )

    dispositions, movements = generate_return_dispositions(
        (_return(),),
        _locations(),
    )

    assert dispositions[0].disposition_type == "RESTOCK"

    assert len(movements) == 2

    assert movements[0].movement_type == "RETURN_TRANSFER_OUT"

    assert movements[0].quantity_delta == -4

    assert movements[0].inventory_location_id == "ret_001"

    assert movements[1].movement_type == "RESTOCK_IN"

    assert movements[1].quantity_delta == 4

    assert movements[1].inventory_location_id == "bulk_001"

    assert sum(movement.quantity_delta for movement in movements) == 0


def test_quarantine_moves_returns_to_quarantine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator_module,
        "_choose_disposition",
        lambda _: "QUARANTINE",
    )

    dispositions, movements = generate_return_dispositions(
        (_return(),),
        _locations(),
    )

    assert dispositions[0].disposition_type == "QUARANTINE"

    assert len(movements) == 2

    assert movements[0].movement_type == "RETURN_TRANSFER_OUT"

    assert movements[1].movement_type == "QUARANTINE_IN"

    assert movements[1].inventory_location_id == "qua_001"

    assert sum(movement.quantity_delta for movement in movements) == 0


def test_write_off_reduces_physical_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator_module,
        "_choose_disposition",
        lambda _: "WRITE_OFF",
    )

    dispositions, movements = generate_return_dispositions(
        (
            _return(
                returned_quantity=3,
            ),
        ),
        _locations(),
    )

    assert dispositions[0].disposition_type == "WRITE_OFF"

    assert len(movements) == 1

    assert movements[0].movement_type == "WRITE_OFF"

    assert movements[0].quantity_delta == -3

    assert movements[0].inventory_location_id == "ret_001"


def test_disposition_occurs_on_or_after_return() -> None:
    dispositions, _ = generate_return_dispositions(
        (_return(),),
        _locations(),
    )

    assert dispositions[0].disposition_date >= RETURN_DATE


def test_inspection_delay_is_at_most_two_days() -> None:
    dispositions, _ = generate_return_dispositions(
        (_return(),),
        _locations(),
    )

    delay = (dispositions[0].disposition_date - RETURN_DATE).days

    assert 0 <= delay <= 2


def test_metadata_is_preserved() -> None:
    customer_return = _return()

    disposition = generate_return_dispositions(
        (customer_return,),
        _locations(),
    )[0][0]

    assert disposition.return_id == customer_return.return_id

    assert disposition.shipment_id == customer_return.shipment_id

    assert disposition.order_id == customer_return.order_id

    assert disposition.order_item_id == customer_return.order_item_id

    assert disposition.warehouse_id == customer_return.warehouse_id

    assert disposition.assortment_id == customer_return.assortment_id

    assert disposition.product_id == customer_return.product_id

    assert disposition.sku == customer_return.sku


def test_non_received_return_is_rejected() -> None:
    customer_return = replace(
        _return(),
        return_status=cast(
            object,
            "OTHER",
        ),
    )

    with pytest.raises(
        ValueError,
        match=("return disposition requires RECEIVED customer returns"),
    ):
        generate_return_dispositions(
            (customer_return,),
            _locations(),
        )


def test_missing_returns_location_is_rejected() -> None:
    locations = tuple(
        location for location in _locations() if (location.location_type != "RETURNS")
    )

    with pytest.raises(
        ValueError,
        match=("warehouse has no RETURNS location"),
    ):
        generate_return_dispositions(
            (_return(),),
            locations,
        )


def test_restock_requires_bulk_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator_module,
        "_choose_disposition",
        lambda _: "RESTOCK",
    )

    locations = tuple(
        location for location in _locations() if (location.location_type != "BULK_STORAGE")
    )

    with pytest.raises(
        ValueError,
        match=("warehouse has no BULK_STORAGE location"),
    ):
        generate_return_dispositions(
            (_return(),),
            locations,
        )


def test_quarantine_requires_quarantine_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator_module,
        "_choose_disposition",
        lambda _: "QUARANTINE",
    )

    locations = tuple(
        location for location in _locations() if (location.location_type != "QUARANTINE")
    )

    with pytest.raises(
        ValueError,
        match=("warehouse has no QUARANTINE location"),
    ):
        generate_return_dispositions(
            (_return(),),
            locations,
        )


def test_generation_is_deterministic() -> None:
    arguments = (
        (_return(),),
        _locations(),
    )

    first = generate_return_dispositions(*arguments)

    second = generate_return_dispositions(*arguments)

    assert first == second


def test_input_order_does_not_change_results() -> None:
    customer_returns = (
        _return(
            return_id="ret_evt_001",
        ),
        replace(
            _return(
                return_id="ret_evt_002",
            ),
            shipment_id="shp_002",
            order_id="ord_002",
            order_item_id="itm_002",
        ),
    )

    first = generate_return_dispositions(
        customer_returns,
        _locations(),
    )

    second = generate_return_dispositions(
        tuple(reversed(customer_returns)),
        _locations(),
    )

    assert first == second


def test_disposition_ids_are_unique() -> None:
    customer_returns = (
        _return(
            return_id="ret_evt_001",
        ),
        replace(
            _return(
                return_id="ret_evt_002",
            ),
            shipment_id="shp_002",
            order_id="ord_002",
            order_item_id="itm_002",
        ),
    )

    dispositions, _ = generate_return_dispositions(
        customer_returns,
        _locations(),
    )

    ids = [disposition.disposition_id for disposition in dispositions]

    assert len(ids) == len(set(ids))


def test_generated_data_passes_validation() -> None:
    customer_returns = (_return(),)

    dispositions, movements = generate_return_dispositions(
        customer_returns,
        _locations(),
    )

    validate_return_dispositions(
        dispositions,
        customer_returns,
        movements,
        _locations(),
    )


def test_validation_rejects_wrong_quantity() -> None:
    customer_returns = (
        _return(
            returned_quantity=4,
        ),
    )

    dispositions, movements = generate_return_dispositions(
        customer_returns,
        _locations(),
    )

    invalid = (
        replace(
            dispositions[0],
            disposition_quantity=5,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("disposition quantity does not match returned quantity"),
    ):
        validate_return_dispositions(
            invalid,
            customer_returns,
            movements,
            _locations(),
        )
