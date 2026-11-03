from decimal import Decimal

import pytest

from mercatura.source.systems.procurement.purchase_order_config import (
    PurchaseOrderSimulationConfig,
)


def test_default_config_is_valid() -> None:
    config = PurchaseOrderSimulationConfig()

    assert config.cycle_options_days
    assert config.primary_weight > 0


def test_rejects_empty_cycle_options() -> None:
    with pytest.raises(expected_exception=ValueError):
        PurchaseOrderSimulationConfig(
            cycle_options_days=(),
        )


@pytest.mark.parametrize(
    argnames="cycles",
    argvalues=(
        (0,),
        (-7,),
        (14, 0, 28),
    ),
)
def test_rejects_non_positive_cycle_days(
    cycles: tuple[int, ...],
) -> None:
    with pytest.raises(expected_exception=ValueError):
        PurchaseOrderSimulationConfig(
            cycle_options_days=cycles,
        )


def test_rejects_unsorted_cycle_options() -> None:
    with pytest.raises(expected_exception=ValueError):
        PurchaseOrderSimulationConfig(
            cycle_options_days=(
                28,
                14,
                56,
            ),
        )


@pytest.mark.parametrize(
    argnames="field",
    argvalues=(
        "primary",
        "secondary",
        "backup",
    ),
)
def test_rejects_negative_source_weight(
    field: str,
) -> None:
    if field == "primary":
        with pytest.raises(expected_exception=ValueError):
            PurchaseOrderSimulationConfig(
                primary_weight=-0.1,
            )

    elif field == "secondary":
        with pytest.raises(expected_exception=ValueError):
            PurchaseOrderSimulationConfig(
                secondary_weight=-0.1,
            )

    else:
        with pytest.raises(expected_exception=ValueError):
            PurchaseOrderSimulationConfig(
                backup_weight=-0.1,
            )


def test_rejects_all_zero_source_weights() -> None:
    with pytest.raises(expected_exception=ValueError):
        PurchaseOrderSimulationConfig(
            primary_weight=0.0,
            secondary_weight=0.0,
            backup_weight=0.0,
        )


def test_rejects_non_positive_minimum_quantity_factor() -> None:
    with pytest.raises(expected_exception=ValueError):
        PurchaseOrderSimulationConfig(
            minimum_quantity_factor=(Decimal(value="0")),
        )


def test_rejects_maximum_quantity_factor_below_minimum() -> None:
    with pytest.raises(expected_exception=ValueError):
        PurchaseOrderSimulationConfig(
            minimum_quantity_factor=(Decimal(value="1.10")),
            maximum_quantity_factor=(Decimal(value="0.90")),
        )
