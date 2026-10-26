from datetime import date

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)


def build_snapshot(
    *,
    seed: int,
) -> dict[str, object]:
    config = SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
        seed=seed,
        scenarios=(
            "price_changes",
            "reactivation",
        ),
    )

    context: SimulationContext = SimulationContext.create(config)

    customer_ids: dict[str, str] = {
        market.market_code: context.ids.id_for(
            namespace="customer",
            key=f"{market.market_code}:000001",
            prefix="cus",
        )
        for market in config.markets
    }

    random_samples: dict[str, list[float]] = {
        market.market_code: [
            context.rng(
                namespace="crm",
                market_code=market.market_code,
            ).random()
            for _ in range(5)
        ]
        for market in config.markets
    }

    return {
        "simulation_id": context.simulation_id,
        "customer_ids": customer_ids,
        "random_samples": random_samples,
    }


def test_same_configuration_reproduces_same_simulation() -> None:
    first: dict[str, object] = build_snapshot(seed=42)
    second: dict[str, object] = build_snapshot(seed=42)

    assert first == second


def test_seed_change_changes_simulation() -> None:
    first: dict[str, object] = build_snapshot(seed=42)
    second: dict[str, object] = build_snapshot(seed=43)

    assert first != second
