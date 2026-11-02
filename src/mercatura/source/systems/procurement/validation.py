from collections import defaultdict
from decimal import Decimal

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.procurement.config import SOURCING_ROLES
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def validate_sourcing_agreements(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_ids(agreements)

    _validate_references(
        agreements,
        assortments,
        suppliers,
    )

    _validate_roles(
        agreements,
        assortments,
    )

    _validate_costs(
        agreements,
        prices,
    )

    _validate_logistics(agreements)

    _validate_intervals(agreements)

    _validate_lifecycles(
        agreements,
        assortments,
        suppliers,
    )

    _validate_currencies(
        agreements,
        context,
    )


def _validate_unique_ids(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    identifiers: list[str] = [agreement.sourcing_id for agreement in agreements]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate sourcing_id detected")


def _validate_references(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    assortment_by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    supplier_by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    for agreement in agreements:
        assortment: ProductMarketAssortment | None = assortment_by_id.get(agreement.assortment_id)

        if assortment is None:
            raise ValueError("unknown sourcing assortment")

        supplier: Supplier | None = supplier_by_id.get(agreement.supplier_id)

        if supplier is None:
            raise ValueError("unknown sourcing supplier")

        if agreement.product_id != assortment.product_id:
            raise ValueError("sourcing product does not match assortment")

        if agreement.market_code != assortment.market_code:
            raise ValueError("sourcing market does not match assortment")

        if agreement.supplier_code != supplier.supplier_code:
            raise ValueError("supplier code does not match supplier")

        if agreement.sku != assortment.sku:
            raise ValueError("sourcing SKU does not match assortment")


def _validate_roles(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    grouped: dict[
        str,
        list[SourcingAgreement],
    ] = defaultdict(list)

    for agreement in agreements:
        grouped[agreement.assortment_id].append(agreement)

    valid_roles: set[str] = set(SOURCING_ROLES)

    for agreement in agreements:
        if agreement.sourcing_role not in valid_roles:
            raise ValueError(f"invalid sourcing role: {agreement.sourcing_role}")

    for assortment in assortments:
        sourcing: list[SourcingAgreement] = grouped[assortment.assortment_id]

        if not sourcing:
            raise ValueError(f"no sourcing for {assortment.assortment_id}")

        roles: list[str] = [agreement.sourcing_role for agreement in sourcing]

        if roles.count("PRIMARY") != 1:
            raise ValueError("every assortment requires exactly one PRIMARY supplier")

        if len(roles) != len(set(roles)):
            raise ValueError("duplicate sourcing role")

        supplier_ids = [agreement.supplier_id for agreement in sourcing]

        if len(supplier_ids) != len(set(supplier_ids)):
            raise ValueError("same supplier assigned multiple sourcing roles")


def _validate_intervals(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    for agreement in agreements:
        if (
            agreement.effective_to is not None
            and agreement.effective_to <= agreement.effective_from
        ):
            raise ValueError("sourcing agreement has invalid effective interval")


def _validate_costs(
    agreements: tuple[SourcingAgreement, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    initial_prices: dict[str, ProductPrice] = {
        price.assortment_id: price for price in prices if price.version == 1
    }

    for agreement in agreements:
        if not isinstance(
            agreement.unit_cost,
            Decimal,
        ):
            raise ValueError("unit cost must use Decimal")

        if agreement.unit_cost <= Decimal(value="0"):
            raise ValueError("unit cost must be positive")

        retail_price: ProductPrice = initial_prices[agreement.assortment_id]

        if agreement.unit_cost >= retail_price.list_price:
            raise ValueError("unit cost must be below initial list price")


def _validate_logistics(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    for agreement in agreements:
        if agreement.minimum_order_quantity <= 0:
            raise ValueError("MOQ must be positive")

        if agreement.lead_time_days <= 0:
            raise ValueError("lead time must be positive")


def _validate_lifecycles(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    assortment_by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    supplier_by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    for agreement in agreements:
        assortment: ProductMarketAssortment = assortment_by_id[agreement.assortment_id]

        supplier: Supplier = supplier_by_id[agreement.supplier_id]

        if agreement.effective_from != assortment.ranged_from:
            raise ValueError("sourcing does not begin with assortment")

        if agreement.effective_to != assortment.ranged_to:
            raise ValueError("sourcing does not end with assortment")

        if supplier.created_at > agreement.effective_from:
            raise ValueError("supplier did not exist at sourcing start")

        if supplier.inactive_at is not None and (
            agreement.effective_to is None or supplier.inactive_at < agreement.effective_to
        ):
            raise ValueError("supplier lifecycle does not cover sourcing agreement")


def _validate_currencies(
    agreements: tuple[SourcingAgreement, ...],
    context: SimulationContext,
) -> None:
    currency_by_market: dict[str, str] = {
        market.market_code: market.currency for market in context.config.markets
    }

    for agreement in agreements:
        if agreement.currency != currency_by_market[agreement.market_code]:
            raise ValueError("sourcing cost uses incorrect market currency")
