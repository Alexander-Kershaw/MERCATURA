import pytest

from mercatura.source.systems.oms.config import (
    DEFAULT_MARKET_ORDER_CONFIGS,
    MarketOrderConfig,
    OMSSimulationConfig,
)


def test_default_order_population_totals_221000() -> None:
    assert sum(market.order_count for market in DEFAULT_MARKET_ORDER_CONFIGS) == 221_000


def test_rejects_empty_market_code() -> None:
    with pytest.raises(
        ValueError,
        match="market_code",
    ):
        MarketOrderConfig(
            market_code="",
            order_count=100,
        )


def test_rejects_zero_order_count() -> None:
    with pytest.raises(
        ValueError,
        match="order_count",
    ):
        MarketOrderConfig(
            market_code="GB",
            order_count=0,
        )


def test_rejects_negative_order_count() -> None:
    with pytest.raises(
        ValueError,
        match="order_count",
    ):
        MarketOrderConfig(
            market_code="GB",
            order_count=-1,
        )


def test_rejects_duplicate_market_configurations() -> None:
    with pytest.raises(
        ValueError,
        match="must be unique",
    ):
        OMSSimulationConfig(
            market_configs=(
                MarketOrderConfig(
                    market_code="GB",
                    order_count=100,
                ),
                MarketOrderConfig(
                    market_code="GB",
                    order_count=200,
                ),
            )
        )


def test_default_channel_probabilities_sum_to_one() -> None:
    config = OMSSimulationConfig()

    assert (
        config.store_channel_probability
        + config.web_channel_probability
        + config.mobile_channel_probability
    ) == pytest.approx(1.0)


def test_rejects_negative_store_channel_probability() -> None:
    with pytest.raises(
        ValueError,
        match="channel probabilities",
    ):
        OMSSimulationConfig(
            store_channel_probability=-0.01,
            web_channel_probability=0.83,
            mobile_channel_probability=0.18,
        )


def test_rejects_channel_probability_above_one() -> None:
    with pytest.raises(
        ValueError,
        match="channel probabilities",
    ):
        OMSSimulationConfig(
            store_channel_probability=1.01,
            web_channel_probability=0.0,
            mobile_channel_probability=0.0,
        )


def test_rejects_channel_probabilities_not_summing_to_one() -> None:
    with pytest.raises(
        ValueError,
        match="channel probabilities must sum to 1",
    ):
        OMSSimulationConfig(
            store_channel_probability=0.40,
            web_channel_probability=0.30,
            mobile_channel_probability=0.20,
        )


def test_rejects_negative_cancellation_probability() -> None:
    with pytest.raises(
        ValueError,
        match="cancellation_probability",
    ):
        OMSSimulationConfig(cancellation_probability=-0.01)


def test_rejects_cancellation_probability_above_one() -> None:
    with pytest.raises(
        ValueError,
        match="cancellation_probability",
    ):
        OMSSimulationConfig(cancellation_probability=1.01)


def test_rejects_negative_cancellation_delay() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_cancellation_delay_days",
    ):
        OMSSimulationConfig(maximum_cancellation_delay_days=-1)


def test_rejects_empty_line_count_distribution() -> None:
    with pytest.raises(
        ValueError,
        match="line count probabilities cannot be empty",
    ):
        OMSSimulationConfig(line_count_probabilities=())


def test_rejects_invalid_line_count_probability() -> None:
    with pytest.raises(
        ValueError,
        match="line count probabilities",
    ):
        OMSSimulationConfig(
            line_count_probabilities=(
                0.5,
                0.4,
                0.2,
                -0.1,
            )
        )


def test_rejects_line_probabilities_not_summing_to_one() -> None:
    with pytest.raises(
        ValueError,
        match="line count probabilities must sum to 1",
    ):
        OMSSimulationConfig(
            line_count_probabilities=(
                0.5,
                0.3,
            )
        )


def test_rejects_empty_quantity_distribution() -> None:
    with pytest.raises(
        ValueError,
        match="item quantity probabilities cannot be empty",
    ):
        OMSSimulationConfig(item_quantity_probabilities=())


def test_rejects_invalid_item_quantity_probability() -> None:
    with pytest.raises(
        ValueError,
        match="item quantity probabilities",
    ):
        OMSSimulationConfig(
            item_quantity_probabilities=(
                0.9,
                0.2,
                -0.1,
            )
        )


def test_rejects_item_quantity_probabilities_not_summing_to_one() -> None:
    with pytest.raises(
        ValueError,
        match="item quantity probabilities must sum to 1",
    ):
        OMSSimulationConfig(
            item_quantity_probabilities=(
                0.5,
                0.4,
            )
        )


def test_rejects_negative_customer_propensity_sigma() -> None:
    with pytest.raises(
        ValueError,
        match="customer_propensity_sigma",
    ):
        OMSSimulationConfig(customer_propensity_sigma=-0.01)


def test_rejects_zero_customer_propensity_cap() -> None:
    with pytest.raises(
        ValueError,
        match="customer_propensity_cap",
    ):
        OMSSimulationConfig(customer_propensity_cap=0.0)


def test_rejects_negative_customer_propensity_cap() -> None:
    with pytest.raises(
        ValueError,
        match="customer_propensity_cap",
    ):
        OMSSimulationConfig(customer_propensity_cap=-1.0)
