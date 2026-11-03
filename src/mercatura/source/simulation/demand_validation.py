from decimal import Decimal

from mercatura.source.simulation.demand import (
    DEPARTMENT_DEMAND_BANDS,
    MARKET_DEMAND_FACTORS,
    DemandProfile,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.model import (
    Product,
)


def validate_demand_profiles(
    profiles: tuple[DemandProfile, ...],
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    _validate_assortment_coverage(
        profiles,
        assortments,
    )

    _validate_metadata(
        profiles,
        products,
        assortments,
    )

    _validate_values(
        profiles,
    )


def _validate_assortment_coverage(
    profiles: tuple[DemandProfile, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    profile_ids: list[str] = [profile.assortment_id for profile in profiles]

    if len(profile_ids) != len(set(profile_ids)):
        raise ValueError("duplicate demand profile")

    expected: set[str] = {assortment.assortment_id for assortment in assortments}

    if set(profile_ids) != expected:
        raise ValueError("demand profiles do not cover all assortments")


def _validate_metadata(
    profiles: tuple[DemandProfile, ...],
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    products_by_id: dict[str, Product] = {product.product_id: product for product in products}

    assortments_by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    for profile in profiles:
        assortment: ProductMarketAssortment = assortments_by_id[profile.assortment_id]

        product: Product = products_by_id[assortment.product_id]

        if profile.product_id != product.product_id:
            raise ValueError("demand product mismatch")

        if profile.sku != product.sku:
            raise ValueError("demand SKU mismatch")

        if profile.market_code != assortment.market_code:
            raise ValueError("demand market mismatch")

        if profile.department_code != product.department_code:
            raise ValueError("demand department mismatch")


def _validate_values(
    profiles: tuple[DemandProfile, ...],
) -> None:
    for profile in profiles:
        if profile.department_code not in DEPARTMENT_DEMAND_BANDS:
            raise ValueError("unknown demand department")

        if profile.market_code not in MARKET_DEMAND_FACTORS:
            raise ValueError("unknown demand market")

        if profile.average_daily_units <= Decimal(value="0"):
            raise ValueError("average daily demand must be positive")

        if not (Decimal(value="0") <= profile.volatility <= Decimal(value="1")):
            raise ValueError("invalid demand volatility")

        if not (Decimal(value="0") <= profile.seasonality_strength <= Decimal(value="1")):
            raise ValueError("invalid seasonality strength")
