from collections import Counter, defaultdict
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
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.oms.config import (
    OMSSimulationConfig,
)
from mercatura.source.systems.oms.generator import (
    generate_orders,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderItem,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.store.model import (
    Store,
)

EXPECTED_ORDER_COUNTS = {
    "GB": 38_000,
    "DE": 23_000,
    "US": 37_000,
    "CN": 27_000,
    "NO": 5_000,
    "RU": 14_000,
    "JP": 19_000,
    "KR": 15_000,
    "FR": 22_000,
    "NL": 10_000,
    "PL": 11_000,
}


def test_expected_order_count(
    orders: tuple[Order, ...],
) -> None:
    assert len(orders) == 221_000


def test_expected_order_counts_by_market(
    orders: tuple[Order, ...],
) -> None:
    counts = Counter(order.market_code for order in orders)

    assert dict(counts) == (EXPECTED_ORDER_COUNTS)


def test_order_ids_are_unique(
    orders: tuple[Order, ...],
) -> None:
    identifiers = [order.order_id for order in orders]

    assert len(identifiers) == len(set(identifiers))


def test_order_numbers_are_unique(
    orders: tuple[Order, ...],
) -> None:
    numbers = [order.order_number for order in orders]

    assert len(numbers) == len(set(numbers))


def test_order_item_ids_are_unique(
    order_items: tuple[OrderItem, ...],
) -> None:
    identifiers = [item.order_item_id for item in order_items]

    assert len(identifiers) == len(set(identifiers))


def test_order_item_volume_is_reasonable(
    orders: tuple[Order, ...],
    order_items: tuple[OrderItem, ...],
) -> None:
    assert len(order_items) > len(orders)

    assert len(order_items) <= len(orders) * 5


def test_each_order_has_between_one_and_five_lines(
    orders: tuple[Order, ...],
    order_items: tuple[OrderItem, ...],
) -> None:
    counts = Counter(item.order_id for item in order_items)

    assert len(counts) == len(orders)

    assert all(1 <= count <= 5 for count in counts.values())


def test_line_numbers_are_contiguous(
    order_items: tuple[OrderItem, ...],
) -> None:
    lines_by_order: dict[
        str,
        list[int],
    ] = defaultdict(list)

    for item in order_items:
        lines_by_order[item.order_id].append(item.line_number)

    for line_numbers in lines_by_order.values():
        actual = sorted(line_numbers)

        assert actual == list(
            range(
                1,
                len(actual) + 1,
            )
        )


def test_item_quantities_are_between_one_and_four(
    order_items: tuple[OrderItem, ...],
) -> None:
    assert all(1 <= item.quantity <= 4 for item in order_items)


def test_all_channels_are_present(
    orders: tuple[Order, ...],
) -> None:
    assert {order.channel for order in orders} == {
        "STORE",
        "WEB",
        "MOBILE",
    }


def test_channel_distribution_when_store_available(
    orders: tuple[Order, ...],
    oms_stores: tuple[Store, ...],
) -> None:
    stores_by_market: dict[
        str,
        list[Store],
    ] = defaultdict(list)

    for store in oms_stores:
        stores_by_market[store.market_code].append(store)

    eligible_orders = [
        order
        for order in orders
        if any(
            (
                store.opened_at <= order.order_date
                and (store.closed_at is None or order.order_date < store.closed_at)
            )
            for store in stores_by_market[order.market_code]
        )
    ]

    counts = Counter(order.channel for order in eligible_orders)

    total = len(eligible_orders)

    store_share = counts["STORE"] / total

    web_share = counts["WEB"] / total

    mobile_share = counts["MOBILE"] / total

    assert 0.50 < store_share < 0.54
    assert 0.28 < web_share < 0.32
    assert 0.16 < mobile_share < 0.20


def test_orders_without_active_store_are_digital_only(
    orders: tuple[Order, ...],
    oms_stores: tuple[Store, ...],
) -> None:
    stores_by_market: dict[
        str,
        list[Store],
    ] = defaultdict(list)

    for store in oms_stores:
        stores_by_market[store.market_code].append(store)

    orders_without_store = [
        order
        for order in orders
        if not any(
            (
                store.opened_at <= order.order_date
                and (store.closed_at is None or order.order_date < store.closed_at)
            )
            for store in stores_by_market[order.market_code]
        )
    ]

    assert orders_without_store

    assert all(
        order.channel
        in {
            "WEB",
            "MOBILE",
        }
        for order in orders_without_store
    )


def test_digital_distribution_when_no_store_available(
    orders: tuple[Order, ...],
    oms_stores: tuple[Store, ...],
) -> None:
    stores_by_market: dict[
        str,
        list[Store],
    ] = defaultdict(list)

    for store in oms_stores:
        stores_by_market[store.market_code].append(store)

    orders_without_store = [
        order
        for order in orders
        if not any(
            (
                store.opened_at <= order.order_date
                and (store.closed_at is None or order.order_date < store.closed_at)
            )
            for store in stores_by_market[order.market_code]
        )
    ]

    counts = Counter(order.channel for order in orders_without_store)

    total = len(orders_without_store)

    web_share = counts["WEB"] / total

    mobile_share = counts["MOBILE"] / total

    assert 0.59 < web_share < 0.66
    assert 0.34 < mobile_share < 0.41


def test_store_orders_reference_store(
    orders: tuple[Order, ...],
) -> None:
    assert all(
        (order.store_id is not None and order.store_code is not None)
        for order in orders
        if order.channel == "STORE"
    )


def test_digital_orders_do_not_reference_store(
    orders: tuple[Order, ...],
) -> None:
    assert all(
        (order.store_id is None and order.store_code is None)
        for order in orders
        if order.channel
        in {
            "WEB",
            "MOBILE",
        }
    )


def test_confirmed_and_cancelled_orders_exist(
    orders: tuple[Order, ...],
) -> None:
    statuses = {order.order_status for order in orders}

    assert statuses == {
        "CONFIRMED",
        "CANCELLED",
    }


def test_cancellation_rate_is_reasonable(
    orders: tuple[Order, ...],
) -> None:
    cancelled = sum(order.order_status == "CANCELLED" for order in orders)

    rate = cancelled / len(orders)

    assert 0.03 < rate < 0.04


def test_customer_orders_repeat(
    orders: tuple[Order, ...],
) -> None:
    counts = Counter(order.customer_id for order in orders)

    assert any(count > 1 for count in counts.values())


def test_order_dates_are_inside_simulation(
    oms_context: SimulationContext,
    orders: tuple[Order, ...],
) -> None:
    assert all(
        (oms_context.config.start_date <= order.order_date <= oms_context.config.end_date)
        for order in orders
    )


def test_customers_are_active_on_order_date(
    orders: tuple[Order, ...],
    oms_customers: tuple[Customer, ...],
) -> None:
    customers_by_id = {customer.customer_id: customer for customer in oms_customers}

    assert all(
        customers_by_id[order.customer_id].is_active_on(order.order_date) for order in orders
    )


def test_line_totals_are_correct(
    order_items: tuple[OrderItem, ...],
) -> None:
    assert all(item.line_total == (item.unit_price * item.quantity) for item in order_items)


def test_order_totals_reconcile(
    orders: tuple[Order, ...],
    order_items: tuple[OrderItem, ...],
) -> None:
    totals: dict[
        str,
        Decimal,
    ] = defaultdict(lambda: Decimal("0"))

    for item in order_items:
        totals[item.order_id] += item.line_total

    assert all(order.order_total == totals[order.order_id] for order in orders)


def test_no_duplicate_assortment_within_order(
    order_items: tuple[OrderItem, ...],
) -> None:
    assortments_by_order: dict[
        str,
        list[str],
    ] = defaultdict(list)

    for item in order_items:
        assortments_by_order[item.order_id].append(item.assortment_id)

    assert all(
        len(assortments) == len(set(assortments)) for assortments in assortments_by_order.values()
    )


def test_order_prices_are_positive(
    order_items: tuple[OrderItem, ...],
) -> None:
    assert all(item.unit_price > Decimal("0") for item in order_items)


def test_generation_is_deterministic(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> None:
    first = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    second = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    assert first == second


def test_customer_input_order_independent(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> None:
    first = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    second = generate_orders(
        oms_context,
        tuple(reversed(oms_customers)),
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    assert first == second


def test_store_input_order_independent(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> None:
    first = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    second = generate_orders(
        oms_context,
        oms_customers,
        tuple(reversed(oms_stores)),
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    assert first == second


def test_assortment_input_order_independent(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> None:
    first = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    second = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        tuple(reversed(oms_assortments)),
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    assert first == second


def test_price_input_order_independent(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> None:
    first = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    second = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        tuple(reversed(oms_prices)),
        oms_demand_profiles,
        config=small_oms_config,
    )

    assert first == second


def test_demand_input_order_independent(
    oms_context: SimulationContext,
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_demand_profiles: tuple[DemandProfile, ...],
    small_oms_config: OMSSimulationConfig,
) -> None:
    first = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_demand_profiles,
        config=small_oms_config,
    )

    second = generate_orders(
        oms_context,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        tuple(reversed(oms_demand_profiles)),
        config=small_oms_config,
    )

    assert first == second
