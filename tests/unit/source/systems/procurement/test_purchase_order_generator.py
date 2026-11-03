from collections import Counter
from datetime import timedelta
from decimal import Decimal

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
from mercatura.source.systems.procurement.purchase_order_generator import (
    generate_purchase_orders,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)


def normalize_orders(
    orders: tuple[PurchaseOrder, ...],
) -> list[PurchaseOrder]:
    return sorted(
        orders,
        key=lambda row: row.purchase_order_id,
    )


def normalize_lines(
    lines: tuple[PurchaseOrderLine, ...],
) -> list[PurchaseOrderLine]:
    return sorted(
        lines,
        key=lambda row: row.purchase_order_line_id,
    )


def test_generation_is_deterministic(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    demand_profiles: tuple[DemandProfile, ...],
) -> None:
    first_orders, first_lines = generate_purchase_orders(
        context,
        assortments,
        agreements,
        demand_profiles,
    )

    second_orders, second_lines = generate_purchase_orders(
        context,
        assortments,
        agreements,
        demand_profiles,
    )

    assert first_orders == second_orders
    assert first_lines == second_lines


def test_purchase_order_ids_are_unique(
    purchase_orders: tuple[PurchaseOrder, ...],
) -> None:
    identifiers = [order.purchase_order_id for order in purchase_orders]

    assert len(identifiers) == len(set(identifiers))


def test_purchase_order_numbers_are_unique(
    purchase_orders: tuple[PurchaseOrder, ...],
) -> None:
    numbers = [order.purchase_order_number for order in purchase_orders]

    assert len(numbers) == len(set(numbers))


def test_purchase_order_line_ids_are_unique(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    identifiers = [line.purchase_order_line_id for line in purchase_order_lines]

    assert len(identifiers) == len(set(identifiers))


def test_every_order_has_at_least_one_line(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    populated = {line.purchase_order_id for line in purchase_order_lines}

    assert all(order.purchase_order_id in populated for order in purchase_orders)


def test_multiple_line_purchase_orders_exist(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    counts = Counter(line.purchase_order_id for line in purchase_order_lines)

    assert any(count > 1 for count in counts.values())


def test_order_dates_are_inside_simulation(
    context: SimulationContext,
    purchase_orders: tuple[PurchaseOrder, ...],
) -> None:
    assert all(
        context.config.start_date <= order.order_date <= context.config.end_date
        for order in purchase_orders
    )


def test_historical_assortments_generate_activity(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    assortment_by_id = {row.assortment_id: row for row in assortments}

    assert any(
        assortment_by_id[line.assortment_id].ranged_from < context.config.start_date
        for line in purchase_order_lines
    )


def test_new_assortments_generate_activity(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    assortment_by_id = {row.assortment_id: row for row in assortments}

    assert any(
        assortment_by_id[line.assortment_id].ranged_from >= context.config.start_date
        for line in purchase_order_lines
    )


def test_order_quantities_are_positive(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    assert all(line.ordered_quantity > 0 for line in purchase_order_lines)


def test_order_quantities_respect_moq(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    sourcing_by_id = {agreement.sourcing_id: agreement for agreement in agreements}

    for line in purchase_order_lines:
        sourcing = sourcing_by_id[line.sourcing_id]

        assert line.ordered_quantity % sourcing.minimum_order_quantity == 0


def test_unit_cost_matches_sourcing_agreement(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    sourcing_by_id = {agreement.sourcing_id: agreement for agreement in agreements}

    for line in purchase_order_lines:
        assert line.unit_cost == sourcing_by_id[line.sourcing_id].unit_cost


def test_unit_costs_use_decimal(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    assert all(
        isinstance(
            line.unit_cost,
            Decimal,
        )
        for line in purchase_order_lines
    )


def test_expected_delivery_matches_lead_time(
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    orders_by_id = {order.purchase_order_id: order for order in purchase_orders}

    sourcing_by_id = {agreement.sourcing_id: agreement for agreement in agreements}

    for line in purchase_order_lines:
        order = orders_by_id[line.purchase_order_id]

        sourcing = sourcing_by_id[line.sourcing_id]

        assert line.expected_delivery_date == order.order_date + timedelta(
            days=(sourcing.lead_time_days)
        )


def test_primary_source_is_used_most_often(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    sourcing_by_id = {agreement.sourcing_id: agreement for agreement in agreements}

    counts = Counter(
        sourcing_by_id[line.sourcing_id].sourcing_role for line in purchase_order_lines
    )

    assert counts["PRIMARY"] > counts["SECONDARY"]

    assert counts["SECONDARY"] > counts["BACKUP"]


def test_secondary_source_is_used(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    sourcing_by_id = {row.sourcing_id: row for row in agreements}

    assert any(
        sourcing_by_id[line.sourcing_id].sourcing_role == "SECONDARY"
        for line in purchase_order_lines
    )


def test_backup_source_is_used(
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    sourcing_by_id = {row.sourcing_id: row for row in agreements}

    assert any(
        sourcing_by_id[line.sourcing_id].sourcing_role == "BACKUP" for line in purchase_order_lines
    )


def test_assortment_input_order_does_not_change_results(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    demand_profiles: tuple[DemandProfile, ...],
) -> None:
    first_orders, first_lines = generate_purchase_orders(
        context,
        assortments,
        agreements,
        demand_profiles,
    )

    second_orders, second_lines = generate_purchase_orders(
        context,
        tuple(reversed(assortments)),
        agreements,
        demand_profiles,
    )

    assert normalize_orders(first_orders) == normalize_orders(second_orders)

    assert normalize_lines(first_lines) == normalize_lines(second_lines)


def test_sourcing_input_order_does_not_change_results(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    demand_profiles: tuple[DemandProfile, ...],
) -> None:
    first_orders, first_lines = generate_purchase_orders(
        context,
        assortments,
        agreements,
        demand_profiles,
    )

    second_orders, second_lines = generate_purchase_orders(
        context,
        assortments,
        tuple(reversed(agreements)),
        demand_profiles,
    )

    assert normalize_orders(first_orders) == normalize_orders(second_orders)

    assert normalize_lines(first_lines) == normalize_lines(second_lines)


def test_demand_input_order_does_not_change_results(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    demand_profiles: tuple[DemandProfile, ...],
) -> None:
    first_orders, first_lines = generate_purchase_orders(
        context,
        assortments,
        agreements,
        demand_profiles,
    )

    second_orders, second_lines = generate_purchase_orders(
        context,
        assortments,
        agreements,
        tuple(reversed(demand_profiles)),
    )

    assert normalize_orders(first_orders) == normalize_orders(second_orders)

    assert normalize_lines(first_lines) == normalize_lines(second_lines)
