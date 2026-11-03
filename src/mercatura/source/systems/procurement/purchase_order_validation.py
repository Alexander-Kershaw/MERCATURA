from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig
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
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def validate_purchase_orders(
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    sourcing_agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_orders(orders)

    _validate_unique_lines(lines)

    _validate_order_headers(
        orders,
        suppliers,
        context,
    )

    _validate_line_coverage_and_numbering(
        orders,
        lines,
    )

    _validate_line_business_rules(
        orders,
        lines,
        assortments,
        sourcing_agreements,
    )


def _validate_unique_orders(
    orders: tuple[PurchaseOrder, ...],
) -> None:
    order_ids: list[str] = [order.purchase_order_id for order in orders]

    if len(order_ids) != len(set(order_ids)):
        raise ValueError("duplicate purchase_order_id detected")

    order_numbers: list[str] = [order.purchase_order_number for order in orders]

    if len(order_numbers) != len(set(order_numbers)):
        raise ValueError("duplicate purchase_order_number detected")

    for order in orders:
        if not order.purchase_order_number.strip():
            raise ValueError("purchase_order_number cannot be empty")


def _validate_unique_lines(
    lines: tuple[PurchaseOrderLine, ...],
) -> None:
    line_ids: list[str] = [line.purchase_order_line_id for line in lines]

    if len(line_ids) != len(set(line_ids)):
        raise ValueError("duplicate purchase_order_line_id detected")


def _validate_order_headers(
    orders: tuple[PurchaseOrder, ...],
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    markets: dict[str, MarketConfig] = {
        market.market_code: market for market in context.config.markets
    }

    suppliers_by_id: dict[str, Supplier] = {
        supplier.supplier_id: supplier for supplier in suppliers
    }

    for order in orders:
        market: MarketConfig | None = markets.get(order.market_code)

        if market is None:
            raise ValueError(f"unknown purchase order market: {order.market_code}")

        if order.currency != market.currency:
            raise ValueError(f"{order.purchase_order_number} uses incorrect market currency")

        supplier: Supplier | None = suppliers_by_id.get(order.supplier_id)

        if supplier is None:
            raise ValueError(f"{order.purchase_order_number} references unknown supplier")

        if order.supplier_code != supplier.supplier_code:
            raise ValueError(
                f"{order.purchase_order_number} supplier code does not match supplier master"
            )

        if not supplier.is_active_on(value=order.order_date):
            raise ValueError(
                f"{order.purchase_order_number} uses supplier outside its active lifecycle"
            )

        if not (context.config.start_date <= order.order_date <= context.config.end_date):
            raise ValueError(
                f"{order.purchase_order_number} order date is outside the simulation window"
            )


def _validate_line_coverage_and_numbering(
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
) -> None:
    order_ids: set[str] = {order.purchase_order_id for order in orders}

    grouped: dict[
        str,
        list[PurchaseOrderLine],
    ] = defaultdict(list)

    for line in lines:
        if line.purchase_order_id not in order_ids:
            raise ValueError("purchase order line references unknown purchase order")

        grouped[line.purchase_order_id].append(line)

    for order in orders:
        order_lines: list[PurchaseOrderLine] = grouped.get(
            order.purchase_order_id,
            [],
        )

        if not order_lines:
            raise ValueError(f"{order.purchase_order_number} contains no purchase order lines")

        ordered_lines: list[PurchaseOrderLine] = sorted(
            order_lines,
            key=lambda row: row.line_number,
        )

        actual_numbers: list[int] = [line.line_number for line in ordered_lines]

        expected_numbers: list[int] = list(
            range(
                1,
                len(ordered_lines) + 1,
            )
        )

        if actual_numbers != expected_numbers:
            raise ValueError(f"{order.purchase_order_number} has invalid line numbering")

        assortment_ids: list[str] = [line.assortment_id for line in ordered_lines]

        if len(assortment_ids) != len(set(assortment_ids)):
            raise ValueError(f"{order.purchase_order_number} contains duplicate assortment lines")


def _validate_line_business_rules(
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    sourcing_agreements: tuple[SourcingAgreement, ...],
) -> None:
    orders_by_id: dict[str, PurchaseOrder] = {order.purchase_order_id: order for order in orders}

    assortments_by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    sourcing_by_id: dict[str, SourcingAgreement] = {
        agreement.sourcing_id: agreement for agreement in sourcing_agreements
    }

    for line in lines:
        order: PurchaseOrder = orders_by_id[line.purchase_order_id]

        assortment: ProductMarketAssortment | None = assortments_by_id.get(line.assortment_id)

        if assortment is None:
            raise ValueError("purchase order line references unknown assortment")

        sourcing: SourcingAgreement | None = sourcing_by_id.get(line.sourcing_id)

        if sourcing is None:
            raise ValueError("purchase order line references unknown sourcing agreement")

        _validate_line_metadata(
            line=line,
            order=order,
            assortment=assortment,
            sourcing=sourcing,
        )

        _validate_line_quantity(
            line=line,
            sourcing=sourcing,
        )

        _validate_line_cost(
            line=line,
            sourcing=sourcing,
        )

        _validate_line_dates(
            line=line,
            order=order,
            assortment=assortment,
            sourcing=sourcing,
        )


def _validate_line_metadata(
    *,
    line: PurchaseOrderLine,
    order: PurchaseOrder,
    assortment: ProductMarketAssortment,
    sourcing: SourcingAgreement,
) -> None:
    if line.product_id != assortment.product_id:
        raise ValueError("purchase order line product does not match assortment")

    if line.sku != assortment.sku:
        raise ValueError("purchase order line SKU does not match assortment")

    if sourcing.assortment_id != assortment.assortment_id:
        raise ValueError("sourcing agreement does not match purchase order assortment")

    if sourcing.product_id != line.product_id:
        raise ValueError("sourcing product does not match purchase order line")

    if sourcing.sku != line.sku:
        raise ValueError("sourcing SKU does not match purchase order line")

    if assortment.market_code != order.market_code:
        raise ValueError("purchase order market does not match assortment market")

    if sourcing.market_code != order.market_code:
        raise ValueError("purchase order market does not match sourcing market")

    if sourcing.supplier_id != order.supplier_id:
        raise ValueError("purchase order supplier does not match sourcing agreement")

    if sourcing.supplier_code != order.supplier_code:
        raise ValueError("purchase order supplier code does not match sourcing agreement")

    if line.currency != order.currency:
        raise ValueError("purchase order line currency does not match purchase order")

    if sourcing.currency != order.currency:
        raise ValueError("purchase order currency does not match sourcing agreement")


def _validate_line_quantity(
    *,
    line: PurchaseOrderLine,
    sourcing: SourcingAgreement,
) -> None:
    if not isinstance(
        line.ordered_quantity,
        int,
    ) or isinstance(
        line.ordered_quantity,
        bool,
    ):
        raise ValueError("ordered quantity must be an integer")

    if line.ordered_quantity <= 0:
        raise ValueError("ordered quantity must be positive")

    moq: int = sourcing.minimum_order_quantity

    if moq <= 0:
        raise ValueError("sourcing agreement has invalid MOQ")

    if line.ordered_quantity % moq != 0:
        raise ValueError("ordered quantity must be a multiple of sourcing MOQ")


def _validate_line_cost(
    *,
    line: PurchaseOrderLine,
    sourcing: SourcingAgreement,
) -> None:
    if not isinstance(
        line.unit_cost,
        Decimal,
    ):
        raise ValueError("purchase order unit cost must use Decimal")

    if line.unit_cost <= Decimal(value="0"):
        raise ValueError("purchase order unit cost must be positive")

    if line.unit_cost != sourcing.unit_cost:
        raise ValueError("purchase order unit cost does not match sourcing agreement")


def _validate_line_dates(
    *,
    line: PurchaseOrderLine,
    order: PurchaseOrder,
    assortment: ProductMarketAssortment,
    sourcing: SourcingAgreement,
) -> None:
    if not sourcing.is_effective_on(value=order.order_date):
        raise ValueError("sourcing agreement is not effective on purchase order date")

    if order.order_date < assortment.ranged_from:
        raise ValueError("purchase order predates assortment lifecycle")

    if assortment.ranged_to is not None and order.order_date >= assortment.ranged_to:
        raise ValueError("purchase order occurs after assortment withdrawal")

    if sourcing.lead_time_days <= 0:
        raise ValueError("sourcing agreement has invalid lead time")

    expected_delivery = order.order_date + timedelta(days=sourcing.lead_time_days)

    if line.expected_delivery_date != expected_delivery:
        raise ValueError("incorrect expected delivery date")

    if assortment.ranged_to is not None and line.expected_delivery_date >= assortment.ranged_to:
        raise ValueError("expected delivery occurs after assortment withdrawal")
