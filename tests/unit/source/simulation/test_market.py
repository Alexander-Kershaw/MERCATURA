import pytest

from mercatura.source.simulation.market import MarketConfig


def test_market_accepts_valid_configuration() -> None:
    market = MarketConfig(
        market_code="GB",
        country_name="United Kingdom",
        legal_entity="Mercatura UK Ltd",
        currency="GBP",
        locale="en_GB",
        timezone="Europe/London",
        tax_regime="GB_VAT",
    )

    assert market.market_code == "GB"
    assert market.currency == "GBP"


def test_market_rejects_invalid_currency() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="currency must be",
    ):
        MarketConfig(
            market_code="GB",
            country_name="United Kingdom",
            legal_entity="Mercatura UK Ltd",
            currency="gbp",
            locale="en_GB",
            timezone="Europe/London",
            tax_regime="GB_VAT",
        )


def test_market_rejects_unknown_timezone() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="unknown timezone",
    ):
        MarketConfig(
            market_code="GB",
            country_name="United Kingdom",
            legal_entity="Mercatura UK Ltd",
            currency="GBP",
            locale="en_GB",
            timezone="Not/A_Timezone",
            tax_regime="GB_VAT",
        )
