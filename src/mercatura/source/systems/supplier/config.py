from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketSupplierConfig:
    market_code: str
    supplier_count: int

    def __post_init__(self) -> None:
        if self.supplier_count < 0:
            raise ValueError("supplier_count must be non-negative")


@dataclass(frozen=True, slots=True)
class SupplierSimulationConfig:
    """
    ====================================================================================

    SUPPLIER CONFIG

    ====================================================================================

    Each market supplier has a market_code and a supplier count:

    - market_code: the regional market code used to identify a market e.g GB, CN,...
    - supplier_count: the number of suppliers for that market

    ------------------------------------------------------------------------------------

    Overall config:

    - Suppliers has 12 years of history
    - suppliers have an onboarding rate of 12 percent
    - suppliers have a deacivation rate of 8 percent
    - suppliers have a minimum of 180 days of activity

    ------------------------------------------------------------------------------------

    Constraints:

    - history years must be positive
    - onboading and deactivation rates are bounded between 0 and 1
    - must have a positive number of active days

    ------------------------------------------------------------------------------------

    DEFAULT_MARKET_SUPPLIERS accounts fo 72 suppliers over 11 market codes.

    ====================================================================================
    """

    history_years: int = 12
    onboard_during_simulation_rate: float = 0.12
    deactivate_rate: float = 0.08
    minimum_active_days: int = 180

    def __post_init__(self) -> None:
        if self.history_years < 0:
            raise ValueError("history_years must be non-negative")

        for name, value in (
            (
                "onboard_during_simulation_rate",
                self.onboard_during_simulation_rate,
            ),
            (
                "deactivate_rate",
                self.deactivate_rate,
            ),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        if self.minimum_active_days < 0:
            raise ValueError("minimum_active_days must be non-negative")


DEFAULT_MARKET_SUPPLIERS: tuple[MarketSupplierConfig, ...] = (
    MarketSupplierConfig(market_code="GB", supplier_count=10),
    MarketSupplierConfig(market_code="DE", supplier_count=8),
    MarketSupplierConfig(market_code="US", supplier_count=8),
    MarketSupplierConfig(market_code="CN", supplier_count=10),
    MarketSupplierConfig(market_code="NO", supplier_count=3),
    MarketSupplierConfig(market_code="RU", supplier_count=4),
    MarketSupplierConfig(market_code="JP", supplier_count=6),
    MarketSupplierConfig(market_code="KR", supplier_count=5),
    MarketSupplierConfig(market_code="FR", supplier_count=7),
    MarketSupplierConfig(market_code="NL", supplier_count=5),
    MarketSupplierConfig(market_code="PL", supplier_count=6),
)


DEFAULT_SUPPLIER_CONFIG = SupplierSimulationConfig()

# Suppliers can be of these types
SUPPLIER_TYPES: tuple[str, ...] = (
    "MANUFACTURER",
    "DISTRIBUTOR",
    "WHOLESALER",
    "IMPORTER",
)
