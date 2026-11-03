from collections import Counter, defaultdict

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.procurement.fulfilment_generator import (
    generate_fulfilment,
)
from mercatura.source.systems.procurement.fulfilment_model import (
    FULFILMENT_OUTCOMES,
    GoodsReceipt,
    PurchaseOrderLineFulfilment,
    SupplierShipment,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)


def test_generation_is_deterministic(
    context: SimulationContext,
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    first: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ] = generate_fulfilment(
        context,
        orders=purchase_orders,
        lines=purchase_order_lines,
    )

    second: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ] = generate_fulfilment(
        context,
        orders=purchase_orders,
        lines=purchase_order_lines,
    )

    assert first == second


def test_every_po_line_has_one_fulfilment_record(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    assert len(line_fulfilments) == len(purchase_order_lines)

    assert {row.purchase_order_line_id for row in line_fulfilments} == {
        line.purchase_order_line_id for line in purchase_order_lines
    }


def test_all_outcomes_are_present(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
) -> None:
    actual: set[str] = {row.fulfilment_outcome for row in line_fulfilments}

    assert actual == set(FULFILMENT_OUTCOMES)


def test_outcome_distribution_is_reasonable(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
) -> None:
    counts: Counter[str] = Counter(row.fulfilment_outcome for row in line_fulfilments)

    total = len(line_fulfilments)

    shares: dict[str, float] = {key: value / total for key, value in counts.items()}

    assert 0.63 <= shares["ON_TIME_FULL"] <= 0.73

    assert 0.07 <= shares["EARLY_FULL"] <= 0.13

    assert 0.07 <= shares["LATE_FULL"] <= 0.13

    assert 0.04 <= shares["SPLIT_FULL"] <= 0.10

    assert 0.02 <= shares["SHORT_SHIPPED"] <= 0.06

    assert 0.003 <= shares["CANCELLED"] <= 0.02


def test_fulfilment_ids_are_unique(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
) -> None:
    ids: list[str] = [row.fulfilment_id for row in line_fulfilments]

    assert len(ids) == len(set(ids))


def test_shipment_ids_are_unique(
    shipments: tuple[SupplierShipment, ...],
) -> None:
    ids: list[str] = [row.shipment_id for row in shipments]

    assert len(ids) == len(set(ids))


def test_shipment_numbers_are_unique(
    shipments: tuple[SupplierShipment, ...],
) -> None:
    numbers: list[str] = [row.shipment_number for row in shipments]

    assert len(numbers) == len(set(numbers))


def test_receipt_ids_are_unique(
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    ids: list[str] = [row.goods_receipt_id for row in goods_receipts]

    assert len(ids) == len(set(ids))


def test_receipt_numbers_are_unique(
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    numbers: list[str] = [row.receipt_number for row in goods_receipts]

    assert len(numbers) == len(set(numbers))


def test_every_shipment_has_one_receipt(
    shipments: tuple[SupplierShipment, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    assert {row.shipment_id for row in shipments} == {row.shipment_id for row in goods_receipts}


def test_cancelled_lines_have_no_shipments(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
) -> None:
    cancelled: set[str] = {
        row.purchase_order_line_id
        for row in line_fulfilments
        if (row.fulfilment_outcome == "CANCELLED")
    }

    assert all(shipment.purchase_order_line_id not in cancelled for shipment in shipments)


def test_split_lines_have_two_shipments(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
) -> None:
    grouped: dict[
        str,
        list[SupplierShipment],
    ] = defaultdict(list)

    for shipment in shipments:
        grouped[shipment.purchase_order_line_id].append(shipment)

    for fulfilment in line_fulfilments:
        if fulfilment.fulfilment_outcome == "SPLIT_FULL":
            assert len(grouped[fulfilment.purchase_order_line_id]) == 2


def test_split_lines_fully_fulfil_order(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        row.purchase_order_line_id: row for row in purchase_order_lines
    }

    grouped: dict[
        str,
        list[SupplierShipment],
    ] = defaultdict(list)

    for shipment in shipments:
        grouped[shipment.purchase_order_line_id].append(shipment)

    for fulfilment in line_fulfilments:
        if fulfilment.fulfilment_outcome != "SPLIT_FULL":
            continue

        line_id: str = fulfilment.purchase_order_line_id

        assert (
            sum(row.shipped_quantity for row in grouped[line_id])
            == lines_by_id[line_id].ordered_quantity
        )


def test_short_shipments_are_below_ordered_quantity(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        row.purchase_order_line_id: row for row in purchase_order_lines
    }

    shipments_by_line: dict[str, SupplierShipment] = {
        row.purchase_order_line_id: row
        for row in shipments
        if (row.fulfilment_outcome == "SHORT_SHIPPED")
    }

    for fulfilment in line_fulfilments:
        if fulfilment.fulfilment_outcome != "SHORT_SHIPPED":
            continue

        line_id: str = fulfilment.purchase_order_line_id

        assert (
            0 < shipments_by_line[line_id].shipped_quantity < lines_by_id[line_id].ordered_quantity
        )


def test_on_time_full_arrives_on_expected_date(
    line_fulfilments: tuple[PurchaseOrderLineFulfilment, ...],
    shipments: tuple[SupplierShipment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        row.purchase_order_line_id: row for row in purchase_order_lines
    }

    for shipment in shipments:
        if shipment.fulfilment_outcome == "ON_TIME_FULL":
            assert (
                shipment.delivered_date
                == lines_by_id[shipment.purchase_order_line_id].expected_delivery_date
            )


def test_early_full_arrives_before_expected_date(
    shipments: tuple[SupplierShipment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        row.purchase_order_line_id: row for row in purchase_order_lines
    }

    for shipment in shipments:
        if shipment.fulfilment_outcome == "EARLY_FULL":
            assert (
                shipment.delivered_date
                < lines_by_id[shipment.purchase_order_line_id].expected_delivery_date
            )


def test_late_full_arrives_after_expected_date(
    shipments: tuple[SupplierShipment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    lines_by_id: dict[str, PurchaseOrderLine] = {
        row.purchase_order_line_id: row for row in purchase_order_lines
    }

    for shipment in shipments:
        if shipment.fulfilment_outcome == "LATE_FULL":
            assert (
                shipment.delivered_date
                > lines_by_id[shipment.purchase_order_line_id].expected_delivery_date
            )


def test_receipts_match_shipments(
    shipments: tuple[SupplierShipment, ...],
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    shipments_by_id: dict[str, SupplierShipment] = {row.shipment_id: row for row in shipments}

    for receipt in goods_receipts:
        shipment: SupplierShipment = shipments_by_id[receipt.shipment_id]

        assert receipt.received_quantity == shipment.shipped_quantity

        assert receipt.received_date == shipment.delivered_date


def test_future_receipts_can_extend_beyond_simulation(
    context: SimulationContext,
    goods_receipts: tuple[GoodsReceipt, ...],
) -> None:
    assert any(receipt.received_date > context.config.end_date for receipt in goods_receipts)


def test_line_input_order_does_not_change_results(
    context: SimulationContext,
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    first: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ] = generate_fulfilment(
        context,
        orders=purchase_orders,
        lines=purchase_order_lines,
    )

    second: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ] = generate_fulfilment(
        context,
        orders=purchase_orders,
        lines=tuple(reversed(purchase_order_lines)),
    )

    assert first == second


def test_order_input_order_does_not_change_results(
    context: SimulationContext,
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    first: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ] = generate_fulfilment(
        context,
        orders=purchase_orders,
        lines=purchase_order_lines,
    )

    second: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ] = generate_fulfilment(
        context,
        orders=tuple(reversed(purchase_orders)),
        lines=purchase_order_lines,
    )

    assert first == second
