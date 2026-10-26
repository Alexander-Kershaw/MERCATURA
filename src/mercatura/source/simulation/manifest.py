from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Self

from mercatura.source.simulation.config import SimulationConfig
from mercatura.source.simulation.context import SimulationContext


@dataclass(frozen=True, slots=True)
class SimulationManifest:
    simulation_id: str
    generator_version: str
    seed: int
    start_date: str
    end_date: str
    reporting_currency: str
    markets: tuple[str, ...]
    scenarios: tuple[str, ...]
    defects: tuple[str, ...]
    created_at_utc: str

    @classmethod
    def from_context(
        cls,
        context: SimulationContext,
        *,
        created_at: datetime | None = None,
    ) -> Self:
        timestamp: datetime = created_at or datetime.now(tz=UTC)

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        config: SimulationConfig = context.config

        return cls(
            simulation_id=context.simulation_id,
            generator_version=config.generator_version,
            seed=config.seed,
            start_date=config.start_date.isoformat(),
            end_date=config.end_date.isoformat(),
            reporting_currency=config.reporting_currency,
            markets=tuple(sorted(market.market_code for market in config.markets)),
            scenarios=tuple(sorted(config.scenarios)),
            defects=tuple(sorted(config.defects)),
            created_at_utc=timestamp.astimezone(UTC).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(obj=self)
