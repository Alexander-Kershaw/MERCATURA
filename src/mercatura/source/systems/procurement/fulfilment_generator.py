import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.procurement.fulfilment_config import (
    DEFAULT_FULFILMENT_CONFIG,
    FulfilmentSimulationConfig,
)
from mercatura.source.systems.procurement.fulfilment_model import (
    FulfilmentOutcome,
    GoodsReceipt,
    PurchaseOrderLineFulfilment,
    SupplierShipment,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)


def generate_fulfilment(
    context: SimulationContext,
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    *,
    config: FulfilmentSimulationConfig = (DEFAULT_FULFILMENT_CONFIG),
) -> tuple[
    tuple[PurchaseOrderLineFulfilment, ...],
    tuple[SupplierShipment, ...],
    tuple[GoodsReceipt, ...],
]:
    orders_by_id: dict[str, PurchaseOrder] = {order.purchase_order_id: order for order in orders}

    fulfilments: list[PurchaseOrderLineFulfilment] = []

    shipments: list[SupplierShipment] = []

    receipts: list[GoodsReceipt] = []

    for line in sorted(
        lines,
        key=lambda row: row.purchase_order_line_id,
    ):
        order: PurchaseOrder = orders_by_id[line.purchase_order_id]

        rng = random.Random(
            x=context.seed_for(namespace=(f"procurement:fulfilment:{line.purchase_order_line_id}"))
        )

        outcome = _select_outcome(
            rng=rng,
            config=config,
        )

        fulfilments.append(
            _build_line_fulfilment(
                context=context,
                order=order,
                line=line,
                outcome=outcome,
            )
        )

        line_shipments: list[SupplierShipment] = _generate_line_shipments(
            context=context,
            order=order,
            line=line,
            outcome=outcome,
            config=config,
            rng=rng,
        )

        shipments.extend(line_shipments)

        receipts.extend(
            _generate_receipts(
                context=context,
                order=order,
                line=line,
                shipments=line_shipments,
            )
        )

    return (
        tuple(fulfilments),
        tuple(shipments),
        tuple(receipts),
    )


def _build_line_fulfilment(
    *,
    context: SimulationContext,
    order: PurchaseOrder,
    line: PurchaseOrderLine,
    outcome: FulfilmentOutcome,
) -> PurchaseOrderLineFulfilment:
    fulfilment_id: str = context.ids.id_for(
        namespace="purchase_order_line_fulfilment",
        key=line.purchase_order_line_id,
        prefix="ful",
    )

    return PurchaseOrderLineFulfilment(
        fulfilment_id=fulfilment_id,
        purchase_order_id=(order.purchase_order_id),
        purchase_order_line_id=(line.purchase_order_line_id),
        fulfilment_outcome=outcome,
    )


def _select_outcome(
    *,
    rng: random.Random,
    config: FulfilmentSimulationConfig,
) -> FulfilmentOutcome:
    value: float = rng.random()

    thresholds: tuple[
        tuple[float, str],
        tuple[float, str],
        tuple[float, str],
        tuple[float, str],
        tuple[float, str],
        tuple[float, str],
    ] = (
        (
            config.on_time_full_probability,
            "ON_TIME_FULL",
        ),
        (
            config.early_full_probability,
            "EARLY_FULL",
        ),
        (
            config.late_full_probability,
            "LATE_FULL",
        ),
        (
            config.split_full_probability,
            "SPLIT_FULL",
        ),
        (
            config.short_shipped_probability,
            "SHORT_SHIPPED",
        ),
        (
            config.cancelled_probability,
            "CANCELLED",
        ),
    )

    cumulative = 0.0

    for probability, outcome in thresholds:
        cumulative += probability

        if value < cumulative:
            return outcome

    return "CANCELLED"


def _generate_line_shipments(
    *,
    context: SimulationContext,
    order: PurchaseOrder,
    line: PurchaseOrderLine,
    outcome: FulfilmentOutcome,
    config: FulfilmentSimulationConfig,
    rng: random.Random,
) -> list[SupplierShipment]:
    if outcome == "CANCELLED":
        return []

    if outcome == "SPLIT_FULL":
        return _generate_split_shipments(
            context=context,
            order=order,
            line=line,
            outcome=outcome,
            config=config,
            rng=rng,
        )

    if outcome == "SHORT_SHIPPED":
        quantity: int = _short_quantity(
            ordered_quantity=(line.ordered_quantity),
            config=config,
            rng=rng,
        )
    else:
        quantity = line.ordered_quantity

    delivered_date: date = _delivery_date(
        order=order,
        line=line,
        outcome=outcome,
        config=config,
        rng=rng,
    )

    return [
        _build_shipment(
            context=context,
            order=order,
            line=line,
            sequence=1,
            quantity=quantity,
            delivered_date=delivered_date,
            outcome=outcome,
            rng=rng,
        )
    ]


def _delivery_date(
    *,
    order: PurchaseOrder,
    line: PurchaseOrderLine,
    outcome: FulfilmentOutcome,
    config: FulfilmentSimulationConfig,
    rng: random.Random,
) -> date:
    expected: date = line.expected_delivery_date

    if outcome == "ON_TIME_FULL":
        return expected

    if outcome == "EARLY_FULL":
        available_days: int = max(
            0,
            (expected - order.order_date).days - 1,
        )

        maximum_early: int = min(
            config.maximum_early_days,
            available_days,
        )

        if maximum_early == 0:
            return expected

        return expected - timedelta(
            days=rng.randint(
                a=1,
                b=maximum_early,
            )
        )

    if outcome == "LATE_FULL":
        return expected + timedelta(
            days=rng.randint(
                a=1,
                b=config.maximum_late_days,
            )
        )

    if outcome == "SHORT_SHIPPED":
        delay: int = rng.randint(
            a=0,
            b=config.maximum_late_days // 2,
        )

        return expected + timedelta(days=delay)

    raise ValueError(f"unsupported single-shipment outcome: {outcome}")


