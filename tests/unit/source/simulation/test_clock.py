from datetime import UTC, date, datetime, timedelta

import pytest

from mercatura.source.simulation.clock import SimulationClock


def test_clock_iterates_inclusive_date_range() -> None:
    clock = SimulationClock(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2024, month=1, day=3),
    )

    assert list(clock.iter_dates()) == [
        date(year=2024, month=1, day=1),
        date(year=2024, month=1, day=2),
        date(year=2024, month=1, day=3),
    ]


def test_clock_contains_date() -> None:
    clock = SimulationClock(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2024, month=12, day=31),
    )

    assert clock.contains_date(value=date(year=2024, month=6, day=1))
    assert not clock.contains_date(value=date(year=2023, month=12, day=31))


def test_to_utc_converts_aware_datetime() -> None:
    clock = SimulationClock(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
    )

    london: datetime = datetime.fromisoformat("2026-06-01T14:00:00+01:00")

    assert clock.to_utc(value=london) == datetime(
        year=2026,
        month=6,
        day=1,
        hour=13,
        minute=0,
        tzinfo=UTC,
    )


def test_naive_datetime_is_rejected() -> None:
    clock = SimulationClock(
        start_date=date(year=2024, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="timezone-aware",
    ):
        clock.to_utc(value=datetime(year=2026, month=1, day=1, hour=12, minute=0))


def test_london_dst_day_is_23_hours() -> None:
    clock = SimulationClock(
        start_date=date(year=2026, month=1, day=1),
        end_date=date(year=2026, month=12, day=31),
    )

    start, end = clock.local_day_window_utc(
        value=date(year=2026, month=3, day=29),
        timezone="Europe/London",
    )

    assert end - start == timedelta(hours=23)
