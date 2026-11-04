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
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.oms.config import (
    OMSSimulationConfig,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderChannel,
    OrderItem,
    OrderStatus,
)
from mercatura.source.systems.oms.validation import (
    validate_orders,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.store.model import (
    Store,
)


def replace_order(
    orders: tuple[Order, ...],
    replacement: Order,
) -> tuple[Order, ...]:
    return tuple(
        replacement if order.order_id == replacement.order_id else order for order in orders
    )


def replace_item(
    items: tuple[OrderItem, ...],
    replacement: OrderItem,
) -> tuple[OrderItem, ...]:
    return tuple(
        replacement if item.order_item_id == replacement.order_item_id else item for item in items
    )


def validate_small(
    *,
    orders: tuple[Order, ...],
    items: tuple[OrderItem, ...],
    customers: tuple[Customer, ...],
    stores: tuple[Store, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
    context: SimulationContext,
    config: OMSSimulationConfig,
) -> None:
    validate_orders(
        orders,
        items,
        customers,
        stores,
        assortments,
        prices,
        context,
        config=config,
    )


def test_full_dataset_passes_validation(
    orders: tuple[Order, ...],
    order_items: tuple[OrderItem, ...],
    oms_customers: tuple[Customer, ...],
    oms_stores: tuple[Store, ...],
    oms_assortments: tuple[ProductMarketAssortment, ...],
    oms_prices: tuple[ProductPrice, ...],
    oms_context: SimulationContext,
) -> None:
    validate_orders(
        orders,
        order_items,
        oms_customers,
        oms_stores,
        oms_assortments,
        oms_prices,
        oms_context,
    )


def test_small_dataset_passes_validation(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    validate_small(
        orders=small_orders,
        items=small_order_items,
        customers=oms_customers,
        stores=oms_stores,
        assortments=oms_assortments,
        prices=oms_prices,
        context=oms_context,
        config=small_oms_config,
    )


def test_rejects_duplicate_order_id(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    broken = (
        *small_orders,
        small_orders[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate order_id",
    ):
        validate_small(
            orders=broken,
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_duplicate_order_number(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[1]

    broken_order = replace(
        target,
        order_number=(small_orders[0].order_number),
    )

    with pytest.raises(
        ValueError,
        match="duplicate order_number",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken_order,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_duplicate_order_item_id(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    broken = (
        *small_order_items,
        small_order_items[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate order_item_id",
    ):
        validate_small(
            orders=small_orders,
            items=broken,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_duplicate_order_line(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    duplicate = replace(
        target,
        order_item_id="itm_duplicate",
    )

    broken = (
        *small_order_items,
        duplicate,
    )

    with pytest.raises(
        ValueError,
        match="duplicate order line",
    ):
        validate_small(
            orders=small_orders,
            items=broken,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_missing_order(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    broken = small_orders[1:]

    with pytest.raises(
        ValueError,
        match="order count",
    ):
        validate_small(
            orders=broken,
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_unknown_customer(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        customer_id="cus_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown customer",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_wrong_currency(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        currency="USD",
    )

    with pytest.raises(
        ValueError,
        match="currency does not match market",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_invalid_channel(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        channel=cast(
            OrderChannel,
            "KIOSK",
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid channel",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_invalid_status(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        order_status=cast(
            OrderStatus,
            "PENDING",
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid status",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_order_date_outside_simulation(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        order_date=(oms_context.config.start_date - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="outside simulation window",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_customer_inactive_on_order_date(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    customers_by_id = {customer.customer_id: customer for customer in oms_customers}

    target = next(
        order
        for order in small_orders
        if (customers_by_id[order.customer_id].created_at > oms_context.config.start_date)
    )

    customer = customers_by_id[target.customer_id]

    broken = replace(
        target,
        order_date=(customer.created_at - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="customer is not active",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_store_order_without_store(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if order.channel == "STORE")

    broken = replace(
        target,
        store_id=None,
        store_code=None,
    )

    with pytest.raises(
        ValueError,
        match="must reference a physical store",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_unknown_store(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if order.channel == "STORE")

    broken = replace(
        target,
        store_id="sto_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown store",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_store_code_mismatch(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if order.channel == "STORE")

    broken = replace(
        target,
        store_code="STORE-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="store_code does not match",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_digital_order_with_store(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if order.channel == "WEB")

    store = next(store for store in oms_stores if store.market_code == target.market_code)

    broken = replace(
        target,
        store_id=store.store_id,
        store_code=store.store_code,
    )

    with pytest.raises(
        ValueError,
        match="must not reference a physical store",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_confirmed_order_with_cancellation_date(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if (order.order_status == "CONFIRMED"))

    broken = replace(
        target,
        cancelled_at=(target.order_date),
    )

    with pytest.raises(
        ValueError,
        match="CONFIRMED order cannot",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_cancelled_order_without_cancellation_date(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if (order.order_status == "CANCELLED"))

    broken = replace(
        target,
        cancelled_at=None,
    )

    with pytest.raises(
        ValueError,
        match="must have cancelled_at",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_cancellation_before_order(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(order for order in small_orders if (order.order_status == "CANCELLED"))

    broken = replace(
        target,
        cancelled_at=(target.order_date - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="before order date",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_excessive_cancellation_delay(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = next(
        order
        for order in small_orders
        if (
            order.order_status == "CANCELLED"
            and order.order_date <= (oms_context.config.end_date - timedelta(days=4))
        )
    )

    broken = replace(
        target,
        cancelled_at=(target.order_date + timedelta(days=4)),
    )

    with pytest.raises(
        ValueError,
        match="delay exceeds configuration",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_non_positive_order_total(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        order_total=Decimal("0"),
    )

    with pytest.raises(
        ValueError,
        match="order_total must be positive",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_item_for_unknown_order(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        order_id="ord_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown order",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_unknown_assortment(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        assortment_id="ast_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown assortment",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_unknown_price(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        price_id="prc_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown price",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_non_positive_line_number(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        line_number=0,
    )

    with pytest.raises(
        ValueError,
        match="line_number must be positive",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_non_positive_quantity(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        quantity=0,
    )

    with pytest.raises(
        ValueError,
        match="quantity must be positive",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_quantity_above_configured_maximum(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        quantity=5,
    )

    with pytest.raises(
        ValueError,
        match="quantity exceeds configured maximum",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_wrong_product(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        product_id="prd_wrong",
    )

    with pytest.raises(
        ValueError,
        match="product does not match assortment",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_wrong_sku(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        sku="MRC-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="SKU does not match assortment",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_price_from_wrong_assortment(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    alternative_price = next(
        price for price in oms_prices if (price.assortment_id != target.assortment_id)
    )

    broken = replace(
        target,
        price_id=(alternative_price.price_id),
    )

    with pytest.raises(
        ValueError,
        match="price does not match assortment",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_wrong_unit_price(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        unit_price=(target.unit_price + Decimal("1.00")),
    )

    with pytest.raises(
        ValueError,
        match="unit_price does not match price",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_wrong_line_total(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        line_total=(target.line_total + Decimal("1.00")),
    )

    with pytest.raises(
        ValueError,
        match="line_total is invalid",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_order_without_items(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target_order = small_orders[0]

    broken_items = tuple(
        item for item in small_order_items if (item.order_id != target_order.order_id)
    )

    with pytest.raises(
        ValueError,
        match="order has no order items",
    ):
        validate_small(
            orders=small_orders,
            items=broken_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_too_many_lines(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target_order = small_orders[0]

    source_item = next(
        item for item in small_order_items if (item.order_id == target_order.order_id)
    )

    existing_target_items = [
        item for item in small_order_items if (item.order_id == target_order.order_id)
    ]

    additions: list[OrderItem] = []

    next_line = len(existing_target_items) + 1

    while len(existing_target_items) + len(additions) < 6:
        additions.append(
            replace(
                source_item,
                order_item_id=(f"itm_extra_{next_line}"),
                line_number=(next_line),
            )
        )

        next_line += 1

    broken_items = (
        *small_order_items,
        *additions,
    )

    with pytest.raises(
        ValueError,
        match="order has too many lines",
    ):
        validate_small(
            orders=small_orders,
            items=broken_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_non_contiguous_line_numbers(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_order_items[0]

    broken = replace(
        target,
        line_number=99,
    )

    with pytest.raises(
        ValueError,
        match="line numbers are not contiguous",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_duplicate_assortment_within_order(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    items_by_order: dict[
        str,
        list[OrderItem],
    ] = {}

    for item in small_order_items:
        items_by_order.setdefault(
            item.order_id,
            [],
        ).append(item)

    target_items = next(rows for rows in items_by_order.values() if len(rows) >= 2)

    source = target_items[0]
    target = target_items[1]

    source_price = next(price for price in oms_prices if (price.price_id == source.price_id))

    broken = replace(
        target,
        assortment_id=(source.assortment_id),
        product_id=(source.product_id),
        sku=source.sku,
        price_id=source.price_id,
        unit_price=(source_price.list_price),
        line_total=(source_price.list_price * target.quantity),
    )

    with pytest.raises(
        ValueError,
        match="duplicate assortment lines",
    ):
        validate_small(
            orders=small_orders,
            items=replace_item(
                small_order_items,
                broken,
            ),
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )


def test_rejects_order_total_mismatch(
    small_orders,
    small_order_items,
    oms_customers,
    oms_stores,
    oms_assortments,
    oms_prices,
    oms_context,
    small_oms_config,
) -> None:
    target = small_orders[0]

    broken = replace(
        target,
        order_total=(target.order_total + Decimal("1.00")),
    )

    with pytest.raises(
        ValueError,
        match="order_total does not reconcile",
    ):
        validate_small(
            orders=replace_order(
                small_orders,
                broken,
            ),
            items=small_order_items,
            customers=oms_customers,
            stores=oms_stores,
            assortments=oms_assortments,
            prices=oms_prices,
            context=oms_context,
            config=small_oms_config,
        )
