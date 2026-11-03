from dataclasses import replace
from datetime import date

import pytest

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.supplier.capability_generator import (
    generate_supplier_capabilities,
)
from mercatura.source.systems.supplier.capability_model import SupplierCapability
from mercatura.source.systems.supplier.capability_validation import (
    validate_supplier_capabilities,
)
from mercatura.source.systems.supplier.generator import (
    generate_suppliers,
)
from mercatura.source.systems.supplier.model import Supplier


def build_dataset() -> tuple[
    tuple[Product, ...], tuple[Supplier, ...], tuple[SupplierCapability, ...]
]:
    context: SimulationContext = SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    capabilities: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    return (
        products,
        suppliers,
        capabilities,
    )


def test_valid_capabilities_pass_validation() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    validate_supplier_capabilities(
        capabilities,
        suppliers,
        products,
    )


def test_rejects_duplicate_capability_id() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    broken = (
        *capabilities,
        capabilities[0],
    )

    with pytest.raises(expected_exception=ValueError):
        validate_supplier_capabilities(
            broken,
            suppliers,
            products,
        )


def test_rejects_duplicate_supplier_department() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    duplicate: SupplierCapability = replace(
        capabilities[0],
        capability_id="cap_duplicate",
    )

    broken = (
        *capabilities,
        duplicate,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_supplier_capabilities(
            broken,
            suppliers,
            products,
        )


def test_rejects_unknown_supplier() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    broken_row: SupplierCapability = replace(
        capabilities[0],
        supplier_id="sup_missing",
    )

    broken = (
        broken_row,
        *capabilities[1:],
    )

    with pytest.raises(expected_exception=ValueError):
        validate_supplier_capabilities(
            broken,
            suppliers,
            products,
        )


def test_rejects_supplier_code_mismatch() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    broken_row: SupplierCapability = replace(
        capabilities[0],
        supplier_code="SUP-WRONG",
    )

    broken = (
        broken_row,
        *capabilities[1:],
    )

    with pytest.raises(expected_exception=ValueError):
        validate_supplier_capabilities(
            broken,
            suppliers,
            products,
        )


def test_rejects_unknown_department() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    broken_row: SupplierCapability = replace(
        capabilities[0],
        department_code="UNKNOWN",
    )

    broken = (
        broken_row,
        *capabilities[1:],
    )

    with pytest.raises(expected_exception=ValueError):
        validate_supplier_capabilities(
            broken,
            suppliers,
            products,
        )


def test_rejects_department_name_mismatch() -> None:
    (
        products,
        suppliers,
        capabilities,
    ) = build_dataset()

    broken_row: SupplierCapability = replace(
        capabilities[0],
        department_name="Wrong",
    )

    broken = (
        broken_row,
        *capabilities[1:],
    )

    with pytest.raises(expected_exception=ValueError):
        validate_supplier_capabilities(
            broken,
            suppliers,
            products,
        )
