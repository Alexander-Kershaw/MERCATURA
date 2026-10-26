from dataclasses import dataclass
from datetime import date

from mercatura.source.simulation.market import DEFAULT_MARKETS, MarketConfig


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """
    ================================================================================================

    SIMULATION CONFIGURATION

    ================================================================================================

    SimulationConfig is a dataclass that encapsulates the configuration parameters for a simulation.
    it is frozen and uses slots for memory efficiency. This stops any mutation or modification of
    the simulation configuration attributes after instantiation, therefore ensuring the integrity
    of the simulation config throughout its lifecycle.

    slots are used to optimize memory usage and improve attribute access speed, which is
    particularly beneficial when dealing with a large number of simulation configurations
    or when performance is critical. Also prevents any arbitary attributes from being added
    to class instances further preventing accidential mutation.

    The class includes attributes for the start and end dates of the simulation, a random seed
    for reproducibility, the version of the generator used, and tuples for scenarios and defects
    to be included in the simulation.

    -----------------------------------------------------------------------------------------------

    Attributes:
        start_date (date): The start date of the simulation.
        end_date (date): The end date of the simulation.
        seed (int): The random seed for reproducibility. Default is 777.
        generator_version (str): The version of the generator used. Default is "0.1.0".
        scenarios (tuple[str, ...]): A tuple of scenario names to be included in the simulation.
        defects (tuple[str, ...]): A tuple of defect names to be included in the simulation.

    -----------------------------------------------------------------------------------------------

    Raises:
        ValueError: If start_date is after end_date.
        ValueError: If seed is a negative integer.
        ValueError: If generator_version is an empty string.

    -----------------------------------------------------------------------------------------------

    properties:
        day_count (int): The total number of days in the simulation,
        inclusive of start and end dates.

    -----------------------------------------------------------------------------------------------

    Methods:
        canonical_payload() -> dict[str, object]: Returns a dictionary
        representation of the simulation configuration.

        This is used for simulation identity and manifests.

    ================================================================================================
    """

    start_date: date
    end_date: date
    seed: int = 777
    generator_version: str = "0.1.0"
    scenarios: tuple[str, ...] = ()
    defects: tuple[str, ...] = ()
    reporting_currency: str = "GBP"
    markets: tuple[MarketConfig, ...] = DEFAULT_MARKETS

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")

        if self.seed < 0:
            raise ValueError("seed must be a non-negative integer")

        if not self.generator_version.strip():
            raise ValueError("generator_version must not be empty")

        if len(self.reporting_currency) != 3 or not self.reporting_currency.isupper():
            raise ValueError("reporting_currency must be a three-character uppercase currency code")

        if not self.markets:
            raise ValueError("at least one market must be configured")

        market_codes: list[str] = [market.market_code for market in self.markets]

        if len(market_codes) != len(set(market_codes)):
            raise ValueError("market_code values must be unique")

        legal_entities: list[str] = [market.legal_entity for market in self.markets]

        if len(legal_entities) != len(set(legal_entities)):
            raise ValueError("legal_entity values must be unique")

    @property
    def day_count(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def canonical_payload(self) -> dict[str, object]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "seed": self.seed,
            "generator_version": self.generator_version,
            "scenarios": sorted(self.scenarios),
            "defects": sorted(self.defects),
            "markets": [
                market.canonical_payload()
                for market in sorted(self.markets, key=lambda item: item.market_code)
            ],
            "reporting_currency": self.reporting_currency,
        }
