from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketStoreConfig:
    """
    ================================================================================================

    MARKET-STORE CONFIGURATION

    ================================================================================================

    Contains market code, store count, and format of store (FLAGSHIP, STANDARD, EXPRESS, OUTLET)

    requires that stores to exist and have a store format.

    ================================================================================================
    """

    market_code: str
    store_count: int
    formats: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.store_count < 0:
            raise ValueError("store_count must be non-negative")

        if not self.formats:
            raise ValueError("at least one store format is required")


"""
========================================================================================

STORES

========================================================================================

Using a total of 66 physical stores:

- 12 in Great Britain
- 7 in Germany
- 8 in the United States
- 6 in China
- 3 in Norway
- 4 in Russia
- 6 in Japan
- 5 in Korea
- 6 in France
- 4 in Netherlands
- 5 in Poland

========================================================================================
"""

DEFAULT_STORE_CONFIG: tuple[MarketStoreConfig, ...] = (
    MarketStoreConfig(
        market_code="GB",
        store_count=12,
        formats=("FLAGSHIP", "STANDARD", "EXPRESS"),
    ),
    MarketStoreConfig(
        market_code="DE",
        store_count=7,
        formats=("FLAGSHIP", "STANDARD"),
    ),
    MarketStoreConfig(
        market_code="US",
        store_count=8,
        formats=("FLAGSHIP", "STANDARD", "OUTLET"),
    ),
    MarketStoreConfig(
        market_code="CN",
        store_count=6,
        formats=("FLAGSHIP", "STANDARD"),
    ),
    MarketStoreConfig(
        market_code="NO",
        store_count=3,
        formats=("STANDARD", "EXPRESS"),
    ),
    MarketStoreConfig(
        market_code="RU",
        store_count=4,
        formats=("FLAGSHIP", "STANDARD"),
    ),
    MarketStoreConfig(
        market_code="JP",
        store_count=6,
        formats=("FLAGSHIP", "STANDARD", "EXPRESS"),
    ),
    MarketStoreConfig(
        market_code="KR",
        store_count=5,
        formats=("FLAGSHIP", "STANDARD"),
    ),
    MarketStoreConfig(
        market_code="FR",
        store_count=6,
        formats=("FLAGSHIP", "STANDARD", "EXPRESS"),
    ),
    MarketStoreConfig(
        market_code="NL",
        store_count=4,
        formats=("STANDARD", "EXPRESS"),
    ),
    MarketStoreConfig(
        market_code="PL",
        store_count=5,
        formats=("FLAGSHIP", "STANDARD"),
    ),
)
