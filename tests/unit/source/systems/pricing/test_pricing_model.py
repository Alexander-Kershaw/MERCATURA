from datetime import date
from decimal import Decimal

from mercatura.source.systems.pricing.model import ProductPrice


def build_price(
    *,
    effective_from: date = date(year=2024, month=1, day=1),
    effective_to: date | None = date(year=2025, month=1, day=1),
) -> ProductPrice:
    return ProductPrice(
        price_id="prc_test",
        assortment_id="ast_test",
        product_id="prd_test",
        sku="MRC-000001",
        market_code="GB",
        currency="GBP",
        list_price=Decimal(value="29.99"),
        effective_from=effective_from,
        effective_to=effective_to,
        version=1,
    )


def test_price_not_effective_before_start() -> None:
    price: ProductPrice = build_price()

    assert not price.is_effective_on(value=date(year=2023, month=12, day=31))


def test_effective_from_is_inclusive() -> None:
    price: ProductPrice = build_price()

    assert price.is_effective_on(value=date(year=2024, month=1, day=1))


def test_price_effective_inside_interval() -> None:
    price: ProductPrice = build_price()

    assert price.is_effective_on(value=date(year=2024, month=6, day=1))


def test_effective_to_is_exclusive() -> None:
    price: ProductPrice = build_price()

    assert not price.is_effective_on(value=date(year=2025, month=1, day=1))


def test_open_ended_price_remains_effective() -> None:
    price: ProductPrice = build_price(effective_to=None)

    assert price.is_effective_on(value=date(year=2030, month=1, day=1))
