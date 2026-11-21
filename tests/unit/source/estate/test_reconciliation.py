from dataclasses import (
    dataclass,
    replace,
)
from decimal import Decimal

import pytest

from mercatura.source.estate.reconciliation import (
    reconcile_source_estate,
    validate_source_estate_reconciliation,
)


@dataclass(
    frozen=True,
    slots=True,
)
class OrderStub:
    order_id: str
    order_status: str
    channel: str
    order_total: Decimal


@dataclass(
    frozen=True,
    slots=True,
)
class OrderItemStub:
    order_item_id: str
    order_id: str
    quantity: int


@dataclass(
    frozen=True,
    slots=True,
)
class PaymentStub:
    payment_id: str
    order_id: str
    payment_status: str
    amount: Decimal


@dataclass(
    frozen=True,
    slots=True,
)
class RequestStub:
    fulfilment_request_id: str
    order_id: str
    order_item_id: str

    requested_quantity: int
    allocated_quantity: int
    unallocated_quantity: int


@dataclass(
    frozen=True,
    slots=True,
)
class AllocationStub:
    allocation_id: str
    fulfilment_request_id: str
    order_item_id: str
    allocated_quantity: int


@dataclass(
    frozen=True,
    slots=True,
)
class ReservationStub:
    reservation_id: str
    allocation_id: str
    order_item_id: str
    reserved_quantity: int


@dataclass(
    frozen=True,
    slots=True,
)
class ShipmentStub:
    shipment_id: str
    reservation_id: str
    order_item_id: str
    shipped_quantity: int


@dataclass(
    frozen=True,
    slots=True,
)
class ReturnStub:
    return_id: str
    shipment_id: str
    order_id: str
    order_item_id: str
    returned_quantity: int


@dataclass(
    frozen=True,
    slots=True,
)
class DispositionStub:
    disposition_id: str
    return_id: str
    disposition_quantity: int
    disposition_type: str


@dataclass(
    frozen=True,
    slots=True,
)
class RefundStub:
    refund_id: str
    return_id: str
    payment_id: str
    order_id: str
    order_item_id: str
    refunded_quantity: int
    refund_amount: Decimal


@dataclass(
    frozen=True,
    slots=True,
)
class MovementStub:
    movement_type: str
    quantity_delta: int


@dataclass(
    frozen=True,
    slots=True,
)
class EstateFixture:
    orders: tuple[
        OrderStub,
        ...,
    ]

    order_items: tuple[
        OrderItemStub,
        ...,
    ]

    payments: tuple[
        PaymentStub,
        ...,
    ]

    requests: tuple[
        RequestStub,
        ...,
    ]

    allocations: tuple[
        AllocationStub,
        ...,
    ]

    reservations: tuple[
        ReservationStub,
        ...,
    ]

    shipments: tuple[
        ShipmentStub,
        ...,
    ]

    returns: tuple[
        ReturnStub,
        ...,
    ]

    dispositions: tuple[
        DispositionStub,
        ...,
    ]

    refunds: tuple[
        RefundStub,
        ...,
    ]

    movements: tuple[
        MovementStub,
        ...,
    ]


def _valid_estate() -> EstateFixture:
    orders = (
        OrderStub(
            order_id="ord_001",
            order_status="CONFIRMED",
            channel="WEB",
            order_total=Decimal("20.00"),
        ),
        OrderStub(
            order_id="ord_002",
            order_status="CANCELLED",
            channel="STORE",
            order_total=Decimal("15.00"),
        ),
    )

    order_items = (
        OrderItemStub(
            order_item_id="itm_001",
            order_id="ord_001",
            quantity=2,
        ),
        OrderItemStub(
            order_item_id="itm_002",
            order_id="ord_002",
            quantity=1,
        ),
    )

    payments = (
        PaymentStub(
            payment_id="pay_001",
            order_id="ord_001",
            payment_status="CAPTURED",
            amount=Decimal("20.00"),
        ),
        PaymentStub(
            payment_id="pay_002",
            order_id="ord_002",
            payment_status="VOIDED",
            amount=Decimal("15.00"),
        ),
    )

    requests = (
        RequestStub(
            fulfilment_request_id="req_001",
            order_id="ord_001",
            order_item_id="itm_001",
            requested_quantity=2,
            allocated_quantity=2,
            unallocated_quantity=0,
        ),
    )

    allocations = (
        AllocationStub(
            allocation_id="alloc_001",
            fulfilment_request_id="req_001",
            order_item_id="itm_001",
            allocated_quantity=2,
        ),
    )

    reservations = (
        ReservationStub(
            reservation_id="res_001",
            allocation_id="alloc_001",
            order_item_id="itm_001",
            reserved_quantity=2,
        ),
    )

    shipments = (
        ShipmentStub(
            shipment_id="shp_001",
            reservation_id="res_001",
            order_item_id="itm_001",
            shipped_quantity=2,
        ),
    )

    returns = (
        ReturnStub(
            return_id="ret_001",
            shipment_id="shp_001",
            order_id="ord_001",
            order_item_id="itm_001",
            returned_quantity=1,
        ),
    )

    dispositions = (
        DispositionStub(
            disposition_id="dsp_001",
            return_id="ret_001",
            disposition_quantity=1,
            disposition_type="RESTOCK",
        ),
    )

    refunds = (
        RefundStub(
            refund_id="rfd_001",
            return_id="ret_001",
            payment_id="pay_001",
            order_id="ord_001",
            order_item_id="itm_001",
            refunded_quantity=1,
            refund_amount=Decimal("10.00"),
        ),
    )

    movements = (
        MovementStub(
            movement_type="DISPATCH",
            quantity_delta=-2,
        ),
        MovementStub(
            movement_type=("RETURN_RECEIPT"),
            quantity_delta=1,
        ),
    )

    return EstateFixture(
        orders=orders,
        order_items=order_items,
        payments=payments,
        requests=requests,
        allocations=allocations,
        reservations=reservations,
        shipments=shipments,
        returns=returns,
        dispositions=dispositions,
        refunds=refunds,
        movements=movements,
    )


