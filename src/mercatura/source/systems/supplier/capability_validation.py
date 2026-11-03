from collections import defaultdict

from mercatura.source.systems.pim.model import (
    Product,
)
from mercatura.source.systems.supplier.capability_config import (
    SUPPLIER_TYPE_CAPABILITY_RANGES,
)
from mercatura.source.systems.supplier.capability_model import (
    SupplierCapability,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def validate_supplier_capabilities(
    capabilities: tuple[SupplierCapability, ...],
    suppliers: tuple[Supplier, ...],
    products: tuple[Product, ...],
) -> None:
    _validate_unique_ids(capabilities)

    _validate_unique_supplier_department(capabilities)

    _validate_supplier_references(
        capabilities,
        suppliers,
    )

    _validate_department_references(
        capabilities,
        products,
    )

    _validate_supplier_coverage(
        capabilities,
        suppliers,
    )

    _validate_capability_counts(
        capabilities,
        suppliers,
    )


def _validate_unique_ids(
    capabilities: tuple[SupplierCapability, ...],
) -> None:
    identifiers: list[str] = [capability.capability_id for capability in capabilities]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate supplier capability ID")


def _validate_unique_supplier_department(
    capabilities: tuple[SupplierCapability, ...],
) -> None:
    keys: list[tuple[str, str]] = [
        (
            capability.supplier_id,
            capability.department_code,
        )
        for capability in capabilities
    ]

    if len(keys) != len(set(keys)):
        raise ValueError("duplicate supplier-department capability")


def _validate_supplier_references(
    capabilities: tuple[SupplierCapability, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    supplier_by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    for capability in capabilities:
        supplier: Supplier | None = supplier_by_id.get(capability.supplier_id)

        if supplier is None:
            raise ValueError("unknown supplier capability reference")

        if capability.supplier_code != supplier.supplier_code:
            raise ValueError("capability supplier code mismatch")


def _validate_department_references(
    capabilities: tuple[SupplierCapability, ...],
    products: tuple[Product, ...],
) -> None:
    departments: dict[str, str] = {
        product.department_code: product.department_name for product in products
    }

    for capability in capabilities:
        expected_name: str | None = departments.get(capability.department_code)

        if expected_name is None:
            raise ValueError("unknown capability department")

        if capability.department_name != expected_name:
            raise ValueError("capability department name mismatch")


def _validate_supplier_coverage(
    capabilities: tuple[SupplierCapability, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    capable_supplier_ids: set[str] = {capability.supplier_id for capability in capabilities}

    for supplier in suppliers:
        if supplier.supplier_id not in capable_supplier_ids:
            raise ValueError(f"{supplier.supplier_code} has no product capabilities")


def _validate_capability_counts(
    capabilities: tuple[SupplierCapability, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    grouped: dict[str, int] = defaultdict(int)

    for capability in capabilities:
        grouped[capability.supplier_id] += 1

    for supplier in suppliers:
        minimum, maximum = SUPPLIER_TYPE_CAPABILITY_RANGES[supplier.supplier_type]

        count: int = grouped[supplier.supplier_id]

        if not minimum <= count <= maximum:
            raise ValueError(f"{supplier.supplier_code} has invalid capability count")
