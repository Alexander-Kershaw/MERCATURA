from datetime import date

from mercatura.source.simulation.config import SimulationConfig
from mercatura.source.simulation.identity import build_simulation_id


def build_config(
    *,
    seed: int = 42,
    scenarios: tuple[str, ...] = (),
) -> SimulationConfig:
    return SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
        seed=seed,
        generator_version="0.1.0",
        scenarios=scenarios,
    )


def test_same_configuration_produces_same_simulation_id() -> None:
    first: SimulationConfig = build_config()
    second: SimulationConfig = build_config()

    assert build_simulation_id(config=first) == build_simulation_id(config=second)


def test_different_seed_changes_simulation_id() -> None:
    first: SimulationConfig = build_config(seed=42)
    second: SimulationConfig = build_config(seed=43)

    assert build_simulation_id(config=first) != build_simulation_id(config=second)


def test_different_scenario_changes_simulation_id() -> None:
    baseline: SimulationConfig = build_config()

    price_changes: SimulationConfig = build_config(scenarios=("price_changes",))

    assert build_simulation_id(config=baseline) != build_simulation_id(config=price_changes)


def test_scenario_order_does_not_change_simulation_id() -> None:
    first: SimulationConfig = build_config(scenarios=("reactivation", "price_changes"))

    second: SimulationConfig = build_config(scenarios=("price_changes", "reactivation"))

    assert build_simulation_id(config=first) == build_simulation_id(config=second)
