import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_CEILING, Decimal

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    DemandProfile,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.procurement.purchase_order_config import (
    DEFAULT_PURCHASE_ORDER_CONFIG,
    PurchaseOrderSimulationConfig,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)


@dataclass(frozen=True, slots=True)
class _PlannedOrderLine:
    assortment: ProductMarketAssortment
    sourcing: SourcingAgreement
    order_date: date
    ordered_quantity: int
    expected_delivery_date: date


def generate_purchase_orders(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    sourcing_agreements: tuple[SourcingAgreement, ...],
    demand_profiles: tuple[DemandProfile, ...],
    *,
    config: PurchaseOrderSimulationConfig = (DEFAULT_PURCHASE_ORDER_CONFIG),
) -> tuple[
    tuple[PurchaseOrder, ...],
    tuple[PurchaseOrderLine, ...],
]:
    sourcing_by_assortment: dict[str, tuple[SourcingAgreement, ...]] = _sourcing_by_assortment(
        agreements=sourcing_agreements
    )

    demand_by_assortment: dict[str, DemandProfile] = {
        profile.assortment_id: profile for profile in demand_profiles
    }

    planned_lines: list[_PlannedOrderLine] = []

    for assortment in sorted(
        assortments,
        key=lambda row: (
            row.market_code,
            row.sku,
        ),
    ):
        sourcing: tuple[SourcingAgreement, ...] = sourcing_by_assortment[assortment.assortment_id]

        demand: DemandProfile = demand_by_assortment[assortment.assortment_id]

        planned_lines.extend(
            _plan_assortment_orders(
                context=context,
                assortment=assortment,
                sourcing=sourcing,
                demand=demand,
                config=config,
            )
        )

    return _build_purchase_orders(
        context=context,
        planned_lines=planned_lines,
    )


def _sourcing_by_assortment(
    agreements: tuple[SourcingAgreement, ...],
) -> dict[
    str,
    tuple[SourcingAgreement, ...],
]:
    grouped: dict[
        str,
        list[SourcingAgreement],
    ] = defaultdict(list)

    for agreement in agreements:
        grouped[agreement.assortment_id].append(agreement)

    return {
        assortment_id: tuple(
            sorted(
                rows,
                key=lambda row: _role_order(role=row.sourcing_role),
            )
        )
        for assortment_id, rows in grouped.items()
    }


def _role_order(
    role: str,
) -> int:
    return {
        "PRIMARY": 1,
        "SECONDARY": 2,
        "BACKUP": 3,
    }[role]


def _replenishment_cycle_days(
    *,
    demand: DemandProfile,
    primary: SourcingAgreement,
    config: PurchaseOrderSimulationConfig,
) -> int:
    estimated_days_to_consume_moq: Decimal = (
        Decimal(value=primary.minimum_order_quantity) / demand.average_daily_units
    )

    required_days = int(estimated_days_to_consume_moq.to_integral_value(rounding=ROUND_CEILING))

    for cycle_days in config.cycle_options_days:
        if cycle_days >= required_days:
            return cycle_days

    return config.cycle_options_days[-1]


def _plan_assortment_orders(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    sourcing: tuple[SourcingAgreement, ...],
    demand: DemandProfile,
    config: PurchaseOrderSimulationConfig,
) -> list[_PlannedOrderLine]:
    primary: SourcingAgreement = next(row for row in sourcing if row.sourcing_role == "PRIMARY")

    cycle_days: int = _replenishment_cycle_days(
        demand=demand,
        primary=primary,
        config=config,
    )

    active_start: date = max(
        context.config.start_date,
        assortment.ranged_from,
    )

    active_end_exclusive: date = assortment.ranged_to or (
        context.config.end_date + timedelta(days=1)
    )

    simulation_end_exclusive: date = context.config.end_date + timedelta(days=1)

    active_end_exclusive = min(
        active_end_exclusive,
        simulation_end_exclusive,
    )

    if active_start >= active_end_exclusive:
        return []

    first_order_date: date = _first_order_date(
        context=context,
        assortment=assortment,
        active_start=active_start,
        cycle_days=cycle_days,
    )

    planned: list[_PlannedOrderLine] = []

    order_date: date = first_order_date

    while order_date < active_end_exclusive:
        source: SourcingAgreement = _select_source(
            context=context,
            assortment=assortment,
            sourcing=sourcing,
            order_date=order_date,
            config=config,
        )

        expected_delivery: date = order_date + timedelta(days=source.lead_time_days)

        if assortment.ranged_to is None or expected_delivery < assortment.ranged_to:
            quantity: int = _ordered_quantity(
                context=context,
                assortment=assortment,
                source=source,
                demand=demand,
                order_date=order_date,
                cycle_days=cycle_days,
                config=config,
            )

            planned.append(
                _PlannedOrderLine(
                    assortment=assortment,
                    sourcing=source,
                    order_date=order_date,
                    ordered_quantity=quantity,
                    expected_delivery_date=(expected_delivery),
                )
            )

        order_date += timedelta(days=cycle_days)

    return planned


