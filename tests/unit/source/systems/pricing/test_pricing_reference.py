from decimal import Decimal

from mercatura.source.reference.pricing import (
    SUBCATEGORY_PRICE_BANDS,
)
from mercatura.source.reference.product_taxonomy import (
    PRODUCT_TAXONOMY,
)


def test_every_product_subcategory_has_price_band() -> None:
    taxonomy_codes: set[str] = {category.subcategory_code for category in PRODUCT_TAXONOMY}

    pricing_codes = set(SUBCATEGORY_PRICE_BANDS)

    assert taxonomy_codes <= pricing_codes


def test_price_band_minimums_are_positive() -> None:
    for price_band in SUBCATEGORY_PRICE_BANDS.values():
        assert price_band.minimum_gbp > Decimal(value="0")


def test_price_band_maximum_not_below_minimum() -> None:
    for price_band in SUBCATEGORY_PRICE_BANDS.values():
        assert price_band.maximum_gbp >= price_band.minimum_gbp


def test_price_bands_use_decimal() -> None:
    for price_band in SUBCATEGORY_PRICE_BANDS.values():
        assert isinstance(
            price_band.minimum_gbp,
            Decimal,
        )

        assert isinstance(
            price_band.maximum_gbp,
            Decimal,
        )
