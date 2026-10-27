from collections import defaultdict
from decimal import Decimal
from itertools import pairwise

from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)


def validate_prices(
    prices: tuple[ProductPrice, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_ids(prices)
    _validate_positive_prices(prices)
    _validate_references(
        prices,
        assortments,
    )
    _validate_currencies(
        prices,
        context,
    )
    _validate_intervals(prices)
    _validate_histories(
        prices,
        assortments,
    )


def _validate_unique_ids(
    prices: tuple[ProductPrice, ...],
) -> None:
    ids = [price.price_id for price in prices]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate price_id detected")


def _validate_positive_prices(
    prices: tuple[ProductPrice, ...],
) -> None:
    for price in prices:
        if not isinstance(
            price.list_price,
            Decimal,
        ):
            raise ValueError(f"{price.price_id} does not use Decimal")

        if price.list_price <= Decimal("0"):
            raise ValueError(f"{price.price_id} has non-positive price")


def _validate_references(
    prices: tuple[ProductPrice, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    for price in prices:
        assortment: ProductMarketAssortment | None = by_id.get(price.assortment_id)

        if assortment is None:
            raise ValueError(f"{price.price_id} references unknown assortment")

        if price.product_id != assortment.product_id:
            raise ValueError(f"{price.price_id} product_id does not match assortment")

        if price.sku != assortment.sku:
            raise ValueError(f"{price.price_id} SKU does not match assortment")

        if price.market_code != assortment.market_code:
            raise ValueError(f"{price.price_id} market does not match assortment")


def _validate_currencies(
    prices: tuple[ProductPrice, ...],
    context: SimulationContext,
) -> None:
    currency_by_market: dict[str, str] = {
        market.market_code: market.currency for market in context.config.markets
    }

    for price in prices:
        expected: str | None = currency_by_market.get(price.market_code)

        if expected is None:
            raise ValueError(f"unknown pricing market: {price.market_code}")

        if price.currency != expected:
            raise ValueError(f"{price.price_id} uses incorrect market currency")


def _validate_intervals(
    prices: tuple[ProductPrice, ...],
) -> None:
    for price in prices:
        if price.version <= 0:
            raise ValueError(f"{price.price_id} has invalid version")

        if price.effective_to is not None and price.effective_to <= price.effective_from:
            raise ValueError(f"{price.price_id} has invalid effective interval")


def _validate_histories(
    prices: tuple[ProductPrice, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    grouped: dict[
        str,
        list[ProductPrice],
    ] = defaultdict(list)

    for price in prices:
        grouped[price.assortment_id].append(price)

    for assortment in assortments:
        history: list[ProductPrice] = sorted(
            grouped[assortment.assortment_id],
            key=lambda row: row.effective_from,
        )

        if not history:
            raise ValueError(f"no price history for {assortment.assortment_id}")

        if history[0].effective_from != assortment.ranged_from:
            raise ValueError("price history does not start at assortment start")

        versions: list[int] = [row.version for row in history]

        expected_versions: list[int] = list(
            range(
                1,
                len(history) + 1,
            )
        )

        if versions != expected_versions:
            raise ValueError("price versions are not sequential")

        for previous, current in pairwise(history):
            if previous.effective_to != current.effective_from:
                raise ValueError("price history contains a gap or overlap")

        if history[-1].effective_to != assortment.ranged_to:
            raise ValueError("price history does not end at assortment end")
