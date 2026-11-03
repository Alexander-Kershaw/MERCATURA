from collections import defaultdict
from decimal import Decimal

from mercatura.source.reference.currency import (
    CURRENCY_MINOR_UNITS,
)
from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.model import (
    Product,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.procurement.config import (
    MARKET_REGIONS,
)
from mercatura.source.systems.procurement.generator import (
    generate_sourcing_agreements,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.supplier.capability_model import (
    SupplierCapability,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def group_by_assortment(
    agreements: tuple[SourcingAgreement, ...],
) -> dict[
    str,
    list[SourcingAgreement],
]:
    grouped: dict[
        str,
        list[SourcingAgreement],
    ] = defaultdict(list)

    for agreement in agreements:
        grouped[agreement.assortment_id].append(agreement)

    return grouped


def normalize(
    agreements: tuple[SourcingAgreement, ...],
) -> list[SourcingAgreement]:
    return sorted(
        agreements,
        key=lambda agreement: (
            agreement.market_code,
            agreement.sku,
            agreement.sourcing_role,
            agreement.supplier_code,
        ),
    )


def test_generation_is_deterministic(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    capabilities: tuple[SupplierCapability, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    first: tuple[SourcingAgreement, ...] = generate_sourcing_agreements(
        context,
        products,
        assortments,
        suppliers,
        capabilities,
        prices,
    )

    second: tuple[SourcingAgreement, ...] = generate_sourcing_agreements(
        context,
        products,
        assortments,
        suppliers,
        capabilities,
        prices,
    )

    assert first == second


def test_every_assortment_has_sourcing(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    actual: set[str] = {agreement.assortment_id for agreement in agreements}

    expected: set[str] = {assortment.assortment_id for assortment in assortments}

    assert actual == expected


def test_sourcing_ids_are_unique(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    identifiers: list[str] = [agreement.sourcing_id for agreement in agreements]

    assert len(identifiers) == len(set(identifiers))


def test_exactly_one_primary_per_assortment(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    for rows in grouped.values():
        assert sum(row.sourcing_role == "PRIMARY" for row in rows) == 1


def test_source_topology_is_valid(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    for rows in grouped.values():
        roles: set[str] = {row.sourcing_role for row in rows}

        if len(rows) == 1:
            assert roles == {
                "PRIMARY",
            }

        elif len(rows) == 2:
            assert roles == {
                "PRIMARY",
                "SECONDARY",
            }

        else:
            assert len(rows) == 3

            assert roles == {
                "PRIMARY",
                "SECONDARY",
                "BACKUP",
            }


def test_supplier_is_unique_within_assortment(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    for rows in grouped.values():
        supplier_ids: list[str] = [row.supplier_id for row in rows]

        assert len(supplier_ids) == len(set(supplier_ids))


def test_all_assortment_references_are_valid(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    valid: set[str] = {assortment.assortment_id for assortment in assortments}

    assert all(agreement.assortment_id in valid for agreement in agreements)


def test_all_supplier_references_are_valid(
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    valid: set[str] = {supplier.supplier_id for supplier in suppliers}

    assert all(agreement.supplier_id in valid for agreement in agreements)


def test_agreement_metadata_matches_assortment(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    for agreement in agreements:
        assortment: ProductMarketAssortment = by_id[agreement.assortment_id]

        assert agreement.product_id == assortment.product_id

        assert agreement.sku == assortment.sku

        assert agreement.market_code == assortment.market_code


def test_supplier_code_matches_supplier(
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    for agreement in agreements:
        supplier = by_id[agreement.supplier_id]

        assert agreement.supplier_code == supplier.supplier_code


def test_unit_costs_are_decimal(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    assert all(
        isinstance(
            agreement.unit_cost,
            Decimal,
        )
        for agreement in agreements
    )


def test_unit_costs_are_positive(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    assert all(agreement.unit_cost > Decimal("0") for agreement in agreements)


def test_unit_cost_below_initial_retail_price(
    agreements: tuple[SourcingAgreement, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    initial_prices: dict[str, Decimal] = {
        price.assortment_id: price.list_price for price in prices if price.version == 1
    }

    for agreement in agreements:
        assert agreement.unit_cost < initial_prices[agreement.assortment_id]


def test_cost_currency_matches_buyer_market(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    currencies: dict[str, str] = {
        market.market_code: market.currency for market in context.config.markets
    }

    for agreement in agreements:
        assert agreement.currency == currencies[agreement.market_code]


def test_costs_respect_currency_minor_units(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    for agreement in agreements:
        minor_unit: Decimal = CURRENCY_MINOR_UNITS[agreement.currency]

        assert (agreement.unit_cost % minor_unit) == Decimal(value="0")


def test_moq_is_positive(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    assert all(agreement.minimum_order_quantity > 0 for agreement in agreements)


def test_lead_time_is_positive(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    assert all(agreement.lead_time_days > 0 for agreement in agreements)


def test_agreement_lifetime_matches_assortment(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    by_id: dict[str, ProductMarketAssortment] = {
        assortment.assortment_id: assortment for assortment in assortments
    }

    for agreement in agreements:
        assortment: ProductMarketAssortment = by_id[agreement.assortment_id]

        assert agreement.effective_from == assortment.ranged_from

        assert agreement.effective_to == assortment.ranged_to


def test_supplier_lifecycle_covers_agreement(
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    for agreement in agreements:
        supplier = by_id[agreement.supplier_id]

        assert supplier.created_at <= agreement.effective_from

        if agreement.effective_to is None:
            assert supplier.inactive_at is None

        elif supplier.inactive_at is not None:
            assert supplier.inactive_at >= agreement.effective_to


def test_single_source_assortments_exist(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    assert any(len(rows) == 1 for rows in grouped.values())


def test_dual_source_assortments_exist(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    assert any(len(rows) == 2 for rows in grouped.values())


def test_triple_source_assortments_exist(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    assert any(len(rows) == 3 for rows in grouped.values())


def test_source_count_distribution_is_reasonable(
    agreements: tuple[SourcingAgreement, ...],
) -> None:
    grouped: dict[str, list[SourcingAgreement]] = group_by_assortment(agreements)

    total: int = len(grouped)

    single: float = sum(len(rows) == 1 for rows in grouped.values()) / total

    dual: float = sum(len(rows) == 2 for rows in grouped.values()) / total

    triple: float = sum(len(rows) == 3 for rows in grouped.values()) / total

    assert 0.35 <= single <= 0.55
    assert 0.30 <= dual <= 0.50
    assert 0.08 <= triple <= 0.22


def test_domestic_sourcing_exists(
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    assert any(
        by_id[agreement.supplier_id].country_code == agreement.market_code
        for agreement in agreements
    )


def test_same_region_international_sourcing_exists(
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    assert any(
        (by_id[agreement.supplier_id].country_code != agreement.market_code)
        and (
            MARKET_REGIONS[by_id[agreement.supplier_id].country_code]
            == MARKET_REGIONS[agreement.market_code]
        )
        for agreement in agreements
    )


def test_cross_region_sourcing_exists(
    agreements: tuple[SourcingAgreement, ...],
    suppliers: tuple[Supplier, ...],
) -> None:
    by_id: dict[str, Supplier] = {supplier.supplier_id: supplier for supplier in suppliers}

    assert any(
        MARKET_REGIONS[by_id[agreement.supplier_id].country_code]
        != MARKET_REGIONS[agreement.market_code]
        for agreement in agreements
    )


def test_supplier_input_order_does_not_change_results(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    capabilities: tuple[SupplierCapability, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    first: tuple[SourcingAgreement, ...] = generate_sourcing_agreements(
        context,
        products,
        assortments,
        suppliers,
        capabilities,
        prices,
    )

    second: tuple[SourcingAgreement, ...] = generate_sourcing_agreements(
        context,
        products,
        assortments,
        tuple(reversed(suppliers)),
        capabilities,
        prices,
    )

    assert normalize(agreements=first) == normalize(agreements=second)


def test_assortment_input_order_does_not_change_results(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    capabilities: tuple[SupplierCapability, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    first: tuple[SourcingAgreement, ...] = generate_sourcing_agreements(
        context,
        products,
        assortments,
        suppliers,
        capabilities,
        prices,
    )

    second: tuple[SourcingAgreement, ...] = generate_sourcing_agreements(
        context,
        products,
        tuple(reversed(assortments)),
        suppliers,
        capabilities,
        prices,
    )

    assert normalize(agreements=first) == normalize(agreements=second)


def test_every_sourcing_supplier_has_required_capability(
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    products: tuple[Product, ...],
    capabilities: tuple[SupplierCapability, ...],
) -> None:
    product_by_id: dict[str, Product] = {product.product_id: product for product in products}

    capability_keys: set[tuple[str, str]] = {
        (
            capability.supplier_id,
            capability.department_code,
        )
        for capability in capabilities
    }

    for agreement in agreements:
        product: Product = product_by_id[agreement.product_id]

        assert (
            agreement.supplier_id,
            product.department_code,
        ) in capability_keys
