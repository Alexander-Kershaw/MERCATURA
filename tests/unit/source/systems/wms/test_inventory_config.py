import pytest

from mercatura.source.systems.wms.inventory_config import (
    InventoryMovementSimulationConfig,
)


def test_default_config_is_valid() -> None:
    config = InventoryMovementSimulationConfig()

    total: float = (
        config.same_day_putaway_probability
        + config.next_day_putaway_probability
        + config.two_day_putaway_probability
    )

    assert total == pytest.approx(expected=1.0)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_same_day_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        InventoryMovementSimulationConfig(same_day_putaway_probability=(value))


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_next_day_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        InventoryMovementSimulationConfig(next_day_putaway_probability=(value))


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_two_day_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        InventoryMovementSimulationConfig(two_day_putaway_probability=(value))


def test_rejects_probabilities_not_summing_to_one() -> None:
    with pytest.raises(expected_exception=ValueError):
        InventoryMovementSimulationConfig(same_day_putaway_probability=(0.50))
