from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketOrderConfig:
    market_code: str
    order_count: int

    def __post_init__(self) -> None:
        if not self.market_code.strip():
            raise ValueError("market_code cannot be empty")

        if self.order_count <= 0:
            raise ValueError("order_count must be positive")


DEFAULT_MARKET_ORDER_CONFIGS: tuple[MarketOrderConfig, ...] = (
    MarketOrderConfig(
        market_code="GB",
        order_count=38_000,
    ),
    MarketOrderConfig(
        market_code="DE",
        order_count=23_000,
    ),
    MarketOrderConfig(
        market_code="US",
        order_count=37_000,
    ),
    MarketOrderConfig(
        market_code="CN",
        order_count=27_000,
    ),
    MarketOrderConfig(
        market_code="NO",
        order_count=5_000,
    ),
    MarketOrderConfig(
        market_code="RU",
        order_count=14_000,
    ),
    MarketOrderConfig(
        market_code="JP",
        order_count=19_000,
    ),
    MarketOrderConfig(
        market_code="KR",
        order_count=15_000,
    ),
    MarketOrderConfig(
        market_code="FR",
        order_count=22_000,
    ),
    MarketOrderConfig(
        market_code="NL",
        order_count=10_000,
    ),
    MarketOrderConfig(
        market_code="PL",
        order_count=11_000,
    ),
)


@dataclass(frozen=True, slots=True)
class OMSSimulationConfig:
    market_configs: tuple[MarketOrderConfig, ...] = DEFAULT_MARKET_ORDER_CONFIGS

    store_channel_probability: float = 0.52
    web_channel_probability: float = 0.30
    mobile_channel_probability: float = 0.18

    cancellation_probability: float = 0.035
    maximum_cancellation_delay_days: int = 3

    line_count_probabilities: tuple[float, ...] = (
        0.48,
        0.30,
        0.14,
        0.06,
        0.02,
    )

    item_quantity_probabilities: tuple[float, ...] = (
        0.84,
        0.11,
        0.04,
        0.01,
    )

    customer_propensity_sigma: float = 0.80
    customer_propensity_cap: float = 8.0

    def __post_init__(self) -> None:
        market_codes: list[str] = [config.market_code for config in self.market_configs]

        if len(market_codes) != len(set(market_codes)):
            raise ValueError("OMS market configurations must be unique")

        channel_probabilities: tuple[float, float, float] = (
            self.store_channel_probability,
            self.web_channel_probability,
            self.mobile_channel_probability,
        )

        _validate_probability_distribution(
            probabilities=channel_probabilities,
            name="channel probabilities",
        )

        if not (0.0 <= self.cancellation_probability <= 1.0):
            raise ValueError("cancellation_probability must be between 0 and 1")

        if self.maximum_cancellation_delay_days < 0:
            raise ValueError("maximum_cancellation_delay_days must be non-negative")

        _validate_probability_distribution(
            probabilities=self.line_count_probabilities,
            name="line count probabilities",
        )

        _validate_probability_distribution(
            probabilities=self.item_quantity_probabilities,
            name="item quantity probabilities",
        )

        if self.customer_propensity_sigma < 0.0:
            raise ValueError("customer_propensity_sigma must be non-negative")

        if self.customer_propensity_cap <= 0.0:
            raise ValueError("customer_propensity_cap must be positive")


def _validate_probability_distribution(
    probabilities: tuple[float, ...],
    name: str,
) -> None:
    if not probabilities:
        raise ValueError(f"{name} cannot be empty")

    if any(probability < 0.0 or probability > 1.0 for probability in probabilities):
        raise ValueError(f"{name} must contain values between 0 and 1")

    if abs(sum(probabilities) - 1.0) > 1e-9:
        raise ValueError(f"{name} must sum to 1")


DEFAULT_OMS_CONFIG = OMSSimulationConfig()
