from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketLoyaltyConfig:
    market_code: str
    enrolment_probability: float

    def __post_init__(self) -> None:
        if not self.market_code.strip():
            raise ValueError("market_code cannot be empty")

        if not (0.0 <= self.enrolment_probability <= 1.0):
            raise ValueError("enrolment_probability must be between 0 and 1")


DEFAULT_MARKET_LOYALTY_CONFIGS: tuple[MarketLoyaltyConfig, ...] = (
    MarketLoyaltyConfig(
        market_code="GB",
        enrolment_probability=0.46,
    ),
    MarketLoyaltyConfig(
        market_code="DE",
        enrolment_probability=0.42,
    ),
    MarketLoyaltyConfig(
        market_code="US",
        enrolment_probability=0.41,
    ),
    MarketLoyaltyConfig(
        market_code="CN",
        enrolment_probability=0.36,
    ),
    MarketLoyaltyConfig(
        market_code="NO",
        enrolment_probability=0.48,
    ),
    MarketLoyaltyConfig(
        market_code="RU",
        enrolment_probability=0.32,
    ),
    MarketLoyaltyConfig(
        market_code="JP",
        enrolment_probability=0.44,
    ),
    MarketLoyaltyConfig(
        market_code="KR",
        enrolment_probability=0.47,
    ),
    MarketLoyaltyConfig(
        market_code="FR",
        enrolment_probability=0.43,
    ),
    MarketLoyaltyConfig(
        market_code="NL",
        enrolment_probability=0.45,
    ),
    MarketLoyaltyConfig(
        market_code="PL",
        enrolment_probability=0.37,
    ),
)


@dataclass(frozen=True, slots=True)
class LoyaltySimulationConfig:
    market_configs: tuple[MarketLoyaltyConfig, ...] = DEFAULT_MARKET_LOYALTY_CONFIGS

    maximum_enrolment_lag_days: int = 365 * 10

    minimum_membership_days_before_closure: int = 30
    standard_tier_probability: float = 0.72
    silver_tier_probability: float = 0.18
    gold_tier_probability: float = 0.08
    platinum_tier_probability: float = 0.02

    def __post_init__(self) -> None:
        if self.maximum_enrolment_lag_days <= 0:
            raise ValueError("maximum_enrolment_lag_days must be positive")

        if self.minimum_membership_days_before_closure <= 0:
            raise ValueError("minimum_membership_days_before_closure must be positive")

        market_codes: list[str] = [market.market_code for market in self.market_configs]

        if len(market_codes) != len(set(market_codes)):
            raise ValueError("loyalty market configurations must be unique")

        tier_probabilities: tuple[float, float, float, float] = (
            self.standard_tier_probability,
            self.silver_tier_probability,
            self.gold_tier_probability,
            self.platinum_tier_probability,
        )

        if any(probability < 0.0 or probability > 1.0 for probability in tier_probabilities):
            raise ValueError("tier probabilities must be between 0 and 1")

        if abs(sum(tier_probabilities) - 1.0) > 1e-9:
            raise ValueError("tier probabilities must sum to 1")


DEFAULT_LOYALTY_CONFIG = LoyaltySimulationConfig()
