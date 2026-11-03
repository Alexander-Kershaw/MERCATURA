from dataclasses import replace
from datetime import timedelta
from typing import cast

import pytest

from mercatura.source.systems.procurement.fulfilment_model import (
    FulfilmentOutcome,
    GoodsReceipt,
    PurchaseOrderLineFulfilment,
    SupplierShipment,
)
from mercatura.source.systems.procurement.fulfilment_validation import (
    validate_fulfilment,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)


def replace_fulfilment(
    rows: tuple[PurchaseOrderLineFulfilment, ...],
    replacement: PurchaseOrderLineFulfilment,
) -> tuple[PurchaseOrderLineFulfilment, ...]:
    return tuple(
        replacement if row.fulfilment_id == replacement.fulfilment_id else row for row in rows
    )


def replace_shipment(
    rows: tuple[SupplierShipment, ...],
    replacement: SupplierShipment,
) -> tuple[SupplierShipment, ...]:
    return tuple(replacement if row.shipment_id == replacement.shipment_id else row for row in rows)


def replace_receipt(
    rows: tuple[GoodsReceipt, ...],
    replacement: GoodsReceipt,
) -> tuple[GoodsReceipt, ...]:
    return tuple(
        replacement if row.goods_receipt_id == replacement.goods_receipt_id else row for row in rows
    )


