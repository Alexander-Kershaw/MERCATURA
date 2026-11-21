from collections import (
    Counter,
    defaultdict,
)
from decimal import Decimal
from typing import Protocol

from mercatura.source.estate.model import (
    EstateReconciliationReport,
    ReconciliationCheck,
)


class OrderLike(Protocol):
    @property
    def order_id(self) -> str: ...

    @property
    def order_status(self) -> str: ...

    @property
    def channel(self) -> str: ...

    @property
    def order_total(self) -> Decimal: ...


class OrderItemLike(Protocol):
    @property
    def order_item_id(self) -> str: ...

    @property
    def order_id(self) -> str: ...

    @property
    def quantity(self) -> int: ...


class PaymentLike(Protocol):
    @property
    def payment_id(self) -> str: ...

    @property
    def order_id(self) -> str: ...

    @property
    def payment_status(self) -> str: ...

    @property
    def amount(self) -> Decimal: ...


class FulfilmentRequestLike(Protocol):
    @property
    def fulfilment_request_id(
        self,
    ) -> str: ...

    @property
    def order_id(self) -> str: ...

    @property
    def order_item_id(self) -> str: ...

    @property
    def requested_quantity(
        self,
    ) -> int: ...

    @property
    def allocated_quantity(
        self,
    ) -> int: ...

    @property
    def unallocated_quantity(
        self,
    ) -> int: ...


class AllocationLike(Protocol):
    @property
    def allocation_id(self) -> str: ...

    @property
    def fulfilment_request_id(
        self,
    ) -> str: ...

    @property
    def order_item_id(self) -> str: ...

    @property
    def allocated_quantity(
        self,
    ) -> int: ...


class ReservationLike(Protocol):
    @property
    def reservation_id(self) -> str: ...

    @property
    def allocation_id(self) -> str: ...

    @property
    def order_item_id(self) -> str: ...

    @property
    def reserved_quantity(
        self,
    ) -> int: ...


class ShipmentLike(Protocol):
    @property
    def shipment_id(self) -> str: ...

    @property
    def reservation_id(self) -> str: ...

    @property
    def order_item_id(self) -> str: ...

    @property
    def shipped_quantity(self) -> int: ...


class ReturnLike(Protocol):
    @property
    def return_id(self) -> str: ...

    @property
    def shipment_id(self) -> str: ...

    @property
    def order_id(self) -> str: ...

    @property
    def order_item_id(self) -> str: ...

    @property
    def returned_quantity(self) -> int: ...


class DispositionLike(Protocol):
    @property
    def disposition_id(self) -> str: ...

    @property
    def return_id(self) -> str: ...

    @property
    def disposition_quantity(
        self,
    ) -> int: ...

    @property
    def disposition_type(self) -> str: ...


class RefundLike(Protocol):
    @property
    def refund_id(self) -> str: ...

    @property
    def return_id(self) -> str: ...

    @property
    def payment_id(self) -> str: ...

    @property
    def order_id(self) -> str: ...

    @property
    def order_item_id(self) -> str: ...

    @property
    def refunded_quantity(
        self,
    ) -> int: ...

    @property
    def refund_amount(
        self,
    ) -> Decimal: ...


class InventoryMovementLike(Protocol):
    @property
    def movement_type(self) -> str: ...

    @property
    def quantity_delta(self) -> int: ...


