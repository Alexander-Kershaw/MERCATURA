import pytest

from mercatura.source.systems.loyalty.config import (
    LoyaltySimulationConfig,
    MarketLoyaltyConfig,
)


def test_valid_market_config() -> None:
    config = MarketLoyaltyConfig(
        market_code="GB",
        enrolment_probability=0.45,
    )

    assert config.enrolment_probability == 0.45


def test_rejects_empty_market_code() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="market_code",
    ):
        MarketLoyaltyConfig(
            market_code="",
            enrolment_probability=0.45,
        )


def test_rejects_negative_enrolment_probability() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="enrolment_probability",
    ):
        MarketLoyaltyConfig(
            market_code="GB",
            enrolment_probability=-0.01,
        )


def test_rejects_enrolment_probability_above_one() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="enrolment_probability",
    ):
        MarketLoyaltyConfig(
            market_code="GB",
            enrolment_probability=1.01,
        )


def test_rejects_invalid_maximum_enrolment_lag() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="maximum_enrolment_lag_days",
    ):
        LoyaltySimulationConfig(maximum_enrolment_lag_days=0)


def test_rejects_invalid_minimum_membership_days() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="minimum_membership_days_before_closure",
    ):
        LoyaltySimulationConfig(minimum_membership_days_before_closure=0)


def test_rejects_duplicate_market_configuration() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="must be unique",
    ):
        LoyaltySimulationConfig(
            market_configs=(
                MarketLoyaltyConfig(
                    market_code="GB",
                    enrolment_probability=0.4,
                ),
                MarketLoyaltyConfig(
                    market_code="GB",
                    enrolment_probability=0.5,
                ),
            )
        )


def test_rejects_negative_tier_probability() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="tier probabilities",
    ):
        LoyaltySimulationConfig(
            standard_tier_probability=-0.01,
            silver_tier_probability=0.91,
            gold_tier_probability=0.08,
            platinum_tier_probability=0.02,
        )


def test_rejects_tier_probability_above_one() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="tier probabilities",
    ):
        LoyaltySimulationConfig(
            standard_tier_probability=1.01,
            silver_tier_probability=0.0,
            gold_tier_probability=0.0,
            platinum_tier_probability=0.0,
        )


def test_rejects_tier_probabilities_not_summing_to_one() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="sum to 1",
    ):
        LoyaltySimulationConfig(
            standard_tier_probability=0.50,
            silver_tier_probability=0.20,
            gold_tier_probability=0.10,
            platinum_tier_probability=0.05,
        )


def test_default_tier_probabilities_sum_to_one() -> None:
    config = LoyaltySimulationConfig()

    total: float = (
        config.standard_tier_probability
        + config.silver_tier_probability
        + config.gold_tier_probability
        + config.platinum_tier_probability
    )

    assert total == pytest.approx(expected=1.0)