def validate(
    *,
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    receipts: tuple[GoodsReceipt, ...],
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    validate_fulfilment(
        fulfilments,
        shipments,
        receipts,
        orders,
        lines,
        agreements,
    )


def fulfilment_for_outcome(
    fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    outcome: FulfilmentOutcome,
) -> PurchaseOrderLineFulfilment:
    return next(row for row in fulfilments if row.fulfilment_outcome == outcome)


def test_valid_dataset_passes_validation(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    validate(
        fulfilments=line_fulfilments,
        shipments=shipments,
        receipts=goods_receipts,
        orders=purchase_orders,
        lines=purchase_order_lines,
        agreements=agreements,
    )


def test_rejects_duplicate_fulfilment_id(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    broken = (
        *line_fulfilments,
        line_fulfilments[0],
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate fulfilment_id",
    ):
        validate(
            fulfilments=broken,
            shipments=shipments,
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_duplicate_fulfilment_for_line(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    duplicate: PurchaseOrderLineFulfilment = replace(
        line_fulfilments[0],
        fulfilment_id="ful_duplicate",
    )

    broken = (
        *line_fulfilments,
        duplicate,
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate fulfilment record",
    ):
        validate(
            fulfilments=broken,
            shipments=shipments,
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_missing_fulfilment_record(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = line_fulfilments[0]

    broken = tuple(row for row in line_fulfilments if row.fulfilment_id != target.fulfilment_id)

    with pytest.raises(
        ValueError,
        match="do not cover every",
    ):
        validate(
            fulfilments=broken,
            shipments=shipments,
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_fulfilment_po_mismatch(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        line_fulfilments[0],
        purchase_order_id="po_wrong",
    )

    with pytest.raises(
        ValueError,
        match="does not match line",
    ):
        validate(
            fulfilments=replace_fulfilment(
                line_fulfilments,
                broken_row,
            ),
            shipments=shipments,
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_invalid_outcome(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        line_fulfilments[0],
        fulfilment_outcome=cast(
            FulfilmentOutcome,
            "INVALID",
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid fulfilment outcome",
    ):
        validate(
            fulfilments=replace_fulfilment(
                line_fulfilments,
                broken_row,
            ),
            shipments=shipments,
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_duplicate_shipment_id(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken = (
        *shipments,
        shipments[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate shipment_id",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=broken,
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_duplicate_shipment_number(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        shipments[1],
        shipment_number=(shipments[0].shipment_number),
    )

    with pytest.raises(
        ValueError,
        match="duplicate shipment_number",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_unknown_shipment_line(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        shipments[0],
        purchase_order_line_id="pol_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown purchase order line",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_shipment_sourcing_mismatch(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        shipments[0],
        sourcing_id="src_wrong",
    )

    with pytest.raises(
        ValueError,
        match="sourcing",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_shipment_supplier_mismatch(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        shipments[0],
        supplier_id="sup_wrong",
    )

    with pytest.raises(
        ValueError,
        match="shipment supplier",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_shipment_market_mismatch(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        shipments[0],
        market_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="shipment market",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_zero_shipped_quantity(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken_row = replace(
        shipments[0],
        shipped_quantity=0,
    )

    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_shipment_before_po(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = shipments[0]

    order = next(
        row for row in purchase_orders if row.purchase_order_id == target.purchase_order_id
    )

    broken_row = replace(
        target,
        shipped_date=(order.order_date - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="predates purchase order",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_delivery_before_shipment(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = shipments[0]

    broken_row = replace(
        target,
        delivered_date=(target.shipped_date - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="delivered before",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_shipment_outcome_mismatch(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = shipments[0]

    fulfilment = next(
        row
        for row in line_fulfilments
        if row.purchase_order_line_id == target.purchase_order_line_id
    )

    wrong: FulfilmentOutcome = (
        "LATE_FULL" if fulfilment.fulfilment_outcome != "LATE_FULL" else "ON_TIME_FULL"
    )

    broken_row = replace(
        target,
        fulfilment_outcome=wrong,
    )

    with pytest.raises(
        ValueError,
        match="outcome does not match",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken_row,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_cancelled_line_with_shipment(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    cancelled = fulfilment_for_outcome(
        line_fulfilments,
        "CANCELLED",
    )

    line = next(
        row
        for row in purchase_order_lines
        if row.purchase_order_line_id == cancelled.purchase_order_line_id
    )

    order = next(row for row in purchase_orders if row.purchase_order_id == line.purchase_order_id)

    fake = replace(
        shipments[0],
        shipment_id="shp_cancelled_test",
        shipment_number=("SHP-CANCELLED-TEST"),
        purchase_order_id=(order.purchase_order_id),
        purchase_order_line_id=(line.purchase_order_line_id),
        sourcing_id=line.sourcing_id,
        supplier_id=order.supplier_id,
        supplier_code=order.supplier_code,
        market_code=order.market_code,
        shipment_sequence=1,
        shipped_quantity=1,
        shipped_date=order.order_date,
        delivered_date=(order.order_date + timedelta(days=1)),
        fulfilment_outcome="CANCELLED",
    )

    with pytest.raises(
        ValueError,
        match="cancelled line",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=(
                *shipments,
                fake,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_on_time_delivery_on_wrong_date(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    fulfilment = fulfilment_for_outcome(
        line_fulfilments,
        "ON_TIME_FULL",
    )

    target = next(
        row for row in shipments if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    broken = replace(
        target,
        delivered_date=(target.delivered_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="must equal expected date",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_early_delivery_not_early(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    fulfilment = fulfilment_for_outcome(
        line_fulfilments,
        "EARLY_FULL",
    )

    line = next(
        row
        for row in purchase_order_lines
        if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    target = next(
        row for row in shipments if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    broken = replace(
        target,
        delivered_date=(line.expected_delivery_date),
    )

    with pytest.raises(
        ValueError,
        match="must precede expected",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_late_delivery_not_late(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    fulfilment = fulfilment_for_outcome(
        line_fulfilments,
        "LATE_FULL",
    )

    line = next(
        row
        for row in purchase_order_lines
        if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    target = next(
        row for row in shipments if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    broken = replace(
        target,
        delivered_date=(line.expected_delivery_date),
    )

    with pytest.raises(
        ValueError,
        match="must follow expected",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_short_shipment_at_full_quantity(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    fulfilment = fulfilment_for_outcome(
        line_fulfilments,
        "SHORT_SHIPPED",
    )

    line = next(
        row
        for row in purchase_order_lines
        if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    target = next(
        row for row in shipments if row.purchase_order_line_id == fulfilment.purchase_order_line_id
    )

    broken = replace(
        target,
        shipped_quantity=(line.ordered_quantity),
    )

    with pytest.raises(
        ValueError,
        match="below ordered quantity",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=replace_shipment(
                shipments,
                broken,
            ),
            receipts=goods_receipts,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_missing_receipt(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = goods_receipts[0]

    broken = tuple(row for row in goods_receipts if row.goods_receipt_id != target.goods_receipt_id)

    with pytest.raises(
        ValueError,
        match="do not cover every shipment",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=shipments,
            receipts=broken,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_duplicate_receipt_id(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    broken = (
        *goods_receipts,
        goods_receipts[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate goods_receipt_id",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=shipments,
            receipts=broken,
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_wrong_received_quantity(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = goods_receipts[0]

    broken = replace(
        target,
        received_quantity=(target.received_quantity + 1),
    )

    with pytest.raises(
        ValueError,
        match="does not match shipped quantity",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=shipments,
            receipts=replace_receipt(
                goods_receipts,
                broken,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_wrong_receipt_date(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = goods_receipts[0]

    broken = replace(
        target,
        received_date=(target.received_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="does not match shipment delivery",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=shipments,
            receipts=replace_receipt(
                goods_receipts,
                broken,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_wrong_receipt_market(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = goods_receipts[0]

    broken = replace(
        target,
        market_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="receipt market",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=shipments,
            receipts=replace_receipt(
                goods_receipts,
                broken,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )


def test_rejects_wrong_receipt_sequence(
    line_fulfilments,
    shipments,
    goods_receipts,
    purchase_orders,
    purchase_order_lines,
    agreements,
) -> None:
    target = goods_receipts[0]

    broken = replace(
        target,
        receipt_sequence=99,
    )

    with pytest.raises(
        ValueError,
        match="receipt sequence",
    ):
        validate(
            fulfilments=line_fulfilments,
            shipments=shipments,
            receipts=replace_receipt(
                goods_receipts,
                broken,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            agreements=agreements,
        )
