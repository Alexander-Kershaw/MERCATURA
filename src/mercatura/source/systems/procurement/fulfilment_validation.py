from collections import defaultdict

from mercatura.source.systems.procurement.fulfilment_model import (
    FULFILMENT_OUTCOMES,
    GoodsReceipt,
    PurchaseOrderLineFulfilment,
    SupplierShipment,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)


def validate_fulfilment(
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    receipts: tuple[GoodsReceipt, ...],
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    sourcing_agreements: tuple[SourcingAgreement, ...],
) -> None:
    _validate_unique_fulfilments(fulfilments)

    _validate_unique_shipments(shipments)

    _validate_unique_receipts(receipts)

    _validate_fulfilment_coverage(
        fulfilments,
        lines,
    )

    _validate_shipments(
        fulfilments,
        shipments,
        orders,
        lines,
        sourcing_agreements,
    )

    _validate_outcome_semantics(
        fulfilments,
        shipments,
        lines,
    )

    _validate_receipts(
        receipts,
        shipments,
    )


def _validate_unique_fulfilments(
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
) -> None:
    ids: list[str] = [row.fulfilment_id for row in fulfilments]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fulfilment_id detected")

    line_ids: list[str] = [row.purchase_order_line_id for row in fulfilments]

    if len(line_ids) != len(set(line_ids)):
        raise ValueError("duplicate fulfilment record for purchase order line")


def _validate_unique_shipments(
    shipments: tuple[SupplierShipment, ...],
) -> None:
    ids: list[str] = [row.shipment_id for row in shipments]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate shipment_id detected")

    numbers: list[str] = [row.shipment_number for row in shipments]

    if len(numbers) != len(set(numbers)):
        raise ValueError("duplicate shipment_number detected")


def _validate_unique_receipts(
    receipts: tuple[GoodsReceipt, ...],
) -> None:
    ids: list[str] = [row.goods_receipt_id for row in receipts]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate goods_receipt_id detected")

    numbers: list[str] = [row.receipt_number for row in receipts]

    if len(numbers) != len(set(numbers)):
        raise ValueError("duplicate receipt_number detected")

    shipment_ids: list[str] = [row.shipment_id for row in receipts]

    if len(shipment_ids) != len(set(shipment_ids)):
        raise ValueError("multiple receipts reference the same shipment")


def _validate_fulfilment_coverage(
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        line.purchase_order_line_id: line for line in lines
    }

    fulfilment_line_ids: set[str] = {row.purchase_order_line_id for row in fulfilments}

    expected_line_ids: set[str] = set(lines_by_id)

    if fulfilment_line_ids != expected_line_ids:
        raise ValueError("fulfilment records do not cover every purchase order line")

    valid_outcomes = set(FULFILMENT_OUTCOMES)

    for fulfilment in fulfilments:
        line: PurchaseOrderLine = lines_by_id[fulfilment.purchase_order_line_id]

        if fulfilment.purchase_order_id != line.purchase_order_id:
            raise ValueError("fulfilment purchase order does not match line")

        if fulfilment.fulfilment_outcome not in valid_outcomes:
            raise ValueError("invalid fulfilment outcome")


def _validate_shipments(
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    sourcing_agreements: tuple[SourcingAgreement, ...],
) -> None:
    orders_by_id: dict[str, PurchaseOrder] = {order.purchase_order_id: order for order in orders}

    lines_by_id: dict[str, PurchaseOrderLine] = {
        line.purchase_order_line_id: line for line in lines
    }

    sourcing_by_id: dict[str, SourcingAgreement] = {
        agreement.sourcing_id: agreement for agreement in sourcing_agreements
    }

    fulfilment_by_line: dict[str, PurchaseOrderLineFulfilment] = {
        row.purchase_order_line_id: row for row in fulfilments
    }

    grouped: dict[
        str,
        list[SupplierShipment],
    ] = defaultdict(list)

    for shipment in shipments:
        line: PurchaseOrderLine | None = lines_by_id.get(shipment.purchase_order_line_id)

        if line is None:
            raise ValueError("shipment references unknown purchase order line")

        order: PurchaseOrder | None = orders_by_id.get(shipment.purchase_order_id)

        if order is None:
            raise ValueError("shipment references unknown purchase order")

        if shipment.purchase_order_id != line.purchase_order_id:
            raise ValueError("shipment purchase order does not match line")

        if shipment.sourcing_id != line.sourcing_id:
            raise ValueError("shipment sourcing does not match purchase order line")

        sourcing: SourcingAgreement | None = sourcing_by_id.get(shipment.sourcing_id)

        if sourcing is None:
            raise ValueError("shipment references unknown sourcing agreement")

        if shipment.supplier_id != order.supplier_id:
            raise ValueError("shipment supplier does not match purchase order")

        if shipment.supplier_code != order.supplier_code:
            raise ValueError("shipment supplier code does not match purchase order")

        if sourcing.supplier_id != shipment.supplier_id:
            raise ValueError("shipment supplier does not match sourcing agreement")

        if shipment.market_code != order.market_code:
            raise ValueError("shipment market does not match purchase order")

        if sourcing.market_code != shipment.market_code:
            raise ValueError("shipment market does not match sourcing agreement")

        fulfilment: PurchaseOrderLineFulfilment = fulfilment_by_line[
            shipment.purchase_order_line_id
        ]

        if shipment.fulfilment_outcome != fulfilment.fulfilment_outcome:
            raise ValueError("shipment outcome does not match line fulfilment")

        if not isinstance(
            shipment.shipped_quantity,
            int,
        ) or isinstance(
            shipment.shipped_quantity,
            bool,
        ):
            raise ValueError("shipped quantity must be an integer")

        if shipment.shipped_quantity <= 0:
            raise ValueError("shipped quantity must be positive")

        if shipment.shipped_date < order.order_date:
            raise ValueError("shipment predates purchase order")

        if shipment.delivered_date < shipment.shipped_date:
            raise ValueError("shipment delivered before it was shipped")

        if shipment.shipment_sequence <= 0:
            raise ValueError("shipment sequence must be positive")

        grouped[shipment.purchase_order_line_id].append(shipment)

    for line_id, line_shipments in grouped.items():
        ordered: list[SupplierShipment] = sorted(
            line_shipments,
            key=lambda row: row.shipment_sequence,
        )

        actual: list[int] = [row.shipment_sequence for row in ordered]

        expected: list[int] = list(
            range(
                1,
                len(ordered) + 1,
            )
        )

        if actual != expected:
            raise ValueError(f"invalid shipment sequence for line {line_id}")


