from decimal import Decimal

import pytest

from mercatura.source.systems.wms.assortment_config import (
    WarehouseAssortmentSimulationConfig,
)


def test_default_config_is_valid() -> None:
    config = WarehouseAssortmentSimulationConfig()

    assert (
        config.low_demand_threshold < config.medium_demand_threshold < config.high_demand_threshold
    )


def test_rejects_non_increasing_thresholds() -> None:
    with pytest.raises(expected_exception=ValueError):
        WarehouseAssortmentSimulationConfig(
            low_demand_threshold=(Decimal(value="2")),
            medium_demand_threshold=(Decimal(value="1")),
        )


def test_rejects_zero_threshold() -> None:
    with pytest.raises(expected_exception=ValueError):
        WarehouseAssortmentSimulationConfig(
            low_demand_threshold=(Decimal(value="0")),
        )


def test_rejects_zero_warehouse_count() -> None:
    with pytest.raises(expected_exception=ValueError):
        WarehouseAssortmentSimulationConfig(low_demand_warehouse_count=0)


def test_rejects_decreasing_warehouse_counts() -> None:
    with pytest.raises(expected_exception=ValueError):
        WarehouseAssortmentSimulationConfig(
            low_demand_warehouse_count=2,
            medium_demand_warehouse_count=1,
        )


def test_rejects_non_positive_warehouse_weight() -> None:
    with pytest.raises(expected_exception=ValueError):
        WarehouseAssortmentSimulationConfig(regional_dc_weight=0.0)
