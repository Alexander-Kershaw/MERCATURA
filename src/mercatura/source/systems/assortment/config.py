from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketAssortmentConfig:
    market_code: str
    coverage_rate: float
    max_launch_lag_days: int = 60
    private_label_boost: float = 0.05

    def __post_init__(self) -> None:
        if not 0.0 <= self.coverage_rate <= 1.0:
            raise ValueError("coverage_rate must be between 0 and 1")

        if self.max_launch_lag_days < 0:
            raise ValueError("max_launch_lag_days must be non-negative")

        if not 0.0 <= self.private_label_boost <= 1.0:
            raise ValueError("private_label_boost must be between 0 and 1")


DEFAULT_ASSORTMENT_CONFIG: tuple[MarketAssortmentConfig, ...] = (
    MarketAssortmentConfig(market_code="GB", coverage_rate=0.95),
    MarketAssortmentConfig(market_code="DE", coverage_rate=0.88),
    MarketAssortmentConfig(market_code="US", coverage_rate=0.90),
    MarketAssortmentConfig(market_code="CN", coverage_rate=0.75),
    MarketAssortmentConfig(market_code="NO", coverage_rate=0.70),
    MarketAssortmentConfig(market_code="RU", coverage_rate=0.65),
    MarketAssortmentConfig(market_code="JP", coverage_rate=0.78),
    MarketAssortmentConfig(market_code="KR", coverage_rate=0.76),
    MarketAssortmentConfig(market_code="FR", coverage_rate=0.86),
    MarketAssortmentConfig(market_code="NL", coverage_rate=0.80),
    MarketAssortmentConfig(market_code="PL", coverage_rate=0.74),
)