def _validate_outcome_semantics(
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        line.purchase_order_line_id: line for line in lines
    }

    shipments_by_line: dict[
        str,
        list[SupplierShipment],
    ] = defaultdict(list)

    for shipment in shipments:
        shipments_by_line[shipment.purchase_order_line_id].append(shipment)

    for fulfilment in fulfilments:
        line: PurchaseOrderLine = lines_by_id[fulfilment.purchase_order_line_id]

        line_shipments: list[SupplierShipment] = sorted(
            shipments_by_line.get(
                line.purchase_order_line_id,
                [],
            ),
            key=lambda row: row.shipment_sequence,
        )

        outcome = fulfilment.fulfilment_outcome

        total_shipped: int = sum(row.shipped_quantity for row in line_shipments)

        if outcome == "CANCELLED":
            if line_shipments:
                raise ValueError("cancelled line must not have shipments")

            continue

        if outcome == "ON_TIME_FULL":
            _require_single_full_shipment(
                line=line,
                shipments=line_shipments,
            )

            if line_shipments[0].delivered_date != line.expected_delivery_date:
                raise ValueError("ON_TIME_FULL delivery must equal expected date")

            continue

        if outcome == "EARLY_FULL":
            _require_single_full_shipment(
                line=line,
                shipments=line_shipments,
            )

            if not (line_shipments[0].delivered_date < line.expected_delivery_date):
                raise ValueError("EARLY_FULL delivery must precede expected date")

            continue

        if outcome == "LATE_FULL":
            _require_single_full_shipment(
                line=line,
                shipments=line_shipments,
            )

            if not (line_shipments[0].delivered_date > line.expected_delivery_date):
                raise ValueError("LATE_FULL delivery must follow expected date")

            continue

        if outcome == "SPLIT_FULL":
            if len(line_shipments) != 2:
                raise ValueError("SPLIT_FULL requires exactly two shipments")

            if total_shipped != line.ordered_quantity:
                raise ValueError("SPLIT_FULL shipments must fully satisfy line")

            if not (line_shipments[1].delivered_date > line_shipments[0].delivered_date):
                raise ValueError("second split shipment must arrive after first")

            continue

        if outcome == "SHORT_SHIPPED":
            if len(line_shipments) != 1:
                raise ValueError("SHORT_SHIPPED requires exactly one shipment")

            if not (0 < total_shipped < line.ordered_quantity):
                raise ValueError("SHORT_SHIPPED quantity must be below ordered quantity")

            continue

        raise ValueError("unsupported fulfilment outcome")


def _require_single_full_shipment(
    *,
    line: PurchaseOrderLine,
    shipments: list[SupplierShipment],
) -> None:
    if len(shipments) != 1:
        raise ValueError("full fulfilment outcome requires exactly one shipment")

    if shipments[0].shipped_quantity != line.ordered_quantity:
        raise ValueError("full fulfilment shipment must equal ordered quantity")


def _validate_receipts(
    receipts: tuple[GoodsReceipt, ...],
    shipments: tuple[SupplierShipment, ...],
) -> None:
    shipments_by_id: dict[str, SupplierShipment] = {
        shipment.shipment_id: shipment for shipment in shipments
    }

    receipt_shipment_ids: set[str] = {receipt.shipment_id for receipt in receipts}

    if receipt_shipment_ids != set(shipments_by_id):
        raise ValueError("goods receipts do not cover every shipment exactly once")

    for receipt in receipts:
        shipment: SupplierShipment | None = shipments_by_id.get(receipt.shipment_id)

        if shipment is None:
            raise ValueError("goods receipt references unknown shipment")

        if receipt.purchase_order_id != shipment.purchase_order_id:
            raise ValueError("receipt purchase order does not match shipment")

        if receipt.purchase_order_line_id != shipment.purchase_order_line_id:
            raise ValueError("receipt line does not match shipment")

        if receipt.market_code != shipment.market_code:
            raise ValueError("receipt market does not match shipment")

        if receipt.receipt_sequence != shipment.shipment_sequence:
            raise ValueError("receipt sequence does not match shipment sequence")

        if receipt.received_quantity != shipment.shipped_quantity:
            raise ValueError("received quantity does not match shipped quantity")

        if receipt.received_date != shipment.delivered_date:
            raise ValueError("receipt date does not match shipment delivery date")
