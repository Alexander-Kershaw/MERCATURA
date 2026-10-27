from datetime import date

from mercatura.source.systems.pim.model import Product


def build_product(
    *,
    created_at: date,
    discontinued_at: date | None = None,
) -> Product:
    return Product(
        product_id="prd_test",
        sku="MRC-000001",
        product_name="Test Product",
        brand_name="Test Brand",
        model_name="Test Model",
        department_code="TEST",
        department_name="Test",
        category_code="TEST",
        category_name="Test",
        subcategory_code="TEST",
        subcategory_name="Test",
        colour=None,
        material=None,
        description="TEST",
        unit_of_measure="EACH",
        created_at=created_at,
        discontinued_at=discontinued_at,
    )


def test_product_is_not_active_before_creation() -> None:
    product: Product = build_product(created_at=date(year=2024, month=6, day=1))

    assert not product.is_active_on(value=date(year=2024, month=5, day=31))


def test_product_is_active_after_creation() -> None:
    product: Product = build_product(created_at=date(year=2024, month=6, day=1))

    assert product.is_active_on(value=date(year=2024, month=6, day=1))


def test_product_is_not_active_on_discontinuation_date() -> None:
    product: Product = build_product(
        created_at=date(year=2024, month=1, day=1),
        discontinued_at=date(year=2025, month=1, day=1),
    )

    assert not product.is_active_on(value=date(year=2025, month=1, day=1))
