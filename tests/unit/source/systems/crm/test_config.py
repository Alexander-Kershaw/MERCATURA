import pytest

from mercatura.source.systems.crm.config import (
    DEFAULT_CUSTOMER_POPULATIONS,
    CustomerPopulation,
    CustomerSimulationConfig,
)


def test_default_population_totals_50100() -> None:
    assert sum(population.customer_count for population in DEFAULT_CUSTOMER_POPULATIONS) == 50_100


def test_rejects_empty_market_code() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="market_code",
    ):
        CustomerPopulation(
            market_code="",
            customer_count=100,
        )


def test_rejects_non_positive_customer_count() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="customer_count",
    ):
        CustomerPopulation(
            market_code="GB",
            customer_count=0,
        )


def test_rejects_negative_customer_count() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="customer_count",
    ):
        CustomerPopulation(
            market_code="GB",
            customer_count=-1,
        )


def test_rejects_invalid_history_years() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="history_years",
    ):
        CustomerSimulationConfig(history_years=0)


def test_rejects_invalid_minimum_active_days() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="minimum_active_days",
    ):
        CustomerSimulationConfig(minimum_active_days=0)


def test_rejects_negative_created_during_simulation_share() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(created_during_simulation_share=-0.01)


def test_rejects_created_during_simulation_share_above_one() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(created_during_simulation_share=1.01)


def test_rejects_negative_deactivation_probability() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(deactivation_probability=-0.01)


def test_rejects_deactivation_probability_above_one() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(deactivation_probability=1.01)


def test_rejects_negative_missing_email_probability() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(missing_email_probability=-0.01)


def test_rejects_missing_email_probability_above_one() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(missing_email_probability=1.01)


def test_rejects_negative_missing_phone_probability() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(missing_phone_probability=-0.01)


def test_rejects_missing_phone_probability_above_one() -> None:
    with pytest.raises(
        ValueError,
        match="probabilities",
    ):
        CustomerSimulationConfig(missing_phone_probability=1.01)


def test_probability_boundaries_are_valid() -> None:
    config = CustomerSimulationConfig(
        created_during_simulation_share=0.0,
        deactivation_probability=1.0,
        missing_email_probability=0.0,
        missing_phone_probability=1.0,
    )

    assert config.created_during_simulation_share == 0.0

    assert config.deactivation_probability == 1.0

    assert config.missing_email_probability == 0.0

    assert config.missing_phone_probability == 1.0


def test_rejects_duplicate_market_populations() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="must be unique",
    ):
        CustomerSimulationConfig(
            populations=(
                CustomerPopulation(
                    market_code="GB",
                    customer_count=100,
                ),
                CustomerPopulation(
                    market_code="GB",
                    customer_count=200,
                ),
            )
        )
