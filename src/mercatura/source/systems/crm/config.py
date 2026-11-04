from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerPopulation:
    market_code: str
    customer_count: int

    def __post_init__(self) -> None:
        if not self.market_code.strip():
            raise ValueError("market_code cannot be empty")

        if self.customer_count <= 0:
            raise ValueError("customer_count must be positive")


DEFAULT_CUSTOMER_POPULATIONS: tuple[CustomerPopulation, ...] = (
    CustomerPopulation(
        market_code="GB",
        customer_count=8_500,
    ),
    CustomerPopulation(
        market_code="DE",
        customer_count=5_200,
    ),
    CustomerPopulation(
        market_code="US",
        customer_count=8_200,
    ),
    CustomerPopulation(
        market_code="CN",
        customer_count=6_000,
    ),
    CustomerPopulation(
        market_code="NO",
        customer_count=1_200,
    ),
    CustomerPopulation(
        market_code="RU",
        customer_count=3_200,
    ),
    CustomerPopulation(
        market_code="JP",
        customer_count=4_300,
    ),
    CustomerPopulation(
        market_code="KR",
        customer_count=3_400,
    ),
    CustomerPopulation(
        market_code="FR",
        customer_count=5_000,
    ),
    CustomerPopulation(
        market_code="NL",
        customer_count=2_400,
    ),
    CustomerPopulation(
        market_code="PL",
        customer_count=2_700,
    ),
)


@dataclass(frozen=True, slots=True)
class CustomerSimulationConfig:
    populations: tuple[CustomerPopulation, ...] = DEFAULT_CUSTOMER_POPULATIONS

    history_years: int = 10
    created_during_simulation_share: float = 0.45
    deactivation_probability: float = 0.05
    missing_email_probability: float = 0.015
    missing_phone_probability: float = 0.08
    minimum_active_days: int = 30

    def __post_init__(self) -> None:
        if self.history_years <= 0:
            raise ValueError("history_years must be positive")

        if self.minimum_active_days <= 0:
            raise ValueError("minimum_active_days must be positive")

        probabilities: tuple[float, float, float, float] = (
            self.created_during_simulation_share,
            self.deactivation_probability,
            self.missing_email_probability,
            self.missing_phone_probability,
        )

        if any(probability < 0.0 or probability > 1.0 for probability in probabilities):
            raise ValueError("customer probabilities must be between 0 and 1")

        market_codes: list[str] = [population.market_code for population in self.populations]

        if len(market_codes) != len(set(market_codes)):
            raise ValueError("customer population markets must be unique")


DEFAULT_CUSTOMER_CONFIG = CustomerSimulationConfig()