def _first_order_date(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    active_start: date,
    cycle_days: int,
) -> date:
    if assortment.ranged_from >= context.config.start_date:
        return active_start

    rng = random.Random(
        x=context.seed_for(
            namespace=(f"procurement:po-phase:{assortment.market_code}:{assortment.sku}")
        )
    )

    weeks: int = max(
        1,
        cycle_days // 7,
    )

    offset_weeks: int = rng.randrange(start=weeks)

    return active_start + timedelta(days=offset_weeks * 7)


def _select_source(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    sourcing: tuple[SourcingAgreement, ...],
    order_date: date,
    config: PurchaseOrderSimulationConfig,
) -> SourcingAgreement:
    eligible: list[SourcingAgreement] = [
        row for row in sourcing if row.is_effective_on(value=order_date)
    ]

    if not eligible:
        raise ValueError(
            f"no sourcing agreement for {assortment.market_code} {assortment.sku} on {order_date}"
        )

    role_weights: dict[str, float] = {
        "PRIMARY": config.primary_weight,
        "SECONDARY": config.secondary_weight,
        "BACKUP": config.backup_weight,
    }

    rng = random.Random(
        x=context.seed_for(
            namespace=(
                "procurement:po-source:"
                f"{assortment.market_code}:"
                f"{assortment.sku}:"
                f"{order_date.isoformat()}"
            )
        )
    )

    return rng.choices(
        population=eligible,
        weights=[role_weights[row.sourcing_role] for row in eligible],
        k=1,
    )[0]


def _ordered_quantity(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    source: SourcingAgreement,
    demand: DemandProfile,
    order_date: date,
    cycle_days: int,
    config: PurchaseOrderSimulationConfig,
) -> int:
    rng = random.Random(
        x=context.seed_for(
            namespace=(
                "procurement:po-quantity:"
                f"{assortment.market_code}:"
                f"{assortment.sku}:"
                f"{order_date.isoformat()}"
            )
        )
    )

    factor = Decimal(
        value=str(
            object=rng.uniform(
                a=float(config.minimum_quantity_factor),
                b=float(config.maximum_quantity_factor),
            )
        )
    )

    expected_units: Decimal = demand.average_daily_units * Decimal(value=cycle_days) * factor

    required_units = int(expected_units.to_integral_value(rounding=ROUND_CEILING))

    required_units: int = max(
        1,
        required_units,
    )

    moq: int = source.minimum_order_quantity

    multiples: Decimal = (Decimal(value=required_units) / Decimal(value=moq)).to_integral_value(
        rounding=ROUND_CEILING
    )

    return int(multiples) * moq


def _build_purchase_orders(
    *,
    context: SimulationContext,
    planned_lines: list[_PlannedOrderLine],
) -> tuple[
    tuple[PurchaseOrder, ...],
    tuple[PurchaseOrderLine, ...],
]:
    grouped: dict[
        tuple[
            str,
            str,
            str,
            str,
            date,
        ],
        list[_PlannedOrderLine],
    ] = defaultdict(list)

    for planned in planned_lines:
        source: SourcingAgreement = planned.sourcing

        key: tuple[str, str, str, str, date] = (
            source.market_code,
            source.supplier_id,
            source.supplier_code,
            source.currency,
            planned.order_date,
        )

        grouped[key].append(planned)

    orders: list[PurchaseOrder] = []

    lines: list[PurchaseOrderLine] = []

    for (
        market_code,
        supplier_id,
        supplier_code,
        currency,
        order_date,
    ), planned_group in sorted(grouped.items()):
        supplier_token: str = supplier_code.replace("SUP-", "").replace("-", "")

        purchase_order_number: str = f"PO-{market_code}-{order_date:%Y%m%d}-{supplier_token}"

        purchase_order_id: str = context.ids.id_for(
            namespace="purchase_order",
            key=purchase_order_number,
            prefix="po",
        )

        orders.append(
            PurchaseOrder(
                purchase_order_id=(purchase_order_id),
                purchase_order_number=(purchase_order_number),
                market_code=market_code,
                supplier_id=supplier_id,
                supplier_code=supplier_code,
                currency=currency,
                order_date=order_date,
            )
        )

        ordered_group: list[_PlannedOrderLine] = sorted(
            planned_group,
            key=lambda row: row.assortment.sku,
        )

        for line_number, planned in enumerate(
            iterable=ordered_group,
            start=1,
        ):
            line_id: str = context.ids.id_for(
                namespace="purchase_order_line",
                key=(f"{purchase_order_number}:{planned.assortment.sku}"),
                prefix="pol",
            )

            lines.append(
                PurchaseOrderLine(
                    purchase_order_line_id=(line_id),
                    purchase_order_id=(purchase_order_id),
                    line_number=line_number,
                    assortment_id=(planned.assortment.assortment_id),
                    product_id=(planned.assortment.product_id),
                    sku=(planned.assortment.sku),
                    sourcing_id=(planned.sourcing.sourcing_id),
                    ordered_quantity=(planned.ordered_quantity),
                    unit_cost=(planned.sourcing.unit_cost),
                    currency=currency,
                    expected_delivery_date=(planned.expected_delivery_date),
                )
            )

    return (
        tuple(orders),
        tuple(lines),
    )
