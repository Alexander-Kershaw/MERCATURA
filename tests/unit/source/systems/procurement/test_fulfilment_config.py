from decimal import Decimal

import pytest

from mercatura.source.systems.procurement.fulfilment_config import (
    FulfilmentSimulationConfig,
)


def test_default_probabilities_sum_to_one() -> None:
    config = FulfilmentSimulationConfig()

    total: float = (
        config.on_time_full_probability
        + config.early_full_probability
        + config.late_full_probability
        + config.split_full_probability
        + config.short_shipped_probability
        + config.cancelled_probability
    )

    assert total == pytest.approx(expected=1.0)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_on_time_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(on_time_full_probability=value)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_early_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(early_full_probability=value)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_late_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(late_full_probability=value)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_split_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(split_full_probability=value)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_short_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(short_shipped_probability=value)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_cancel_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(cancelled_probability=value)


def test_rejects_probabilities_not_summing_to_one() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(on_time_full_probability=0.50)


def test_rejects_negative_maximum_early_days() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(maximum_early_days=-1)


def test_rejects_negative_maximum_late_days() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(maximum_late_days=-1)


def test_rejects_non_positive_split_delay() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(split_maximum_delay_days=0)


def test_rejects_invalid_split_fraction_range() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(
            split_minimum_fraction=(Decimal(value="0.80")),
            split_maximum_fraction=(Decimal(value="0.70")),
        )


def test_rejects_split_fraction_of_one() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(
            split_maximum_fraction=(Decimal(value="1")),
        )


def test_rejects_invalid_short_fraction_range() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(
            short_minimum_fraction=(Decimal(value="0.95")),
            short_maximum_fraction=(Decimal(value="0.75")),
        )


def test_rejects_short_fraction_of_one() -> None:
    with pytest.raises(expected_exception=ValueError):
        FulfilmentSimulationConfig(
            short_maximum_fraction=(Decimal(value="1")),
        )