def reconcile_source_estate(
    *,
    orders: tuple[
        OrderLike,
        ...,
    ],
    order_items: tuple[
        OrderItemLike,
        ...,
    ],
    payment_attempts: tuple[
        PaymentLike,
        ...,
    ],
    fulfilment_requests: tuple[
        FulfilmentRequestLike,
        ...,
    ],
    allocations: tuple[
        AllocationLike,
        ...,
    ],
    reservations: tuple[
        ReservationLike,
        ...,
    ],
    shipments: tuple[
        ShipmentLike,
        ...,
    ],
    customer_returns: tuple[
        ReturnLike,
        ...,
    ],
    dispositions: tuple[
        DispositionLike,
        ...,
    ],
    refunds: tuple[
        RefundLike,
        ...,
    ],
    inventory_movements: tuple[
        InventoryMovementLike,
        ...,
    ],
) -> EstateReconciliationReport:
    checks: list[ReconciliationCheck] = []

    checks.extend(
        _payment_checks(
            orders=orders,
            payment_attempts=(payment_attempts),
        )
    )

    checks.extend(
        _fulfilment_request_checks(
            orders=orders,
            order_items=order_items,
            fulfilment_requests=(fulfilment_requests),
        )
    )

    checks.extend(
        _allocation_checks(
            fulfilment_requests=(fulfilment_requests),
            allocations=allocations,
        )
    )

    checks.extend(
        _reservation_checks(
            allocations=allocations,
            reservations=reservations,
        )
    )

    checks.extend(
        _shipment_checks(
            reservations=reservations,
            shipments=shipments,
        )
    )

    checks.extend(
        _return_checks(
            shipments=shipments,
            customer_returns=(customer_returns),
        )
    )

    checks.extend(
        _disposition_checks(
            customer_returns=(customer_returns),
            dispositions=dispositions,
        )
    )

    checks.extend(
        _refund_checks(
            customer_returns=(customer_returns),
            payment_attempts=(payment_attempts),
            refunds=refunds,
        )
    )

    checks.extend(
        _inventory_checks(
            shipments=shipments,
            customer_returns=(customer_returns),
            dispositions=dispositions,
            inventory_movements=(inventory_movements),
        )
    )

    return EstateReconciliationReport(checks=tuple(checks))


def validate_source_estate_reconciliation(
    report: EstateReconciliationReport,
) -> None:
    if report.passed:
        return

    failures = "; ".join(
        (f"{check.code}: actual={check.actual}, expected={check.expected}")
        for check in report.failed_checks
    )

    raise ValueError(f"source estate reconciliation failed: {failures}")


def _check(
    *,
    code: str,
    description: str,
    actual: int,
    expected: int,
) -> ReconciliationCheck:
    return ReconciliationCheck(
        code=code,
        description=description,
        actual=actual,
        expected=expected,
    )


