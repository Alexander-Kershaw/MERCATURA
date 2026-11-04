import bisect
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from itertools import accumulate

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
    DEFAULT_OMS_CONFIG,
    MarketOrderConfig,
    OMSSimulationConfig,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderChannel,
    OrderItem,
    OrderStatus,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.store.model import (
    Store,
)


@dataclass(frozen=True, slots=True)
class _CustomerPool:
    customers: tuple[Customer, ...]
    cumulative_weights: tuple[float, ...]
    total_weight: float


@dataclass(frozen=True, slots=True)
class _AssortmentPool:
    assortments: tuple[ProductMarketAssortment, ...]
    cumulative_weights: tuple[float, ...]
    total_weight: float


def generate_orders(
    context: SimulationContext,
    customers: tuple[Customer, ...],
    stores: tuple[Store, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
    demand_profiles: tuple[DemandProfile, ...],
    *,
    config: OMSSimulationConfig = (DEFAULT_OMS_CONFIG),
) -> tuple[
    tuple[Order, ...],
    tuple[OrderItem, ...],
]:
    customer_pools = _build_customer_pools(
        context=context,
        customers=customers,
        config=config,
    )

    assortment_pools = _build_assortment_pools(
        assortments=assortments,
        demand_profiles=demand_profiles,
    )

    stores_by_market = _group_stores_by_market(stores)

    prices_by_assortment = _group_prices_by_assortment(prices)

    orders: list[Order] = []
    items: list[OrderItem] = []

    for market_config in config.market_configs:
        market_code = market_config.market_code

        customer_pool = customer_pools.get(market_code)

        if customer_pool is None:
            raise ValueError(f"no eligible customers for OMS market {market_code}")

        assortment_pool = assortment_pools.get(market_code)

        if assortment_pool is None:
            raise ValueError(f"no assortments for OMS market {market_code}")

        market_stores = stores_by_market.get(
            market_code,
            (),
        )

        market_currency = context.market(market_code).currency

        market_orders, market_items = _generate_market_orders(
            context=context,
            market_config=(market_config),
            customer_pool=(customer_pool),
            assortment_pool=(assortment_pool),
            stores=market_stores,
            prices_by_assortment=(prices_by_assortment),
            currency=market_currency,
            config=config,
        )

        orders.extend(market_orders)

        items.extend(market_items)

    return (
        tuple(orders),
        tuple(items),
    )


def _generate_market_orders(
    *,
    context: SimulationContext,
    market_config: MarketOrderConfig,
    customer_pool: _CustomerPool,
    assortment_pool: _AssortmentPool,
    stores: tuple[Store, ...],
    prices_by_assortment: dict[
        str,
        tuple[ProductPrice, ...],
    ],
    currency: str,
    config: OMSSimulationConfig,
) -> tuple[
    list[Order],
    list[OrderItem],
]:
    orders: list[Order] = []
    items: list[OrderItem] = []

    market_code = market_config.market_code

    for ordinal in range(
        1,
        market_config.order_count + 1,
    ):
        order_number = f"ORD-{market_code}-{ordinal:07d}"

        order_id = context.ids.id_for(
            "order",
            order_number,
            prefix="ord",
        )

        rng = random.Random(context.seed_for(f"oms:order:{market_code}:{ordinal:07d}"))

        customer = _weighted_customer_choice(
            pool=customer_pool,
            rng=rng,
        )

        order_date = _generate_order_date(
            context=context,
            customer=customer,
            rng=rng,
        )

        store_available = _has_active_store(
            stores=stores,
            order_date=order_date,
        )

        channel = _select_channel(
            rng=rng,
            config=config,
            store_available=(store_available),
        )

        store = _select_store(
            stores=stores,
            order_date=order_date,
            channel=channel,
            rng=rng,
        )

        line_count = _select_line_count(
            rng=rng,
            config=config,
        )

        order_items = _generate_order_items(
            context=context,
            order_id=order_id,
            order_date=order_date,
            line_count=line_count,
            assortment_pool=(assortment_pool),
            prices_by_assortment=(prices_by_assortment),
            rng=rng,
            config=config,
        )

        order_total = sum(
            (item.line_total for item in order_items),
            start=Decimal("0"),
        )

        (
            order_status,
            cancelled_at,
        ) = _generate_order_status(
            context=context,
            order_date=order_date,
            rng=rng,
            config=config,
        )

        orders.append(
            Order(
                order_id=order_id,
                order_number=order_number,
                customer_id=(customer.customer_id),
                market_code=market_code,
                currency=currency,
                channel=channel,
                store_id=(None if store is None else store.store_id),
                store_code=(None if store is None else store.store_code),
                order_date=order_date,
                order_status=(order_status),
                cancelled_at=(cancelled_at),
                order_total=(order_total),
            )
        )

        items.extend(order_items)

    return (
        orders,
        items,
    )


def _build_customer_pools(
    *,
    context: SimulationContext,
    customers: tuple[Customer, ...],
    config: OMSSimulationConfig,
) -> dict[
    str,
    _CustomerPool,
]:
    grouped: dict[
        str,
        list[Customer],
    ] = defaultdict(list)

    for customer in customers:
        active_start = max(
            customer.created_at,
            context.config.start_date,
        )

        active_end = (
            context.config.end_date
            if customer.deactivated_at is None
            else min(
                (customer.deactivated_at - timedelta(days=1)),
                context.config.end_date,
            )
        )

        if active_start > active_end:
            continue

        grouped[customer.market_code].append(customer)

    result: dict[
        str,
        _CustomerPool,
    ] = {}

    for market_code, rows in grouped.items():
        ordered = tuple(
            sorted(
                rows,
                key=lambda row: row.customer_number,
            )
        )

        weights: list[float] = []

        for customer in ordered:
            active_start = max(
                customer.created_at,
                context.config.start_date,
            )

            active_end = (
                context.config.end_date
                if customer.deactivated_at is None
                else min(
                    (customer.deactivated_at - timedelta(days=1)),
                    context.config.end_date,
                )
            )

            active_days = (active_end - active_start).days + 1

            propensity_rng = random.Random(
                context.seed_for(f"oms:customer-propensity:{customer.customer_id}")
            )

            propensity = min(
                propensity_rng.lognormvariate(
                    0.0,
                    config.customer_propensity_sigma,
                ),
                config.customer_propensity_cap,
            )

            weights.append(float(active_days) * propensity)

        cumulative = tuple(accumulate(weights))

        result[market_code] = _CustomerPool(
            customers=ordered,
            cumulative_weights=(cumulative),
            total_weight=(cumulative[-1]),
        )

    return result


def _build_assortment_pools(
    *,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
) -> dict[
    str,
    _AssortmentPool,
]:
    demand_by_assortment = {profile.assortment_id: profile for profile in demand_profiles}

    grouped: dict[
        str,
        list[ProductMarketAssortment],
    ] = defaultdict(list)

    for assortment in assortments:
        grouped[assortment.market_code].append(assortment)

    result: dict[
        str,
        _AssortmentPool,
    ] = {}

    for market_code, rows in grouped.items():
        ordered = tuple(
            sorted(
                rows,
                key=lambda row: row.sku,
            )
        )

        weights: list[float] = []

        for assortment in ordered:
            demand = demand_by_assortment.get(assortment.assortment_id)

            if demand is None:
                raise ValueError(f"missing demand profile for {assortment.assortment_id}")

            weights.append(float(demand.average_daily_units))

        cumulative = tuple(accumulate(weights))

        result[market_code] = _AssortmentPool(
            assortments=ordered,
            cumulative_weights=(cumulative),
            total_weight=(cumulative[-1]),
        )

    return result


def _weighted_customer_choice(
    *,
    pool: _CustomerPool,
    rng: random.Random,
) -> Customer:
    index = _weighted_index(
        cumulative_weights=(pool.cumulative_weights),
        total_weight=(pool.total_weight),
        rng=rng,
    )

    return pool.customers[index]


def _weighted_assortment_choice(
    *,
    pool: _AssortmentPool,
    rng: random.Random,
) -> ProductMarketAssortment:
    index = _weighted_index(
        cumulative_weights=(pool.cumulative_weights),
        total_weight=(pool.total_weight),
        rng=rng,
    )

    return pool.assortments[index]


def _weighted_index(
    *,
    cumulative_weights: tuple[float, ...],
    total_weight: float,
    rng: random.Random,
) -> int:
    target = rng.random() * total_weight

    index = bisect.bisect_left(
        cumulative_weights,
        target,
    )

    return min(
        index,
        len(cumulative_weights) - 1,
    )


def _generate_order_date(
    *,
    context: SimulationContext,
    customer: Customer,
    rng: random.Random,
) -> date:
    start = max(
        customer.created_at,
        context.config.start_date,
    )

    end = (
        context.config.end_date
        if customer.deactivated_at is None
        else min(
            (customer.deactivated_at - timedelta(days=1)),
            context.config.end_date,
        )
    )

    if start > end:
        raise ValueError("customer has no active OMS ordering interval")

    span = (end - start).days

    return start + timedelta(
        days=rng.randint(
            0,
            span,
        )
    )


def _has_active_store(
    *,
    stores: tuple[Store, ...],
    order_date: date,
) -> bool:
    return any(
        _store_active_on(
            store,
            order_date,
        )
        for store in stores
    )


def _store_active_on(
    store: Store,
    value: date,
) -> bool:
    return store.opened_at <= value and (store.closed_at is None or value < store.closed_at)


def _select_channel(
    *,
    rng: random.Random,
    config: OMSSimulationConfig,
    store_available: bool,
) -> OrderChannel:
    if store_available:
        channels: tuple[OrderChannel, ...] = (
            "STORE",
            "WEB",
            "MOBILE",
        )

        return rng.choices(
            population=channels,
            weights=(
                config.store_channel_probability,
                config.web_channel_probability,
                config.mobile_channel_probability,
            ),
            k=1,
        )[0]

    digital_channels: tuple[OrderChannel, ...] = (
        "WEB",
        "MOBILE",
    )

    digital_weights = (
        config.web_channel_probability,
        config.mobile_channel_probability,
    )

    if sum(digital_weights) <= 0.0:
        raise ValueError("no digital OMS channel is available when physical stores are unavailable")

    return rng.choices(
        population=digital_channels,
        weights=digital_weights,
        k=1,
    )[0]


def _select_store(
    *,
    stores: tuple[Store, ...],
    order_date: date,
    channel: OrderChannel,
    rng: random.Random,
) -> Store | None:
    if channel != "STORE":
        return None

    eligible = [
        store
        for store in stores
        if _store_active_on(
            store,
            order_date,
        )
    ]

    if not eligible:
        raise ValueError("STORE order has no active store available")

    eligible.sort(key=lambda row: row.store_code)

    return rng.choice(eligible)


def _select_line_count(
    *,
    rng: random.Random,
    config: OMSSimulationConfig,
) -> int:
    values = tuple(
        range(
            1,
            len(config.line_count_probabilities) + 1,
        )
    )

    return rng.choices(
        population=values,
        weights=(config.line_count_probabilities),
        k=1,
    )[0]


def _select_item_quantity(
    *,
    rng: random.Random,
    config: OMSSimulationConfig,
) -> int:
    values = tuple(
        range(
            1,
            len(config.item_quantity_probabilities) + 1,
        )
    )

    return rng.choices(
        population=values,
        weights=(config.item_quantity_probabilities),
        k=1,
    )[0]


def _generate_order_items(
    *,
    context: SimulationContext,
    order_id: str,
    order_date: date,
    line_count: int,
    assortment_pool: _AssortmentPool,
    prices_by_assortment: dict[
        str,
        tuple[ProductPrice, ...],
    ],
    rng: random.Random,
    config: OMSSimulationConfig,
) -> list[OrderItem]:
    items: list[OrderItem] = []

    selected_assortments: set[str] = set()

    for line_number in range(
        1,
        line_count + 1,
    ):
        assortment = _select_active_assortment(
            pool=assortment_pool,
            order_date=order_date,
            excluded_assortments=(selected_assortments),
            rng=rng,
        )

        selected_assortments.add(assortment.assortment_id)

        price = _active_price(
            prices=(
                prices_by_assortment.get(
                    assortment.assortment_id,
                    (),
                )
            ),
            order_date=order_date,
        )

        quantity = _select_item_quantity(
            rng=rng,
            config=config,
        )

        line_total = price.list_price * quantity

        stable_key = f"{order_id}:{line_number}"

        order_item_id = context.ids.id_for(
            "order_item",
            stable_key,
            prefix="itm",
        )

        items.append(
            OrderItem(
                order_item_id=(order_item_id),
                order_id=order_id,
                line_number=(line_number),
                assortment_id=(assortment.assortment_id),
                product_id=(assortment.product_id),
                sku=assortment.sku,
                price_id=price.price_id,
                quantity=quantity,
                unit_price=(price.list_price),
                line_total=(line_total),
            )
        )

    return items


def _select_active_assortment(
    *,
    pool: _AssortmentPool,
    order_date: date,
    excluded_assortments: set[str],
    rng: random.Random,
) -> ProductMarketAssortment:
    for _ in range(500):
        assortment = _weighted_assortment_choice(
            pool=pool,
            rng=rng,
        )

        if assortment.assortment_id in excluded_assortments:
            continue

        if _assortment_active_on(
            assortment,
            order_date,
        ):
            return assortment

    raise ValueError("unable to select active unique assortment for OMS order")


def _assortment_active_on(
    assortment: ProductMarketAssortment,
    value: date,
) -> bool:
    return value >= assortment.ranged_from and (
        assortment.ranged_to is None or value < assortment.ranged_to
    )


def _group_prices_by_assortment(
    prices: tuple[ProductPrice, ...],
) -> dict[
    str,
    tuple[ProductPrice, ...],
]:
    grouped: dict[
        str,
        list[ProductPrice],
    ] = defaultdict(list)

    for price in prices:
        grouped[price.assortment_id].append(price)

    return {
        assortment_id: tuple(
            sorted(
                rows,
                key=lambda row: row.effective_from,
            )
        )
        for assortment_id, rows in grouped.items()
    }


def _active_price(
    *,
    prices: tuple[ProductPrice, ...],
    order_date: date,
) -> ProductPrice:
    for price in prices:
        if price.effective_from <= order_date and (
            price.effective_to is None or order_date < price.effective_to
        ):
            return price

    raise ValueError(f"no active price exists for OMS order date {order_date}")


def _group_stores_by_market(
    stores: tuple[Store, ...],
) -> dict[
    str,
    tuple[Store, ...],
]:
    grouped: dict[
        str,
        list[Store],
    ] = defaultdict(list)

    for store in stores:
        grouped[store.market_code].append(store)

    return {
        market_code: tuple(
            sorted(
                rows,
                key=lambda row: row.store_code,
            )
        )
        for market_code, rows in grouped.items()
    }


def _generate_order_status(
    *,
    context: SimulationContext,
    order_date: date,
    rng: random.Random,
    config: OMSSimulationConfig,
) -> tuple[
    OrderStatus,
    date | None,
]:
    if rng.random() >= config.cancellation_probability:
        return (
            "CONFIRMED",
            None,
        )

    delay = rng.randint(
        0,
        config.maximum_cancellation_delay_days,
    )

    cancelled_at = min(
        (order_date + timedelta(days=delay)),
        context.config.end_date,
    )

    return (
        "CANCELLED",
        cancelled_at,
    )
