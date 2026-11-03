import random

from mercatura.source.simulation import (
    SimulationContext,
)
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


def generate_supplier_capabilities(
    context: SimulationContext,
    suppliers: tuple[Supplier, ...],
    products: tuple[Product, ...],
) -> tuple[SupplierCapability, ...]:
    departments: tuple[tuple[str, str], ...] = _departments_from_products(products)

    capabilities: list[SupplierCapability] = []

    for supplier in sorted(
        suppliers,
        key=lambda row: row.supplier_code,
    ):
        capabilities.extend(
            _generate_supplier_capabilities(
                context=context,
                supplier=supplier,
                departments=departments,
            )
        )

    return tuple(capabilities)


def _departments_from_products(
    products: tuple[Product, ...],
) -> tuple[tuple[str, str], ...]:
    departments: set[tuple[str, str]] = {
        (
            product.department_code,
            product.department_name,
        )
        for product in products
    }

    return tuple(
        sorted(
            departments,
            key=lambda row: row[0],
        )
    )


def _generate_supplier_capabilities(
    *,
    context: SimulationContext,
    supplier: Supplier,
    departments: tuple[tuple[str, str], ...],
) -> list[SupplierCapability]:
    rng = random.Random(
        x=context.seed_for(namespace=(f"supplier:capability:{supplier.supplier_code}"))
    )

    minimum, maximum = SUPPLIER_TYPE_CAPABILITY_RANGES[supplier.supplier_type]

    maximum: int = min(
        maximum,
        len(departments),
    )

    minimum: int = min(
        minimum,
        maximum,
    )

    capability_count: int = rng.randint(
        minimum,
        maximum,
    )

    selected: list[tuple[str, str]] = rng.sample(
        population=list(departments),
        k=capability_count,
    )

    return [
        SupplierCapability(
            capability_id=(
                context.ids.id_for(
                    namespace="supplier_capability",
                    key=(f"{supplier.supplier_code}:{department_code}"),
                    prefix="cap",
                )
            ),
            supplier_id=(supplier.supplier_id),
            supplier_code=(supplier.supplier_code),
            department_code=(department_code),
            department_name=(department_name),
        )
        for (
            department_code,
            department_name,
        ) in sorted(selected)
    ]
