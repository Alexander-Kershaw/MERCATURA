import random
from datetime import date, timedelta

from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.assortment.config import (
    DEFAULT_ASSORTMENT_CONFIG,
    MarketAssortmentConfig,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.model import Product


def generate_assortments(
    context: SimulationContext,
    products: tuple[Product, ...],
    *,
    assortment_config: tuple[MarketAssortmentConfig, ...] = DEFAULT_ASSORTMENT_CONFIG,
) -> tuple[ProductMarketAssortment, ...]:
    assortments: list[ProductMarketAssortment] = []

    for market_config in assortment_config:
        context.market(market_code=market_config.market_code)

        for product in products:
            assortment: ProductMarketAssortment | None = _generate_product_market_assortment(
                context=context,
                product=product,
                config=market_config,
            )

            if assortment is not None:
                assortments.append(assortment)

    return tuple(assortments)


def _generate_product_market_assortment(
    *,
    context: SimulationContext,
    product: Product,
    config: MarketAssortmentConfig,
) -> ProductMarketAssortment | None:
    rng: random.Random = _product_market_rng(
        context=context,
        product=product,
        market_code=config.market_code,
    )

    coverage_rate = config.coverage_rate

    if product.brand_name.startswith("Mercatura "):
        coverage_rate: float = min(
            1.0,
            coverage_rate + config.private_label_boost,
        )

    if rng.random() >= coverage_rate:
        return None

    launch_lag: int = rng.randint(
        a=0,
        b=config.max_launch_lag_days,
    )

    ranged_from: date = product.created_at + timedelta(days=launch_lag)

    if ranged_from > context.config.end_date:
        return None

    if product.discontinued_at is not None and ranged_from >= product.discontinued_at:
        return None

    assortment_id: str = context.ids.id_for(
        namespace="assortment",
        key=(f"{config.market_code}:{product.sku}"),
        prefix="ast",
    )

    return ProductMarketAssortment(
        assortment_id=assortment_id,
        product_id=product.product_id,
        sku=product.sku,
        market_code=config.market_code,
        ranged_from=ranged_from,
        ranged_to=product.discontinued_at,
    )


def _product_market_rng(
    *,
    context: SimulationContext,
    product: Product,
    market_code: str,
) -> random.Random:
    seed: int = context.seed_for(namespace=(f"assortment:{market_code}:{product.sku}"))

    return random.Random(seed)
