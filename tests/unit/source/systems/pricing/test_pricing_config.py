from decimal import Decimal
from typing import Literal

import pytest

from mercatura.source.simulation.market import (
    DEFAULT_MARKETS,
)
from mercatura.source.systems.pricing.config import (
    DEFAULT_MARKET_PRICING,
    MarketPricingConfig,
    PricingSimulationConfig,
)


def test_every_market_has_pricing_config() -> None:
    markets: set[str] = {market.market_code for market in DEFAULT_MARKETS}

    pricing_markets: set[str] = {config.market_code for config in DEFAULT_MARKET_PRICING}

    assert markets == pricing_markets


def test_market_pricing_codes_are_unique() -> None:
    codes: list[str] = [config.market_code for config in DEFAULT_MARKET_PRICING]

    assert len(codes) == len(set(codes))


def test_market_pricing_values_are_positive() -> None:
    for config in DEFAULT_MARKET_PRICING:
        assert config.local_currency_scale > Decimal(value="0")

        assert config.market_price_index > Decimal(value="0")

        assert config.minor_unit > Decimal(value="0")


@pytest.mark.parametrize(
    argnames=("field", "value"),
    argvalues=(
        (
            "local_currency_scale",
            Decimal(value="0"),
        ),
        (
            "market_price_index",
            Decimal(value="0"),
        ),
        (
            "minor_unit",
            Decimal(value="0"),
        ),
    ),
)
def test_market_pricing_rejects_non_positive_values(
    field: str,
    value: Decimal,
) -> None:
    values = {
        "market_code": "GB",
        "local_currency_scale": Decimal(value="1"),
        "market_price_index": Decimal(value="1"),
        "minor_unit": Decimal(value="0.01"),
    }

    values[field] = value

    with pytest.raises(expected_exception=ValueError):
        MarketPricingConfig(**values)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-1, 4),
)
def test_pricing_config_rejects_invalid_maximum_changes(
    value: int,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        PricingSimulationConfig(maximum_changes=value)


ProbabilityField = Literal[
    "first_change_probability",
    "second_change_probability",
    "third_change_probability",
]


@pytest.mark.parametrize(
    argnames=("field", "value"),
    argvalues=(
        (
            "first_change_probability",
            -0.01,
        ),
        (
            "first_change_probability",
            1.01,
        ),
        (
            "second_change_probability",
            -0.01,
        ),
        (
            "third_change_probability",
            1.01,
        ),
    ),
)
def test_pricing_config_rejects_invalid_probabilities(
    field: ProbabilityField,
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        if field == "first_change_probability":
            PricingSimulationConfig(first_change_probability=value)

        elif field == "second_change_probability":
            PricingSimulationConfig(second_change_probability=value)

        else:
            PricingSimulationConfig(third_change_probability=value)
