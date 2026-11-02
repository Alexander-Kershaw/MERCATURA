from decimal import Decimal

from mercatura.source.reference.currency import (
    CURRENCY_MINOR_UNITS,
)
from mercatura.source.simulation.market import (
    DEFAULT_MARKETS,
)


def test_every_market_currency_has_minor_unit() -> None:
    currencies: set[str] = {market.currency for market in DEFAULT_MARKETS}

    assert currencies <= set(CURRENCY_MINOR_UNITS)


def test_currency_minor_units_are_decimal() -> None:
    assert all(
        isinstance(
            value,
            Decimal,
        )
        for value in CURRENCY_MINOR_UNITS.values()
    )


def test_currency_minor_units_are_positive() -> None:
    assert all(value > Decimal(value="0") for value in CURRENCY_MINOR_UNITS.values())


def test_jpy_and_krw_use_whole_units() -> None:
    assert CURRENCY_MINOR_UNITS["JPY"] == Decimal(value="1")

    assert CURRENCY_MINOR_UNITS["KRW"] == Decimal(value="1")
