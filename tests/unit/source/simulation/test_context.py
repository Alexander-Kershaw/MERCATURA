from datetime import date
from random import Random

import pytest

from mercatura.source.simulation.config import SimulationConfig
from mercatura.source.simulation.context import SimulationContext
from mercatura.source.simulation.market import MarketConfig


def build_context(
    seed: int = 42,
) -> SimulationContext:
    config = SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
        seed=seed,
    )

    return SimulationContext.create(config)


def test_context_builds_deterministically() -> None:
    first: SimulationContext = build_context()
    second: SimulationContext = build_context()

    assert first.simulation_id == second.simulation_id


def test_context_resolves_market() -> None:
    context: SimulationContext = build_context()

    germany: MarketConfig = context.market(market_code="DE")

    assert germany.currency == "EUR"
    assert germany.locale == "de_DE"


def test_context_rejects_unknown_market() -> None:
    context: SimulationContext = build_context()

    with pytest.raises(
        expected_exception=KeyError,
        match="unknown market",
    ):
        context.market(market_code="ZZ")


def test_market_rng_is_deterministic() -> None:
    first: SimulationContext = build_context()
    second: SimulationContext = build_context()

    first_rng: Random = first.rng(
        namespace="crm",
        market_code="CN",
    )

    second_rng: Random = second.rng(
        namespace="crm",
        market_code="CN",
    )

    assert [first_rng.random() for _ in range(10)] == [second_rng.random() for _ in range(10)]


def test_market_rng_isolated_by_market() -> None:
    context: SimulationContext = build_context()

    gb: Random = context.rng(
        namespace="crm",
        market_code="GB",
    )

    no: Random = context.rng(
        namespace="crm",
        market_code="NO",
    )

    assert [gb.random() for _ in range(10)] != [no.random() for _ in range(10)]


def test_context_ids_are_deterministic() -> None:
    first: SimulationContext = build_context()
    second: SimulationContext = build_context()

    assert first.ids.id_for(
        namespace="customer",
        key="RU:000001",
        prefix="cus",
    ) == second.ids.id_for(
        namespace="customer",
        key="RU:000001",
        prefix="cus",
    )
