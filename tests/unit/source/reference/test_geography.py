from zoneinfo import ZoneInfo

import pytest

from mercatura.source.reference.geography import (
    STORE_LOCATIONS,
    StoreLocation,
    locations_for_market,
)
from mercatura.source.systems.store.config import (
    DEFAULT_STORE_CONFIG,
)


def test_every_store_market_has_geography() -> None:
    for config in DEFAULT_STORE_CONFIG:
        assert config.market_code in STORE_LOCATIONS


def test_every_market_has_enough_locations() -> None:
    for config in DEFAULT_STORE_CONFIG:
        locations: tuple[StoreLocation, ...] = locations_for_market(market_code=config.market_code)

        assert len(locations) >= config.store_count


def test_location_market_matches_dictionary_key() -> None:
    for market_code, locations in STORE_LOCATIONS.items():
        for location in locations:
            assert location.market_code == market_code


def test_location_codes_are_unique_within_market() -> None:
    for locations in STORE_LOCATIONS.values():
        codes: list[str] = [location.location_code for location in locations]

        assert len(codes) == len(set(codes))


def test_all_location_timezones_are_valid() -> None:
    for locations in STORE_LOCATIONS.values():
        for location in locations:
            ZoneInfo(key=location.timezone)


def test_unknown_market_is_rejected() -> None:
    with pytest.raises(
        expected_exception=KeyError,
        match="no store geography configured",
    ):
        locations_for_market(market_code="ZZ")
