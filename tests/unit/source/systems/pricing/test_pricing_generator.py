from collections import defaultdict
from datetime import date
from decimal import Decimal
from itertools import pairwise

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.pricing.generator import (
    generate_prices,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)


def build_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(2024, 1, 1),
            end_date=date(2026, 12, 31),
            seed=42,
        )
    )


def histories_by_assortment(
    prices: tuple[ProductPrice, ...],
) -> dict[str, list[ProductPrice]]:
    histories: dict[
        str,
        list[ProductPrice],
    ] = defaultdict(list)

    for price in prices:
        histories[price.assortment_id].append(price)

    for history in histories.values():
        history.sort(key=lambda row: row.version)

    return histories


def test_pricing_generation_is_deterministic() -> None:
    first_context: SimulationContext = build_context()
    second_context: SimulationContext = build_context()

    first_products: tuple[Product, ...] = generate_products(context=first_context)

    second_products: tuple[Product, ...] = generate_products(context=second_context)

    first_assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context=first_context,
        products=first_products,
    )

    second_assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context=second_context,
        products=second_products,
    )

    assert generate_prices(
        context=first_context,
        products=first_products,
        assortments=first_assortments,
    ) == generate_prices(
        context=second_context,
        products=second_products,
        assortments=second_assortments,
    )


def test_every_assortment_has_price_history(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    priced_assortments: set[str] = {price.assortment_id for price in prices}

    expected: set[str] = {assortment.assortment_id for assortment in assortments}

    assert priced_assortments == expected


def test_at_least_one_price_row_per_assortment(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assert len(prices) >= len(assortments)


def test_price_ids_are_unique(
    prices: tuple[ProductPrice, ...],
) -> None:
    identifiers: list[str] = [price.price_id for price in prices]

    assert len(identifiers) == len(set(identifiers))


def test_all_prices_are_decimal(
    prices: tuple[ProductPrice, ...],
) -> None:
    assert all(
        isinstance(
            price.list_price,
            Decimal,
        )
        for price in prices
    )


def test_all_prices_are_positive(
    prices: tuple[ProductPrice, ...],
) -> None:
    assert all(price.list_price > Decimal(value="0") for price in prices)


def test_price_currency_matches_market(
    context: SimulationContext,
    prices: tuple[ProductPrice, ...],
) -> None:
    currencies: dict[str, str] = {
        market.market_code: market.currency for market in context.config.markets
    }

    for price in prices:
        assert price.currency == currencies[price.market_code]


def test_price_references_known_assortment(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assortment_ids: set[str] = {assortment.assortment_id for assortment in assortments}

    assert all(price.assortment_id in assortment_ids for price in prices)


def test_price_metadata_matches_assortment(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    for price in prices:
        assortment: ProductMarketAssortment = by_id[price.assortment_id]

        assert price.product_id == assortment.product_id

        assert price.sku == assortment.sku

        assert price.market_code == assortment.market_code


def test_histories_start_at_assortment_start(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    histories: dict[str, list[ProductPrice]] = histories_by_assortment(prices)

    for assortment in assortments:
        history: list[ProductPrice] = histories[assortment.assortment_id]

        assert history[0].effective_from == assortment.ranged_from


def test_histories_end_at_assortment_end(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    histories: dict[str, list[ProductPrice]] = histories_by_assortment(prices)

    for assortment in assortments:
        history: list[ProductPrice] = histories[assortment.assortment_id]

        assert history[-1].effective_to == assortment.ranged_to


def test_price_versions_are_sequential(
    prices: tuple[ProductPrice, ...],
) -> None:
    histories: dict[str, list[ProductPrice]] = histories_by_assortment(prices)

    for history in histories.values():
        assert [price.version for price in history] == list(
            range(
                1,
                len(history) + 1,
            )
        )


def test_histories_have_no_gaps_or_overlaps(
    prices: tuple[ProductPrice, ...],
) -> None:
    histories: dict[str, list[ProductPrice]] = histories_by_assortment(prices)

    for history in histories.values():
        for previous, current in pairwise(history):
            assert previous.effective_to == current.effective_from


def test_all_closed_intervals_are_positive_length(
    prices: tuple[ProductPrice, ...],
) -> None:
    for price in prices:
        if price.effective_to is not None:
            assert price.effective_to > price.effective_from


def test_some_assortments_have_multiple_versions(
    prices: tuple[ProductPrice, ...],
) -> None:
    histories: dict[str, list[ProductPrice]] = histories_by_assortment(prices)

    assert any(len(history) > 1 for history in histories.values())


def test_some_prices_actually_change(
    prices: tuple[ProductPrice, ...],
) -> None:
    histories: dict[str, list[ProductPrice]] = histories_by_assortment(prices)

    assert any(len({price.list_price for price in history}) > 1 for history in histories.values())


def test_price_changes_do_not_predate_simulation(
    context: SimulationContext,
    prices: tuple[ProductPrice, ...],
) -> None:
    later_versions: list[ProductPrice] = [price for price in prices if price.version > 1]

    assert later_versions

    assert all(price.effective_from >= context.config.start_date for price in later_versions)


def test_price_changes_do_not_exceed_simulation_end(
    context: SimulationContext,
    prices: tuple[ProductPrice, ...],
) -> None:
    assert all(
        price.effective_from <= context.config.end_date for price in prices if price.version > 1
    )


def test_generation_is_stable_when_assortment_order_changes() -> None:
    first_context: SimulationContext = build_context()
    second_context: SimulationContext = build_context()

    first_products: tuple[Product, ...] = generate_products(context=first_context)

    second_products: tuple[Product, ...] = generate_products(context=second_context)

    first_assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context=first_context,
        products=first_products,
    )

    second_assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context=second_context,
        products=second_products,
    )

    first_prices: tuple[ProductPrice, ...] = generate_prices(
        context=first_context,
        products=first_products,
        assortments=first_assortments,
    )

    second_prices: tuple[ProductPrice, ...] = generate_prices(
        context=second_context,
        products=second_products,
        assortments=tuple(reversed(second_assortments)),
    )

    def normalize(
        rows: tuple[ProductPrice, ...],
    ) -> list[ProductPrice]:
        return sorted(
            rows,
            key=lambda row: (
                row.market_code,
                row.sku,
                row.version,
            ),
        )

    assert normalize(rows=first_prices) == normalize(rows=second_prices)