def _shipment_date(
    *,
    order_date: date,
    delivered_date: date,
    rng: random.Random,
) -> date:
    available_days: int = (delivered_date - order_date).days

    if available_days <= 0:
        return order_date

    offset: int = rng.randint(
        a=0,
        b=max(
            0,
            available_days - 1,
        ),
    )

    return order_date + timedelta(days=offset)


def _build_shipment(
    *,
    context: SimulationContext,
    order: PurchaseOrder,
    line: PurchaseOrderLine,
    sequence: int,
    quantity: int,
    delivered_date: date,
    outcome: FulfilmentOutcome,
    rng: random.Random,
) -> SupplierShipment:
    shipment_number: str = (
        f"SHP-{order.purchase_order_number}-{line.line_number:03d}-{sequence:02d}"
    )

    shipment_id: str = context.ids.id_for(
        namespace="supplier_shipment",
        key=shipment_number,
        prefix="shp",
    )

    shipped_date: date = _shipment_date(
        order_date=order.order_date,
        delivered_date=delivered_date,
        rng=rng,
    )

    return SupplierShipment(
        shipment_id=shipment_id,
        shipment_number=shipment_number,
        purchase_order_id=(order.purchase_order_id),
        purchase_order_line_id=(line.purchase_order_line_id),
        sourcing_id=line.sourcing_id,
        supplier_id=order.supplier_id,
        supplier_code=order.supplier_code,
        market_code=order.market_code,
        shipment_sequence=sequence,
        shipped_quantity=quantity,
        shipped_date=shipped_date,
        delivered_date=delivered_date,
        fulfilment_outcome=outcome,
    )


def _short_quantity(
    *,
    ordered_quantity: int,
    config: FulfilmentSimulationConfig,
    rng: random.Random,
) -> int:
    fraction = Decimal(
        value=str(
            object=rng.uniform(
                a=float(config.short_minimum_fraction),
                b=float(config.short_maximum_fraction),
            )
        )
    )

    quantity = int(
        (Decimal(value=ordered_quantity) * fraction).to_integral_value(rounding=ROUND_HALF_UP)
    )

    return min(
        ordered_quantity - 1,
        max(
            1,
            quantity,
        ),
    )


def _generate_split_shipments(
    *,
    context: SimulationContext,
    order: PurchaseOrder,
    line: PurchaseOrderLine,
    outcome: FulfilmentOutcome,
    config: FulfilmentSimulationConfig,
    rng: random.Random,
) -> list[SupplierShipment]:
    fraction = Decimal(
        value=str(
            object=rng.uniform(
                a=float(config.split_minimum_fraction),
                b=float(config.split_maximum_fraction),
            )
        )
    )

    first_quantity = int(
        (Decimal(value=line.ordered_quantity) * fraction).to_integral_value(rounding=ROUND_HALF_UP)
    )

    first_quantity: int = min(
        line.ordered_quantity - 1,
        max(
            1,
            first_quantity,
        ),
    )

    second_quantity: int = line.ordered_quantity - first_quantity

    first_offset: int = rng.randint(
        a=-2,
        b=2,
    )

    first_delivery: date = line.expected_delivery_date + timedelta(days=first_offset)

    if first_delivery <= order.order_date:
        first_delivery = order.order_date + timedelta(days=1)

    second_delivery: date = first_delivery + timedelta(
        days=rng.randint(
            a=1,
            b=config.split_maximum_delay_days,
        )
    )

    first: SupplierShipment = _build_shipment(
        context=context,
        order=order,
        line=line,
        sequence=1,
        quantity=first_quantity,
        delivered_date=first_delivery,
        outcome=outcome,
        rng=rng,
    )

    second: SupplierShipment = _build_shipment(
        context=context,
        order=order,
        line=line,
        sequence=2,
        quantity=second_quantity,
        delivered_date=second_delivery,
        outcome=outcome,
        rng=rng,
    )

    return [
        first,
        second,
    ]


def _generate_receipts(
    *,
    context: SimulationContext,
    order: PurchaseOrder,
    line: PurchaseOrderLine,
    shipments: list[SupplierShipment],
) -> list[GoodsReceipt]:
    receipts: list[GoodsReceipt] = []

    for shipment in shipments:
        receipt_number: str = (
            f"GRN-"
            f"{order.purchase_order_number}-"
            f"{line.line_number:03d}-"
            f"{shipment.shipment_sequence:02d}"
        )

        receipt_id: str = context.ids.id_for(
            namespace="goods_receipt",
            key=receipt_number,
            prefix="grn",
        )

        receipts.append(
            GoodsReceipt(
                goods_receipt_id=(receipt_id),
                receipt_number=(receipt_number),
                shipment_id=(shipment.shipment_id),
                purchase_order_id=(order.purchase_order_id),
                purchase_order_line_id=(line.purchase_order_line_id),
                market_code=(order.market_code),
                receipt_sequence=(shipment.shipment_sequence),
                received_quantity=(shipment.shipped_quantity),
                received_date=(shipment.delivered_date),
            )
        )

    return receipts
