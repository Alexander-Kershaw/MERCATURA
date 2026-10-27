from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MarketPricingConfig:
    market_code: str

    local_currency_scale: Decimal
    market_price_index: Decimal

    minor_unit: Decimal

    def __post_init__(self) -> None:
        if self.local_currency_scale <= 0:
            raise ValueError("local_currency_scale must be positive")

        if self.market_price_index <= 0:
            raise ValueError("market_price_index must be positive")

        if self.minor_unit <= 0:
            raise ValueError("minor_unit must be positive")


DEFAULT_MARKET_PRICING: tuple[MarketPricingConfig, ...] = (
    MarketPricingConfig(
        market_code="GB",
        local_currency_scale=Decimal(value="1.00"),
        market_price_index=Decimal(value="1.00"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="DE",
        local_currency_scale=Decimal(value="1.18"),
        market_price_index=Decimal(value="1.02"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="US",
        local_currency_scale=Decimal(value="1.28"),
        market_price_index=Decimal(value="1.05"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="CN",
        local_currency_scale=Decimal(value="9.20"),
        market_price_index=Decimal(value="0.88"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="NO",
        local_currency_scale=Decimal(value="13.60"),
        market_price_index=Decimal(value="1.15"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="RU",
        local_currency_scale=Decimal(value="118"),
        market_price_index=Decimal(value="0.90"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="JP",
        local_currency_scale=Decimal(value="195"),
        market_price_index=Decimal(value="1.00"),
        minor_unit=Decimal(value="1"),
    ),
    MarketPricingConfig(
        market_code="KR",
        local_currency_scale=Decimal(value="1750"),
        market_price_index=Decimal(value="0.98"),
        minor_unit=Decimal(value="1"),
    ),
    MarketPricingConfig(
        market_code="FR",
        local_currency_scale=Decimal(value="1.18"),
        market_price_index=Decimal(value="1.04"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="NL",
        local_currency_scale=Decimal(value="1.18"),
        market_price_index=Decimal(value="1.06"),
        minor_unit=Decimal(value="0.01"),
    ),
    MarketPricingConfig(
        market_code="PL",
        local_currency_scale=Decimal(value="5.10"),
        market_price_index=Decimal(value="0.82"),
        minor_unit=Decimal(value="0.01"),
    ),
)


@dataclass(frozen=True, slots=True)
class PricingSimulationConfig:
    maximum_changes: int = 3

    first_change_probability: float = 0.55
    second_change_probability: float = 0.30
    third_change_probability: float = 0.15

    minimum_change_percent: Decimal = Decimal(value="0.03")
    maximum_change_percent: Decimal = Decimal(value="0.15")

    minimum_days_before_change: int = 30

    def __post_init__(self) -> None:
        if not 0 <= self.maximum_changes <= 3:
            raise ValueError("maximum_changes must be between 0 and 3")

        probabilities: tuple[float, float, float] = (
            self.first_change_probability,
            self.second_change_probability,
            self.third_change_probability,
        )

        if any(probability < 0.0 or probability > 1.0 for probability in probabilities):
            raise ValueError("change probabilities must be between 0 and 1")

        if self.minimum_change_percent <= Decimal(value="0"):
            raise ValueError("minimum_change_percent must be positive")

        if self.maximum_change_percent <= Decimal("0"):
            raise ValueError("maximum_change_percent must be positive")

        if self.minimum_change_percent > self.maximum_change_percent:
            raise ValueError("minimum_change_percent must not exceed maximum_change_percent")

        if self.minimum_days_before_change < 0:
            raise ValueError("minimum_days_before_change must be non-negative")

        if not (
            self.first_change_probability
            >= self.second_change_probability
            >= self.third_change_probability
        ):
            raise ValueError("change probabilities must be non-increasing")


DEFAULT_PRICING_CONFIG = PricingSimulationConfig()