def _payment_checks(
    *,
    orders: tuple[
        OrderLike,
        ...,
    ],
    payment_attempts: tuple[
        PaymentLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    confirmed_orders = {
        order.order_id: order for order in orders if (order.order_status == "CONFIRMED")
    }

    cancelled_orders = {
        order.order_id: order for order in orders if (order.order_status == "CANCELLED")
    }

    captured = [payment for payment in payment_attempts if (payment.payment_status == "CAPTURED")]

    voided = [payment for payment in payment_attempts if (payment.payment_status == "VOIDED")]

    captured_counts = Counter(payment.order_id for payment in captured)

    voided_counts = Counter(payment.order_id for payment in voided)

    captured_order_ids = set(captured_counts)

    voided_order_ids = set(voided_counts)

    captured_coverage_mismatches = len(set(confirmed_orders) ^ captured_order_ids)

    voided_coverage_mismatches = len(set(cancelled_orders) ^ voided_order_ids)

    duplicate_captures = sum(count - 1 for count in captured_counts.values() if count > 1)

    duplicate_voids = sum(count - 1 for count in voided_counts.values() if count > 1)

    captured_amount_mismatches = 0

    for payment in captured:
        order = confirmed_orders.get(payment.order_id)

        if order is None:
            continue

        if payment.amount != order.order_total:
            captured_amount_mismatches += 1

    return (
        _check(
            code="PAYMENT_CAPTURE_COVERAGE",
            description=("confirmed orders have captured payment coverage"),
            actual=(captured_coverage_mismatches),
            expected=0,
        ),
        _check(
            code="PAYMENT_VOID_COVERAGE",
            description=("cancelled orders have voided payment coverage"),
            actual=(voided_coverage_mismatches),
            expected=0,
        ),
        _check(
            code="PAYMENT_SINGLE_CAPTURE",
            description=("each confirmed order has one captured payment"),
            actual=duplicate_captures,
            expected=0,
        ),
        _check(
            code="PAYMENT_SINGLE_VOID",
            description=("each cancelled order has one voided payment"),
            actual=duplicate_voids,
            expected=0,
        ),
        _check(
            code="PAYMENT_CAPTURE_AMOUNT",
            description=("captured amount equals OMS order total"),
            actual=(captured_amount_mismatches),
            expected=0,
        ),
    )


def _fulfilment_request_checks(
    *,
    orders: tuple[
        OrderLike,
        ...,
    ],
    order_items: tuple[
        OrderItemLike,
        ...,
    ],
    fulfilment_requests: tuple[
        FulfilmentRequestLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    orders_by_id = {order.order_id: order for order in orders}

    eligible_items = {
        item.order_item_id: item
        for item in order_items
        if (
            item.order_id in orders_by_id
            and orders_by_id[item.order_id].order_status == "CONFIRMED"
            and orders_by_id[item.order_id].channel
            in {
                "WEB",
                "MOBILE",
            }
        )
    }

    request_counts = Counter(request.order_item_id for request in fulfilment_requests)

    request_item_ids = set(request_counts)

    coverage_mismatches = len(set(eligible_items) ^ request_item_ids)

    duplicate_requests = sum(count - 1 for count in request_counts.values() if count > 1)

    quantity_mismatches = 0
    arithmetic_mismatches = 0

    for request in fulfilment_requests:
        item = eligible_items.get(request.order_item_id)

        if item is not None and request.requested_quantity != item.quantity:
            quantity_mismatches += 1

        if request.allocated_quantity + request.unallocated_quantity != request.requested_quantity:
            arithmetic_mismatches += 1

    return (
        _check(
            code="FULFILMENT_REQUEST_COVERAGE",
            description=("confirmed digital OMS items have fulfilment requests"),
            actual=coverage_mismatches,
            expected=0,
        ),
        _check(
            code="FULFILMENT_REQUEST_UNIQUENESS",
            description=("one fulfilment request exists per eligible order item"),
            actual=duplicate_requests,
            expected=0,
        ),
        _check(
            code="FULFILMENT_REQUEST_QUANTITY",
            description=("requested quantity equals OMS order-item quantity"),
            actual=quantity_mismatches,
            expected=0,
        ),
        _check(
            code="FULFILMENT_REQUEST_ARITHMETIC",
            description=("allocated plus unallocated equals requested quantity"),
            actual=arithmetic_mismatches,
            expected=0,
        ),
    )


def _allocation_checks(
    *,
    fulfilment_requests: tuple[
        FulfilmentRequestLike,
        ...,
    ],
    allocations: tuple[
        AllocationLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    requests_by_id = {request.fulfilment_request_id: request for request in fulfilment_requests}

    allocated_by_request: dict[
        str,
        int,
    ] = defaultdict(int)

    unknown_requests = 0

    for allocation in allocations:
        if allocation.fulfilment_request_id not in requests_by_id:
            unknown_requests += 1
            continue

        allocated_by_request[allocation.fulfilment_request_id] += allocation.allocated_quantity

    quantity_mismatches = 0

    for request_id, request in requests_by_id.items():
        if allocated_by_request[request_id] != request.allocated_quantity:
            quantity_mismatches += 1

    return (
        _check(
            code="ALLOCATION_REQUEST_REFERENCES",
            description=("allocation fragments reference known fulfilment requests"),
            actual=unknown_requests,
            expected=0,
        ),
        _check(
            code="ALLOCATION_QUANTITY",
            description=("allocation fragments reconcile to request allocation totals"),
            actual=quantity_mismatches,
            expected=0,
        ),
    )


def _reservation_checks(
    *,
    allocations: tuple[
        AllocationLike,
        ...,
    ],
    reservations: tuple[
        ReservationLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    allocation_ids = {allocation.allocation_id for allocation in allocations}

    reservation_counts = Counter(reservation.allocation_id for reservation in reservations)

    coverage_mismatches = len(allocation_ids ^ set(reservation_counts))

    duplicate_reservations = sum(count - 1 for count in reservation_counts.values() if count > 1)

    allocations_by_id = {allocation.allocation_id: allocation for allocation in allocations}

    quantity_mismatches = 0

    for reservation in reservations:
        allocation = allocations_by_id.get(reservation.allocation_id)

        if allocation is None:
            continue

        if reservation.reserved_quantity != allocation.allocated_quantity:
            quantity_mismatches += 1

    return (
        _check(
            code="RESERVATION_COVERAGE",
            description=("each allocation fragment has one reservation"),
            actual=coverage_mismatches,
            expected=0,
        ),
        _check(
            code="RESERVATION_UNIQUENESS",
            description=("allocation fragments are not reserved more than once"),
            actual=duplicate_reservations,
            expected=0,
        ),
        _check(
            code="RESERVATION_QUANTITY",
            description=("reservation quantity equals allocation quantity"),
            actual=quantity_mismatches,
            expected=0,
        ),
    )


def _shipment_checks(
    *,
    reservations: tuple[
        ReservationLike,
        ...,
    ],
    shipments: tuple[
        ShipmentLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    reservations_by_id = {reservation.reservation_id: reservation for reservation in reservations}

    shipment_counts = Counter(shipment.reservation_id for shipment in shipments)

    coverage_mismatches = len(set(reservations_by_id) ^ set(shipment_counts))

    duplicate_shipments = sum(count - 1 for count in shipment_counts.values() if count > 1)

    quantity_mismatches = 0

    for shipment in shipments:
        reservation = reservations_by_id.get(shipment.reservation_id)

        if reservation is None:
            continue

        if shipment.shipped_quantity != reservation.reserved_quantity:
            quantity_mismatches += 1

    return (
        _check(
            code="SHIPMENT_COVERAGE",
            description=("each reservation produces one outbound shipment"),
            actual=coverage_mismatches,
            expected=0,
        ),
        _check(
            code="SHIPMENT_UNIQUENESS",
            description=("reservations are not shipped more than once"),
            actual=duplicate_shipments,
            expected=0,
        ),
        _check(
            code="SHIPMENT_QUANTITY",
            description=("shipped quantity equals reserved quantity"),
            actual=quantity_mismatches,
            expected=0,
        ),
    )


def _return_checks(
    *,
    shipments: tuple[
        ShipmentLike,
        ...,
    ],
    customer_returns: tuple[
        ReturnLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    shipments_by_id = {shipment.shipment_id: shipment for shipment in shipments}

    return_counts = Counter(customer_return.shipment_id for customer_return in customer_returns)

    duplicate_returns = sum(count - 1 for count in return_counts.values() if count > 1)

    unknown_shipments = 0
    quantity_mismatches = 0

    for customer_return in customer_returns:
        shipment = shipments_by_id.get(customer_return.shipment_id)

        if shipment is None:
            unknown_shipments += 1
            continue

        if (
            customer_return.returned_quantity <= 0
            or customer_return.returned_quantity > shipment.shipped_quantity
        ):
            quantity_mismatches += 1

    return (
        _check(
            code="RETURN_SHIPMENT_REFERENCES",
            description=("returns reference known outbound shipments"),
            actual=unknown_shipments,
            expected=0,
        ),
        _check(
            code="RETURN_UNIQUENESS",
            description=("current model permits at most one return per shipment"),
            actual=duplicate_returns,
            expected=0,
        ),
        _check(
            code="RETURN_QUANTITY",
            description=("returned quantity is within shipped quantity"),
            actual=quantity_mismatches,
            expected=0,
        ),
    )


def _disposition_checks(
    *,
    customer_returns: tuple[
        ReturnLike,
        ...,
    ],
    dispositions: tuple[
        DispositionLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    returns_by_id = {
        customer_return.return_id: customer_return for customer_return in customer_returns
    }

    disposition_counts = Counter(disposition.return_id for disposition in dispositions)

    coverage_mismatches = len(set(returns_by_id) ^ set(disposition_counts))

    duplicate_dispositions = sum(count - 1 for count in disposition_counts.values() if count > 1)

    quantity_mismatches = 0

    for disposition in dispositions:
        customer_return = returns_by_id.get(disposition.return_id)

        if customer_return is None:
            continue

        if disposition.disposition_quantity != customer_return.returned_quantity:
            quantity_mismatches += 1

    return (
        _check(
            code="DISPOSITION_COVERAGE",
            description=("each received return has one disposition"),
            actual=coverage_mismatches,
            expected=0,
        ),
        _check(
            code="DISPOSITION_UNIQUENESS",
            description=("customer returns are not disposed more than once"),
            actual=duplicate_dispositions,
            expected=0,
        ),
        _check(
            code="DISPOSITION_QUANTITY",
            description=("disposition quantity equals returned quantity"),
            actual=quantity_mismatches,
            expected=0,
        ),
    )


def _refund_checks(
    *,
    customer_returns: tuple[
        ReturnLike,
        ...,
    ],
    payment_attempts: tuple[
        PaymentLike,
        ...,
    ],
    refunds: tuple[
        RefundLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    returns_by_id = {
        customer_return.return_id: customer_return for customer_return in customer_returns
    }

    payments_by_id = {payment.payment_id: payment for payment in payment_attempts}

    refund_counts = Counter(refund.return_id for refund in refunds)

    coverage_mismatches = len(set(returns_by_id) ^ set(refund_counts))

    duplicate_refunds = sum(count - 1 for count in refund_counts.values() if count > 1)

    quantity_mismatches = 0
    invalid_payment_references = 0

    refund_totals_by_payment: dict[
        str,
        Decimal,
    ] = defaultdict(lambda: Decimal("0"))

    for refund in refunds:
        customer_return = returns_by_id.get(refund.return_id)

        if (
            customer_return is not None
            and refund.refunded_quantity != customer_return.returned_quantity
        ):
            quantity_mismatches += 1

        payment = payments_by_id.get(refund.payment_id)

        if payment is None or payment.payment_status != "CAPTURED":
            invalid_payment_references += 1
            continue

        refund_totals_by_payment[payment.payment_id] += refund.refund_amount

    over_refunded_payments = 0

    for (
        payment_id,
        refund_total,
    ) in refund_totals_by_payment.items():
        if refund_total > payments_by_id[payment_id].amount:
            over_refunded_payments += 1

    return (
        _check(
            code="REFUND_COVERAGE",
            description=("each customer return has one financial refund"),
            actual=coverage_mismatches,
            expected=0,
        ),
        _check(
            code="REFUND_UNIQUENESS",
            description=("customer returns are not refunded more than once"),
            actual=duplicate_refunds,
            expected=0,
        ),
        _check(
            code="REFUND_QUANTITY",
            description=("refunded quantity equals returned quantity"),
            actual=quantity_mismatches,
            expected=0,
        ),
        _check(
            code="REFUND_CAPTURE_REFERENCE",
            description=("refunds reference valid captured payments"),
            actual=(invalid_payment_references),
            expected=0,
        ),
        _check(
            code="REFUND_CAPTURE_LIMIT",
            description=("cumulative refunds do not exceed captured value"),
            actual=(over_refunded_payments),
            expected=0,
        ),
    )


def _inventory_checks(
    *,
    shipments: tuple[
        ShipmentLike,
        ...,
    ],
    customer_returns: tuple[
        ReturnLike,
        ...,
    ],
    dispositions: tuple[
        DispositionLike,
        ...,
    ],
    inventory_movements: tuple[
        InventoryMovementLike,
        ...,
    ],
) -> tuple[
    ReconciliationCheck,
    ...,
]:
    shipped_units = sum(shipment.shipped_quantity for shipment in shipments)

    dispatch_units = -sum(
        movement.quantity_delta
        for movement in inventory_movements
        if (movement.movement_type == "DISPATCH")
    )

    returned_units = sum(customer_return.returned_quantity for customer_return in customer_returns)

    return_receipt_units = sum(
        movement.quantity_delta
        for movement in inventory_movements
        if (movement.movement_type == "RETURN_RECEIPT")
    )

    written_off_units = sum(
        disposition.disposition_quantity
        for disposition in dispositions
        if (disposition.disposition_type == "WRITE_OFF")
    )

    write_off_movement_units = -sum(
        movement.quantity_delta
        for movement in inventory_movements
        if (movement.movement_type == "WRITE_OFF")
    )

    return (
        _check(
            code="INVENTORY_DISPATCH_UNITS",
            description=("physical DISPATCH movements equal shipped units"),
            actual=dispatch_units,
            expected=shipped_units,
        ),
        _check(
            code="INVENTORY_RETURN_UNITS",
            description=("RETURN_RECEIPT movements equal customer returned units"),
            actual=return_receipt_units,
            expected=returned_units,
        ),
        _check(
            code="INVENTORY_WRITE_OFF_UNITS",
            description=("WRITE_OFF movements equal write-off dispositions"),
            actual=(write_off_movement_units),
            expected=written_off_units,
        ),
    )
