from datetime import date

import pytest

from mercatura.source.simulation.config import SimulationConfig


def test_config_calculates_inclusive_day_count() -> None:
    config = SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2024, month=1, day=31),
    )

    assert config.day_count == 31


def test_config_rejects_end_date_before_start_date() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="start_date must be before end_date",
    ):
        SimulationConfig(
            start_date=date(year=2024, month=2, day=1),
            end_date=date(year=2024, month=1, day=1),
        )


def test_config_rejects_negative_seed() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="seed must be a non-negative integer",
    ):
        SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2024, month=12, day=31),
            seed=-1,
        )


def test_canonical_payload_normalizes_scenario_order() -> None:
    first = SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
        scenarios=("reactivation", "price_changes"),
    )

    second = SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
        scenarios=("price_changes", "reactivation"),
    )

    assert first.canonical_payload() == second.canonical_payload()
