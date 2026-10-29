from datetime import date

from mercatura.source.systems.supplier.model import (
    Supplier,
)


def build_supplier(
    *,
    created_at: date,
    inactive_at: date | None = None,
) -> Supplier:
    return Supplier(
        supplier_id="sup_test",
        supplier_code="SUP-GB-0001",
        legal_name="Example Supplier Ltd",
        supplier_type="MANUFACTURER",
        country_code="GB",
        currency="GBP",
        city="London",
        region="Greater London",
        created_at=created_at,
        inactive_at=inactive_at,
    )


def test_supplier_not_active_before_creation() -> None:
    supplier: Supplier = build_supplier(created_at=date(year=2024, month=6, day=1))

    assert not supplier.is_active_on(value=date(year=2024, month=5, day=31))


def test_supplier_active_on_creation_date() -> None:
    supplier: Supplier = build_supplier(created_at=date(year=2024, month=6, day=1))

    assert supplier.is_active_on(value=date(year=2024, month=6, day=1))


def test_supplier_inactive_boundary_is_exclusive() -> None:
    supplier: Supplier = build_supplier(
        created_at=date(year=2024, month=1, day=1),
        inactive_at=date(year=2025, month=1, day=1),
    )

    assert not supplier.is_active_on(value=date(year=2025, month=1, day=1))
