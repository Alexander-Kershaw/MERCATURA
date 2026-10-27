import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from mercatura.source.reference.pricing import (
    SUBCATEGORY_PRICE_BANDS,
    PriceBand,
)
from mercatura.source.simulation import SimulationContext
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.pricing.config import (
    DEFAULT_MARKET_PRICING,
    DEFAULT_PRICING_CONFIG,
    MarketPricingConfig,
    PricingSimulationConfig,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)

MARKET_PRICING_BY_CODE: dict[str, MarketPricingConfig] = {
    config.market_code: config for config in DEFAULT_MARKET_PRICING
}


def generate_prices(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    *,
    pricing_config: PricingSimulationConfig = DEFAULT_PRICING_CONFIG,
) -> tuple[ProductPrice, ...]:
    products_by_id: dict[str, Product] = {product.product_id: product for product in products}

    prices: list[ProductPrice] = []

    for assortment in assortments:
        product: Product = products_by_id[assortment.product_id]

        prices.extend(
            _generate_price_history(
                context=context,
                product=product,
                assortment=assortment,
                config=pricing_config,
            )
        )

    return tuple(prices)


def _reference_price_gbp(
    context: SimulationContext,
    product: Product,
) -> Decimal:
    price_band: PriceBand = SUBCATEGORY_PRICE_BANDS[product.subcategory_code]

    rng = random.Random(x=context.seed_for(namespace=f"pricing:base:{product.sku}"))

    ratio = Decimal(value=str(object=rng.random()))

    spread: Decimal = price_band.maximum_gbp - price_band.minimum_gbp

    return price_band.minimum_gbp + spread * ratio


def _initial_local_price(
    *,
    context: SimulationContext,
    product: Product,
    market_config: MarketPricingConfig,
) -> Decimal:
    reference_price: Decimal = _reference_price_gbp(
        context,
        product,
    )

    rng = random.Random(
        x=context.seed_for(namespace=(f"pricing:local:{market_config.market_code}:{product.sku}"))
    )

    local_variation = Decimal(
        value=str(
            object=rng.uniform(
                a=0.95,
                b=1.05,
            )
        )
    )

    raw_price: Decimal = (
        reference_price
        * market_config.local_currency_scale
        * market_config.market_price_index
        * local_variation
    )

    return _round_money(
        value=raw_price,
        minor_unit=market_config.minor_unit,
    )


def _round_money(
    value: Decimal,
    minor_unit: Decimal,
) -> Decimal:
    return (value / minor_unit).quantize(
        exp=Decimal(value="1"),
        rounding=ROUND_HALF_UP,
    ) * minor_unit


def _generate_price_history(
    *,
    context: SimulationContext,
    product: Product,
    assortment: ProductMarketAssortment,
    config: PricingSimulationConfig,
) -> list[ProductPrice]:
    market: MarketConfig = context.market(market_code=assortment.market_code)

    market_config: MarketPricingConfig = MARKET_PRICING_BY_CODE[assortment.market_code]

    initial_price: Decimal = _initial_local_price(
        context=context,
        product=product,
        market_config=market_config,
    )

    rng = random.Random(
        x=context.seed_for(namespace=(f"pricing:history:{assortment.market_code}:{product.sku}"))
    )

    change_dates: list[date] = _generate_change_dates(
        context=context,
        assortment=assortment,
        config=config,
        rng=rng,
    )

    boundaries: list[date | None] = [
        assortment.ranged_from,
        *change_dates,
        assortment.ranged_to,
    ]

    rows: list[ProductPrice] = []

    current_price: Decimal = initial_price

    for version in range(
        1,
        len(boundaries),
    ):
        effective_from: date = assortment.ranged_from

        effective_tos: list[date | None] = [
            *change_dates,
            assortment.ranged_to,
        ]

        rows: list[ProductPrice] = []

        current_price = initial_price

        for version, effective_to in enumerate(
            iterable=effective_tos,
            start=1,
        ):
            if version > 1:
                current_price = _change_price(
                    price=current_price,
                    market_config=market_config,
                    config=config,
                    rng=rng,
                )

            price_id: str = context.ids.id_for(
                namespace="price",
                key=(f"{assortment.market_code}:{product.sku}:{effective_from.isoformat()}"),
                prefix="prc",
            )

            rows.append(
                ProductPrice(
                    price_id=price_id,
                    assortment_id=assortment.assortment_id,
                    product_id=product.product_id,
                    sku=product.sku,
                    market_code=assortment.market_code,
                    currency=market.currency,
                    list_price=current_price,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    version=version,
                )
            )

            if effective_to is not None:
                effective_from = effective_to

    return rows


def _generate_change_dates(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    config: PricingSimulationConfig,
    rng: random.Random,
) -> list[date]:
    active_start: date = max(
        assortment.ranged_from,
        context.config.start_date,
    )

    active_end: date = min(
        assortment.ranged_to or (context.config.end_date + timedelta(days=1)),
        context.config.end_date + timedelta(days=1),
    )

    earliest_change: date = active_start + timedelta(days=config.minimum_days_before_change)

    if earliest_change >= active_end:
        return []

    probabilities: tuple[float, ...] = (
        config.first_change_probability,
        config.second_change_probability,
        config.third_change_probability,
    )[: config.maximum_changes]

    change_count: int = sum(rng.random() < probability for probability in probabilities)

    available_days: int = (active_end - earliest_change).days

    change_count = min(
        change_count,
        available_days,
    )

    if change_count == 0:
        return []

    offsets: list[int] = sorted(
        rng.sample(
            range(available_days),
            k=change_count,
        )
    )

    return [earliest_change + timedelta(days=offset) for offset in offsets]


def _change_price(
    *,
    price: Decimal,
    market_config: MarketPricingConfig,
    config: PricingSimulationConfig,
    rng: random.Random,
) -> Decimal:
    percentage = Decimal(
        value=str(
            object=rng.uniform(
                a=float(config.minimum_change_percent),
                b=float(config.maximum_change_percent),
            )
        )
    )

    direction: Decimal = Decimal(value="1") if rng.random() < 0.70 else Decimal(value="-1")

    multiplier: Decimal = Decimal(value="1") + direction * percentage

    changed: Decimal = price * multiplier

    return max(
        market_config.minor_unit,
        _round_money(
            value=changed,
            minor_unit=market_config.minor_unit,
        ),
    )
