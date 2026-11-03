from collections import Counter
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from typing import cast

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)
from mercatura.source.systems.procurement.purchase_order_validation import (
    validate_purchase_orders,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def replace_order(
    orders: tuple[PurchaseOrder, ...],
    replacement: PurchaseOrder,
) -> tuple[PurchaseOrder, ...]:
    return tuple(
        replacement if order.purchase_order_id == replacement.purchase_order_id else order
        for order in orders
    )


def replace_line(
    lines: tuple[PurchaseOrderLine, ...],
    replacement: PurchaseOrderLine,
) -> tuple[PurchaseOrderLine, ...]:
    return tuple(
        replacement if line.purchase_order_line_id == replacement.purchase_order_line_id else line
        for line in lines
    )


def replace_sourcing(
    agreements: tuple[SourcingAgreement, ...],
    replacement: SourcingAgreement,
) -> tuple[SourcingAgreement, ...]:
    return tuple(
        replacement if agreement.sourcing_id == replacement.sourcing_id else agreement
        for agreement in agreements
    )


def validate(
    *,
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    validate_purchase_orders(
        orders,
        lines,
        assortments,
        agreements,
        suppliers,
        context,
    )


def test_valid_dataset_passes_validation(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    validate(
        orders=purchase_orders,
        lines=purchase_order_lines,
        assortments=assortments,
        agreements=agreements,
        suppliers=suppliers,
        context=context,
    )


def test_rejects_duplicate_order_id(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    broken = (
        *purchase_orders,
        purchase_orders[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate purchase_order_id",
    ):
        validate(
            orders=broken,
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_duplicate_order_number(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_orders[1],
        purchase_order_number=(purchase_orders[0].purchase_order_number),
    )

    broken = replace_order(
        purchase_orders,
        replacement,
    )

    with pytest.raises(
        ValueError,
        match="duplicate purchase_order_number",
    ):
        validate(
            orders=broken,
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_duplicate_line_id(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    broken = (
        *purchase_order_lines,
        purchase_order_lines[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate purchase_order_line_id",
    ):
        validate(
            orders=purchase_orders,
            lines=broken,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_unknown_supplier(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_orders[0],
        supplier_id="sup_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown supplier",
    ):
        validate(
            orders=replace_order(
                purchase_orders,
                replacement,
            ),
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_supplier_code_mismatch(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_orders[0],
        supplier_code="SUP-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="supplier code",
    ):
        validate(
            orders=replace_order(
                purchase_orders,
                replacement,
            ),
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_unknown_market(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_orders[0],
        market_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="unknown purchase order market",
    ):
        validate(
            orders=replace_order(
                purchase_orders,
                replacement,
            ),
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_wrong_header_currency(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    order = purchase_orders[0]

    wrong_currency = "USD" if order.currency != "USD" else "GBP"

    replacement = replace(
        order,
        currency=wrong_currency,
    )

    with pytest.raises(
        ValueError,
        match="incorrect market currency",
    ):
        validate(
            orders=replace_order(
                purchase_orders,
                replacement,
            ),
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_order_before_simulation(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_orders[0],
        order_date=(context.config.start_date - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="outside the simulation window",
    ):
        validate(
            orders=replace_order(
                purchase_orders,
                replacement,
            ),
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_order_after_simulation(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_orders[0],
        order_date=(context.config.end_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="outside the simulation window",
    ):
        validate(
            orders=replace_order(
                purchase_orders,
                replacement,
            ),
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_order_without_lines(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    target = purchase_orders[0]

    broken_lines = tuple(
        line for line in purchase_order_lines if line.purchase_order_id != target.purchase_order_id
    )

    with pytest.raises(
        ValueError,
        match="contains no purchase order lines",
    ):
        validate(
            orders=purchase_orders,
            lines=broken_lines,
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_unknown_purchase_order(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        purchase_order_id="po_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown purchase order",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_unknown_assortment(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        assortment_id="ast_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown assortment",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_unknown_sourcing_agreement(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        sourcing_id="src_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown sourcing agreement",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_product_mismatch(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        product_id="prd_wrong",
    )

    with pytest.raises(
        ValueError,
        match="product does not match assortment",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_sku_mismatch(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        sku="MRC-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="SKU",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_zero_quantity(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        ordered_quantity=0,
    )

    with pytest.raises(
        ValueError,
        match="ordered quantity must be positive",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_non_moq_quantity(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    target = purchase_order_lines[0]

    replacement = replace(
        target,
        ordered_quantity=(target.ordered_quantity + 1),
    )

    with pytest.raises(
        ValueError,
        match="multiple of sourcing MOQ",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_non_decimal_unit_cost(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    replacement = replace(
        purchase_order_lines[0],
        unit_cost=cast(
            Decimal,
            1.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="must use Decimal",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_wrong_unit_cost(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    target = purchase_order_lines[0]

    replacement = replace(
        target,
        unit_cost=(target.unit_cost + Decimal("1")),
    )

    with pytest.raises(
        ValueError,
        match="does not match sourcing agreement",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_wrong_line_currency(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    target = purchase_order_lines[0]

    wrong_currency = "USD" if target.currency != "USD" else "GBP"

    replacement = replace(
        target,
        currency=wrong_currency,
    )

    with pytest.raises(
        ValueError,
        match="line currency",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_incorrect_expected_delivery_date(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    target = purchase_order_lines[0]

    replacement = replace(
        target,
        expected_delivery_date=(target.expected_delivery_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="incorrect expected delivery date",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_sourcing_not_effective_on_order_date(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    target_line = purchase_order_lines[0]

    target_order = next(
        order
        for order in purchase_orders
        if order.purchase_order_id == target_line.purchase_order_id
    )

    target_sourcing = next(
        agreement for agreement in agreements if agreement.sourcing_id == target_line.sourcing_id
    )

    broken_sourcing = replace(
        target_sourcing,
        effective_from=(target_order.order_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="not effective",
    ):
        validate(
            orders=purchase_orders,
            lines=purchase_order_lines,
            assortments=assortments,
            agreements=replace_sourcing(
                agreements,
                broken_sourcing,
            ),
            suppliers=suppliers,
            context=context,
        )


def test_rejects_invalid_line_numbering(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    counts = Counter(line.purchase_order_id for line in purchase_order_lines)

    order_id = next(identifier for identifier, count in counts.items() if count >= 2)

    target = next(
        line
        for line in purchase_order_lines
        if (line.purchase_order_id == order_id and line.line_number == 2)
    )

    replacement = replace(
        target,
        line_number=99,
    )

    with pytest.raises(
        ValueError,
        match="invalid line numbering",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_rejects_duplicate_assortment_on_same_order(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    counts = Counter(line.purchase_order_id for line in purchase_order_lines)

    order_id = next(identifier for identifier, count in counts.items() if count >= 2)

    order_lines = sorted(
        (line for line in purchase_order_lines if line.purchase_order_id == order_id),
        key=lambda row: row.line_number,
    )

    first = order_lines[0]
    second = order_lines[1]

    replacement = replace(
        second,
        assortment_id=first.assortment_id,
    )

    with pytest.raises(
        ValueError,
        match="duplicate assortment lines",
    ):
        validate(
            orders=purchase_orders,
            lines=replace_line(
                purchase_order_lines,
                replacement,
            ),
            assortments=assortments,
            agreements=agreements,
            suppliers=suppliers,
            context=context,
        )


def test_delivery_may_extend_beyond_simulation_end(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    sourcing_by_id = {agreement.sourcing_id: agreement for agreement in agreements}

    target_line = next(
        line
        for line in purchase_order_lines
        if (sourcing_by_id[line.sourcing_id].effective_to is None)
    )

    source = sourcing_by_id[target_line.sourcing_id]

    target_order = next(
        order
        for order in purchase_orders
        if order.purchase_order_id == target_line.purchase_order_id
    )

    modified_order = replace(
        target_order,
        order_date=(context.config.end_date),
    )

    modified_line = replace(
        target_line,
        line_number=1,
        expected_delivery_date=(context.config.end_date + timedelta(days=source.lead_time_days)),
    )

    assert modified_line.expected_delivery_date > context.config.end_date

    validate(
        orders=(modified_order,),
        lines=(modified_line,),
        assortments=assortments,
        agreements=agreements,
        suppliers=suppliers,
        context=context,
    )
