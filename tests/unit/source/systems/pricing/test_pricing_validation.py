from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.pricing.validation import (
    validate_prices,
)


def history_for(
    assortment_id: str,
    prices: tuple[ProductPrice, ...],
) -> list[ProductPrice]:
    return sorted(
        (price for price in prices if price.assortment_id == assortment_id),
        key=lambda row: row.version,
    )


def replace_price(
    prices: tuple[ProductPrice, ...],
    replacement: ProductPrice,
) -> tuple[ProductPrice, ...]:
    return tuple(replacement if row.price_id == replacement.price_id else row for row in prices)


def find_multi_version_assortment(
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> ProductMarketAssortment:
    for assortment in assortments:
        if (
            len(
                history_for(
                    assortment.assortment_id,
                    prices,
                )
            )
            >= 2
        ):
            return assortment

    raise AssertionError("expected at least one multi-version price history")


def test_valid_pricing_dataset_passes_validation(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    validate_prices(
        prices,
        assortments,
        context,
    )


def test_validation_rejects_duplicate_price_id(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    duplicate = replace(
        prices[1],
        price_id=prices[0].price_id,
    )

    broken = (*prices, duplicate)

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_zero_price(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row = replace(
        prices[0],
        list_price=Decimal("0"),
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_negative_price(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row = replace(
        prices[0],
        list_price=Decimal("-1.00"),
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_unknown_assortment(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row = replace(
        prices[0],
        assortment_id="ast_missing",
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        (
            "product_id",
            "prd_wrong",
        ),
        (
            "sku",
            "MRC-WRONG",
        ),
    ),
)
def test_validation_rejects_assortment_metadata_mismatch(
    field: str,
    value: str,
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row = replace(
        prices[0],
        **{
            field: value,
        },
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_wrong_currency(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row = replace(
        prices[0],
        currency="ZZZ",
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_non_positive_version(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row = replace(
        prices[0],
        version=0,
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_non_sequential_versions(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assortment = find_multi_version_assortment(
        assortments,
        prices,
    )

    history = history_for(
        assortment.assortment_id,
        prices,
    )

    broken_row = replace(
        history[1],
        version=99,
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_history_gap(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assortment = find_multi_version_assortment(
        assortments,
        prices,
    )

    history = history_for(
        assortment.assortment_id,
        prices,
    )

    first = history[0]
    second = history[1]

    broken_row = replace(
        first,
        effective_to=(second.effective_from - timedelta(days=1)),
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_history_overlap(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assortment = find_multi_version_assortment(
        assortments,
        prices,
    )

    history = history_for(
        assortment.assortment_id,
        prices,
    )

    first = history[0]
    second = history[1]

    broken_row = replace(
        first,
        effective_to=(second.effective_from + timedelta(days=1)),
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_late_history_start(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assortment = assortments[0]

    history = history_for(
        assortment.assortment_id,
        prices,
    )

    first = history[0]

    broken_row = replace(
        first,
        effective_from=(first.effective_from + timedelta(days=1)),
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_invalid_interval(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target = prices[0]

    broken_row = replace(
        target,
        effective_to=target.effective_from,
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )


def test_validation_rejects_wrong_final_boundary(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    assortment = next(assortment for assortment in assortments if assortment.ranged_to is None)

    history = history_for(
        assortment.assortment_id,
        prices,
    )

    final = history[-1]

    broken_row = replace(
        final,
        effective_to=(context.config.end_date),
    )

    broken = replace_price(
        prices,
        broken_row,
    )

    with pytest.raises(ValueError):
        validate_prices(
            broken,
            assortments,
            context,
        )