def _reconcile(
    estate: EstateFixture,
):
    return reconcile_source_estate(
        orders=estate.orders,
        order_items=estate.order_items,
        payment_attempts=(estate.payments),
        fulfilment_requests=(estate.requests),
        allocations=(estate.allocations),
        reservations=(estate.reservations),
        shipments=estate.shipments,
        customer_returns=(estate.returns),
        dispositions=(estate.dispositions),
        refunds=estate.refunds,
        inventory_movements=(estate.movements),
    )


def test_valid_estate_passes() -> None:
    report = _reconcile(_valid_estate())

    assert report.passed

    assert report.failed_checks == ()


def test_valid_report_passes_validation() -> None:
    report = _reconcile(_valid_estate())

    validate_source_estate_reconciliation(report)


def test_missing_capture_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        payments=tuple(
            payment for payment in estate.payments if (payment.payment_status != "CAPTURED")
        ),
    )

    report = _reconcile(estate)

    assert not report.passed

    codes = {check.code for check in report.failed_checks}

    assert "PAYMENT_CAPTURE_COVERAGE" in codes


def test_wrong_payment_amount_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        payments=(
            replace(
                estate.payments[0],
                amount=Decimal("19.00"),
            ),
            estate.payments[1],
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "PAYMENT_CAPTURE_AMOUNT" in codes


def test_missing_fulfilment_request_is_detected() -> None:
    estate = replace(
        _valid_estate(),
        requests=(),
        allocations=(),
        reservations=(),
        shipments=(),
        returns=(),
        dispositions=(),
        refunds=(),
        movements=(),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "FULFILMENT_REQUEST_COVERAGE" in codes


def test_allocation_quantity_mismatch_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        allocations=(
            replace(
                estate.allocations[0],
                allocated_quantity=1,
            ),
        ),
        reservations=(
            replace(
                estate.reservations[0],
                reserved_quantity=1,
            ),
        ),
        shipments=(
            replace(
                estate.shipments[0],
                shipped_quantity=1,
            ),
        ),
        returns=(),
        dispositions=(),
        refunds=(),
        movements=(
            MovementStub(
                movement_type="DISPATCH",
                quantity_delta=-1,
            ),
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "ALLOCATION_QUANTITY" in codes


def test_missing_reservation_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        reservations=(),
        shipments=(),
        returns=(),
        dispositions=(),
        refunds=(),
        movements=(),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "RESERVATION_COVERAGE" in codes


def test_shipment_quantity_mismatch_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        shipments=(
            replace(
                estate.shipments[0],
                shipped_quantity=1,
            ),
        ),
        returns=(),
        dispositions=(),
        refunds=(),
        movements=(
            MovementStub(
                movement_type="DISPATCH",
                quantity_delta=-1,
            ),
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "SHIPMENT_QUANTITY" in codes


def test_excess_return_quantity_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        returns=(
            replace(
                estate.returns[0],
                returned_quantity=3,
            ),
        ),
        dispositions=(
            replace(
                estate.dispositions[0],
                disposition_quantity=3,
            ),
        ),
        refunds=(
            replace(
                estate.refunds[0],
                refunded_quantity=3,
            ),
        ),
        movements=(
            estate.movements[0],
            MovementStub(
                movement_type=("RETURN_RECEIPT"),
                quantity_delta=3,
            ),
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "RETURN_QUANTITY" in codes


def test_missing_disposition_is_detected() -> None:
    estate = replace(
        _valid_estate(),
        dispositions=(),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "DISPOSITION_COVERAGE" in codes


def test_missing_refund_is_detected() -> None:
    estate = replace(
        _valid_estate(),
        refunds=(),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "REFUND_COVERAGE" in codes


def test_over_refund_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        refunds=(
            replace(
                estate.refunds[0],
                refund_amount=Decimal("25.00"),
            ),
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "REFUND_CAPTURE_LIMIT" in codes


def test_dispatch_ledger_mismatch_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        movements=(
            MovementStub(
                movement_type="DISPATCH",
                quantity_delta=-1,
            ),
            estate.movements[1],
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "INVENTORY_DISPATCH_UNITS" in codes


def test_return_ledger_mismatch_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        movements=(
            estate.movements[0],
            MovementStub(
                movement_type=("RETURN_RECEIPT"),
                quantity_delta=2,
            ),
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "INVENTORY_RETURN_UNITS" in codes


def test_write_off_reconciles_to_inventory() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        dispositions=(
            replace(
                estate.dispositions[0],
                disposition_type=("WRITE_OFF"),
            ),
        ),
        movements=(
            *estate.movements,
            MovementStub(
                movement_type="WRITE_OFF",
                quantity_delta=-1,
            ),
        ),
    )

    report = _reconcile(estate)

    assert report.passed


def test_missing_write_off_movement_is_detected() -> None:
    estate = _valid_estate()

    estate = replace(
        estate,
        dispositions=(
            replace(
                estate.dispositions[0],
                disposition_type=("WRITE_OFF"),
            ),
        ),
    )

    report = _reconcile(estate)

    codes = {check.code for check in report.failed_checks}

    assert "INVENTORY_WRITE_OFF_UNITS" in codes


def test_failed_report_raises_with_check_code() -> None:
    estate = replace(
        _valid_estate(),
        refunds=(),
    )

    report = _reconcile(estate)

    with pytest.raises(
        ValueError,
        match="REFUND_COVERAGE",
    ):
        validate_source_estate_reconciliation(report)
