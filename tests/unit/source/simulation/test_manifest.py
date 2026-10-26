from datetime import UTC, date, datetime

import pytest

from mercatura.source.simulation.config import SimulationConfig
from mercatura.source.simulation.context import SimulationContext
from mercatura.source.simulation.manifest import SimulationManifest


def build_context() -> SimulationContext:
    config = SimulationConfig(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
        seed=42,
        scenarios=(
            "price_changes",
            "reactivation",
        ),
    )

    return SimulationContext.create(config)


def test_manifest_contains_simulation_metadata() -> None:
    context: SimulationContext = build_context()

    manifest: SimulationManifest = SimulationManifest.from_context(
        context,
        created_at=datetime(
            year=2026,
            month=10,
            day=26,
            hour=9,
            minute=0,
            tzinfo=UTC,
        ),
    )

    assert manifest.simulation_id == context.simulation_id
    assert manifest.seed == 42
    assert manifest.start_date == "2024-01-01"
    assert manifest.end_date == "2026-12-31"
    assert manifest.reporting_currency == "GBP"

    assert manifest.markets == (
        "CN",
        "DE",
        "FR",
        "GB",
        "JP",
        "KR",
        "NL",
        "NO",
        "PL",
        "RU",
        "US",
    )


def test_manifest_normalizes_scenario_order() -> None:
    context: SimulationContext = build_context()

    manifest: SimulationManifest = SimulationManifest.from_context(
        context,
        created_at=datetime(
            year=2026,
            month=10,
            day=26,
            hour=9,
            minute=0,
            tzinfo=UTC,
        ),
    )

    assert manifest.scenarios == (
        "price_changes",
        "reactivation",
    )


def test_manifest_converts_timestamp_to_utc() -> None:
    context: SimulationContext = build_context()

    local_time: datetime = datetime.fromisoformat("2026-10-26T10:00:00+01:00")

    manifest: SimulationManifest = SimulationManifest.from_context(
        context,
        created_at=local_time,
    )

    assert manifest.created_at_utc == ("2026-10-26T09:00:00+00:00")


def test_manifest_rejects_naive_timestamp() -> None:
    context: SimulationContext = build_context()

    with pytest.raises(
        expected_exception=ValueError,
        match="timezone-aware",
    ):
        SimulationManifest.from_context(
            context,
            created_at=datetime(
                year=2026,
                month=10,
                day=26,
                hour=9,
                minute=0,
            ),
        )
