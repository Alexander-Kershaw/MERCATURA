import random
from dataclasses import dataclass
from typing import Self

from mercatura.source.simulation.clock import SimulationClock
from mercatura.source.simulation.config import SimulationConfig
from mercatura.source.simulation.identity import build_simulation_id
from mercatura.source.simulation.ids import DeterministicIdGenerator
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.simulation.rng import RandomStreams


@dataclass(frozen=True, slots=True)
class SimulationContext:
    config: SimulationConfig
    simulation_id: str
    clock: SimulationClock
    random_streams: RandomStreams
    ids: DeterministicIdGenerator

    @classmethod
    def create(
        cls,
        config: SimulationConfig,
    ) -> Self:
        simulation_id: str = build_simulation_id(config)

        return cls(
            config=config,
            simulation_id=simulation_id,
            clock=SimulationClock(
                start_date=config.start_date,
                end_date=config.end_date,
            ),
            random_streams=RandomStreams(
                root_seed=config.seed,
            ),
            ids=DeterministicIdGenerator(
                simulation_id,
            ),
        )

    def market(
        self,
        market_code: str,
    ) -> MarketConfig:
        for market in self.config.markets:
            if market.market_code == market_code:
                return market

        raise KeyError(f"unknown market: {market_code}")

    def rng(
        self,
        namespace: str,
        *,
        market_code: str | None = None,
    ) -> random.Random:
        if market_code is None:
            return self.random_streams.get(namespace)

        self.market(market_code)

        return self.random_streams.get(namespace=f"{namespace}:{market_code}")

    def seed_for(
        self,
        namespace: str,
        *,
        market_code: str | None = None,
    ) -> int:
        if market_code is None:
            return self.random_streams.seed_for(namespace)

        self.market(market_code)

        return self.random_streams.seed_for(namespace=f"{namespace}:{market_code}")
