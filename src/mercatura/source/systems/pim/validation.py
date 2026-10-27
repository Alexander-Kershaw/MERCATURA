from mercatura.source.reference.product_taxonomy import (
    PRODUCT_TAXONOMY,
)
from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.pim.model import Product


def validate_products(
    products: tuple[Product, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_ids(products)
    _validate_unique_skus(products)
    _validate_taxonomy(products)
    _validate_lifecycles(
        products,
        context,
    )
    _validate_required_text(products)


def _validate_unique_ids(
    products: tuple[Product, ...],
) -> None:
    ids: list[str] = [product.product_id for product in products]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate product_id detected")


def _validate_unique_skus(
    products: tuple[Product, ...],
) -> None:
    skus: list[str] = [product.sku for product in products]

    if len(skus) != len(set(skus)):
        raise ValueError("duplicate SKU detected")


def _validate_lifecycles(
    products: tuple[Product, ...],
    context: SimulationContext,
) -> None:
    for product in products:
        if product.created_at > context.config.end_date:
            raise ValueError(f"product {product.sku} created after simulation period")

        if product.discontinued_at is not None and product.discontinued_at <= product.created_at:
            raise ValueError(f"product {product.sku} discontinued before creation")

        if (
            product.discontinued_at is not None
            and product.discontinued_at > context.config.end_date
        ):
            raise ValueError(f"product {product.sku} discontinued after simulation period")


def _validate_taxonomy(
    products: tuple[Product, ...],
) -> None:
    valid_paths: set[tuple[str, str, str]] = {
        (
            category.department_code,
            category.category_code,
            category.subcategory_code,
        )
        for category in PRODUCT_TAXONOMY
    }

    for product in products:
        path: tuple[str, str, str] = (
            product.department_code,
            product.category_code,
            product.subcategory_code,
        )

        if path not in valid_paths:
            raise ValueError(f"invalid taxonomy path for product {product.sku}: {path}")


def _validate_required_text(
    products: tuple[Product, ...],
) -> None:
    for product in products:
        required: tuple[str, str, str, str] = (
            product.product_name,
            product.brand_name,
            product.model_name,
            product.description,
        )

        if any(not value.strip() for value in required):
            raise ValueError(f"empty required PIM field for product {product.sku}")
