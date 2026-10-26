from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


class SimulationClock:
    def __init__(
        self,
        start_date: date,
        end_date: date,
    ) -> None:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        self._start_date: date = start_date
        self._end_date: date = end_date

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def end_date(self) -> date:
        return self._end_date

    def contains_date(self, value: date) -> bool:
        return self.start_date <= value <= self.end_date

    def iter_dates(self) -> Iterator[date]:
        current: date = self.start_date

        while current <= self.end_date:
            yield current
            current += timedelta(days=1)

    def to_utc(self, value: datetime) -> datetime:

        self._require_aware(value)

        return value.astimezone(tz=UTC)

    def to_timezone(
        self,
        value: datetime,
        timezone: str,
    ) -> datetime:

        self._require_aware(value)

        return value.astimezone(tz=ZoneInfo(key=timezone))

    def local_day_window_utc(
        self,
        value: date,
        timezone: str,
    ) -> tuple[datetime, datetime]:

        zone = ZoneInfo(key=timezone)

        local_start = datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            tzinfo=zone,
        )

        next_day: date = value + timedelta(days=1)

        local_end = datetime(
            year=next_day.year,
            month=next_day.month,
            day=next_day.day,
            tzinfo=zone,
        )

        return (
            local_start.astimezone(tz=UTC),
            local_end.astimezone(tz=UTC),
        )

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
