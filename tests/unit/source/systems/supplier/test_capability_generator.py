from datetime import date

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.supplier.capability_config import (
    SUPPLIER_TYPE_CAPABILITY_RANGES,
)
from mercatura.source.systems.supplier.capability_generator import (
    generate_supplier_capabilities,
)
from mercatura.source.systems.supplier.capability_model import SupplierCapability
from mercatura.source.systems.supplier.generator import (
    generate_suppliers,
)
from mercatura.source.systems.supplier.model import Supplier


def build_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )


def normalize(rows) -> list:
    return sorted(
        rows,
        key=lambda row: (
            row.supplier_code,
            row.department_code,
        ),
    )


def test_capability_generation_is_deterministic() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    first: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    second: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    assert first == second


def test_capability_ids_are_unique() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    capabilities: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    identifiers: list[str] = [row.capability_id for row in capabilities]

    assert len(identifiers) == len(set(identifiers))


def test_supplier_department_pairs_are_unique() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    capabilities: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    keys: list[tuple[str, str]] = [
        (
            row.supplier_id,
            row.department_code,
        )
        for row in capabilities
    ]

    assert len(keys) == len(set(keys))


def test_every_supplier_has_capability() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    capabilities: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    capable = {row.supplier_id for row in capabilities}

    assert all(supplier.supplier_id in capable for supplier in suppliers)


def test_capability_counts_match_supplier_type() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    capabilities: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    for supplier in suppliers:
        count = sum(row.supplier_id == supplier.supplier_id for row in capabilities)

        minimum, maximum = SUPPLIER_TYPE_CAPABILITY_RANGES[supplier.supplier_type]

        assert minimum <= count <= maximum


def test_all_departments_have_capable_suppliers() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    capabilities: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    departments: set[str] = {product.department_code for product in products}

    capable_departments: set[str] = {capability.department_code for capability in capabilities}

    assert departments <= capable_departments


def test_supplier_input_order_does_not_change_capabilities() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    first: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    second: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        tuple(reversed(suppliers)),
        products,
    )

    assert normalize(rows=first) == normalize(rows=second)


def test_product_input_order_does_not_change_capabilities() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)
    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    first: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    second: tuple[SupplierCapability, ...] = generate_supplier_capabilities(
        context,
        suppliers,
        tuple(reversed(products)),
    )

    assert normalize(rows=first) == normalize(rows=second)
