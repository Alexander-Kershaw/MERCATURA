from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.oms.config import (
    DEFAULT_OMS_CONFIG,
    OMSSimulationConfig,
)
from mercatura.source.systems.oms.model import (
    ORDER_CHANNELS,
    ORDER_STATUSES,
    Order,
    OrderItem,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.store.model import (
    Store,
)


def validate_orders(
    orders: tuple[Order, ...],
    items: tuple[OrderItem, ...],
    customers: tuple[Customer, ...],
    stores: tuple[Store, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
    context: SimulationContext,
    *,
    config: OMSSimulationConfig = (DEFAULT_OMS_CONFIG),
) -> None:
    _validate_order_uniqueness(orders)

    _validate_item_uniqueness(items)

    _validate_market_counts(
        orders,
        config,
    )

    _validate_order_rows(
        orders=orders,
        customers=customers,
        stores=stores,
        context=context,
        config=config,
    )

    _validate_items(
        orders=orders,
        items=items,
        assortments=assortments,
        prices=prices,
        context=context,
        config=config,
    )


def _validate_order_uniqueness(
    orders: tuple[Order, ...],
) -> None:
    ids: list[str] = [order.order_id for order in orders]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate order_id detected")

    numbers: list[str] = [order.order_number for order in orders]

    if len(numbers) != len(set(numbers)):
        raise ValueError("duplicate order_number detected")


def _validate_item_uniqueness(
    items: tuple[OrderItem, ...],
) -> None:
    ids: list[str] = [item.order_item_id for item in items]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate order_item_id detected")

    order_line_pairs: list[tuple[str, int]] = [
        (
            item.order_id,
            item.line_number,
        )
        for item in items
    ]

    if len(order_line_pairs) != len(set(order_line_pairs)):
        raise ValueError("duplicate order line detected")


def _validate_market_counts(
    orders: tuple[Order, ...],
    config: OMSSimulationConfig,
) -> None:
    expected: dict[str, int] = {
        market.market_code: market.order_count for market in config.market_configs
    }

    actual: Counter[str] = Counter(order.market_code for order in orders)

    if set(actual) != set(expected):
        raise ValueError("OMS order markets do not match configuration")

    for market_code, expected_count in expected.items():
        if actual[market_code] != expected_count:
            raise ValueError(f"OMS order count for {market_code} does not match configuration")


def _validate_order_rows(
    *,
    orders: tuple[Order, ...],
    customers: tuple[Customer, ...],
    stores: tuple[Store, ...],
    context: SimulationContext,
    config: OMSSimulationConfig,
) -> None:
    customers_by_id: dict[str, Customer] = {
        customer.customer_id: customer for customer in customers
    }

    stores_by_id: dict[str, Store] = {store.store_id: store for store in stores}

    valid_channels = set(ORDER_CHANNELS)

    valid_statuses = set(ORDER_STATUSES)

    for order in orders:
        customer: Customer | None = customers_by_id.get(order.customer_id)

        if customer is None:
            raise ValueError("order references unknown customer")

        if order.market_code != customer.market_code:
            raise ValueError("order market does not match customer")

        if (
            order.order_date < context.config.start_date
            or order.order_date > context.config.end_date
        ):
            raise ValueError("order date is outside simulation window")

        if not customer.is_active_on(value=order.order_date):
            raise ValueError("customer is not active on order date")

        market: MarketConfig = context.market(market_code=order.market_code)

        if order.currency != market.currency:
            raise ValueError("order currency does not match market")

        if order.channel not in valid_channels:
            raise ValueError("order has invalid channel")

        if order.order_status not in valid_statuses:
            raise ValueError("order has invalid status")

        _validate_store_semantics(
            order=order,
            stores_by_id=stores_by_id,
        )

        _validate_status_semantics(
            order=order,
            context=context,
            config=config,
        )

        if order.order_total <= Decimal(value="0"):
            raise ValueError("order_total must be positive")


def _validate_store_semantics(
    *,
    order: Order,
    stores_by_id: dict[
        str,
        Store,
    ],
) -> None:
    if order.channel == "STORE":
        if order.store_id is None or order.store_code is None:
            raise ValueError("STORE order must reference a physical store")

        store: Store | None = stores_by_id.get(order.store_id)

        if store is None:
            raise ValueError("STORE order references unknown store")

        if store.store_code != order.store_code:
            raise ValueError("order store_code does not match store")

        if store.market_code != order.market_code:
            raise ValueError("order store market does not match order")

        if store.opened_at > order.order_date or (
            store.closed_at is not None and order.order_date >= store.closed_at
        ):
            raise ValueError("store is not active on order date")

        return

    if order.store_id is not None or order.store_code is not None:
        raise ValueError("non-STORE order must not reference a physical store")


def _validate_status_semantics(
    *,
    order: Order,
    context: SimulationContext,
    config: OMSSimulationConfig,
) -> None:
    if order.order_status == "CONFIRMED":
        if order.cancelled_at is not None:
            raise ValueError("CONFIRMED order cannot have cancelled_at")

        return

    if order.cancelled_at is None:
        raise ValueError("CANCELLED order must have cancelled_at")

    if order.cancelled_at < order.order_date:
        raise ValueError("order cancellation occurs before order date")

    if order.cancelled_at > context.config.end_date:
        raise ValueError("order cancellation occurs after simulation end")

    delay = (order.cancelled_at - order.order_date).days

    if delay > config.maximum_cancellation_delay_days:
        raise ValueError("order cancellation delay exceeds configuration")


def _validate_items(
    *,
    orders: tuple[Order, ...],
    items: tuple[OrderItem, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
    context: SimulationContext,
    config: OMSSimulationConfig,
) -> None:
    orders_by_id: dict[str, Order] = {order.order_id: order for order in orders}

    assortments_by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    prices_by_id: dict[str, ProductPrice] = {price.price_id: price for price in prices}

    items_by_order: dict[
        str,
        list[OrderItem],
    ] = defaultdict(list)

    for item in items:
        order: Order | None = orders_by_id.get(item.order_id)

        if order is None:
            raise ValueError("order item references unknown order")

        assortment: ProductMarketAssortment | None = assortments_by_id.get(item.assortment_id)

        if assortment is None:
            raise ValueError("order item references unknown assortment")

        price: ProductPrice | None = prices_by_id.get(item.price_id)

        if price is None:
            raise ValueError("order item references unknown price")

        if item.line_number <= 0:
            raise ValueError("order item line_number must be positive")

        if item.quantity <= 0:
            raise ValueError("order item quantity must be positive")

        if item.quantity > len(config.item_quantity_probabilities):
            raise ValueError("order item quantity exceeds configured maximum")

        if assortment.market_code != order.market_code:
            raise ValueError("order item assortment market does not match order")

        if item.product_id != assortment.product_id:
            raise ValueError("order item product does not match assortment")

        if item.sku != assortment.sku:
            raise ValueError("order item SKU does not match assortment")

        if not _assortment_active_on(
            assortment,
            value=order.order_date,
        ):
            raise ValueError("order item assortment is not active on order date")

        if price.assortment_id != assortment.assortment_id:
            raise ValueError("order item price does not match assortment")

        if price.market_code != order.market_code:
            raise ValueError("order item price market does not match order")

        if not _price_active_on(
            price,
            value=order.order_date,
        ):
            raise ValueError("order item price is not effective on order date")

        if item.unit_price != price.list_price:
            raise ValueError("order item unit_price does not match price")

        expected_total: Decimal = item.unit_price * item.quantity

        if item.line_total != expected_total:
            raise ValueError("order item line_total is invalid")

        items_by_order[item.order_id].append(item)

    for order in orders:
        order_items: list[OrderItem] = items_by_order.get(
            order.order_id,
            [],
        )

        if not order_items:
            raise ValueError("order has no order items")

        if len(order_items) > len(config.line_count_probabilities):
            raise ValueError("order has too many lines")

        line_numbers: list[int] = sorted(item.line_number for item in order_items)

        expected_lines: list[int] = list(
            range(
                1,
                len(order_items) + 1,
            )
        )

        if line_numbers != expected_lines:
            raise ValueError("order line numbers are not contiguous")

        assortment_ids: list[str] = [item.assortment_id for item in order_items]

        if len(assortment_ids) != len(set(assortment_ids)):
            raise ValueError("order contains duplicate assortment lines")

        expected_total = sum(
            (item.line_total for item in order_items),
            start=Decimal(value="0"),
        )

        if order.order_total != expected_total:
            raise ValueError("order_total does not reconcile to order items")


def _assortment_active_on(
    assortment: ProductMarketAssortment,
    value: date,
) -> bool:
    return value >= assortment.ranged_from and (
        assortment.ranged_to is None or value < assortment.ranged_to
    )


def _price_active_on(
    price: ProductPrice,
    value: date,
) -> bool:
    return value >= price.effective_from and (
        price.effective_to is None or value < price.effective_to
    )
