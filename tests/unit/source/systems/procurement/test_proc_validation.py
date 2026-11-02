from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from typing import cast

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
    SourcingRole,
)
from mercatura.source.systems.procurement.validation import (
    validate_sourcing_agreements,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def replace_agreement(
    agreements: tuple[SourcingAgreement, ...],
    replacement: SourcingAgreement,
) -> tuple[SourcingAgreement, ...]:
    return tuple(
        replacement if row.sourcing_id == replacement.sourcing_id else row for row in agreements
    )


def replace_supplier(
    suppliers: tuple[Supplier, ...],
    replacement: Supplier,
) -> tuple[Supplier, ...]:
    return tuple(
        replacement if row.supplier_id == replacement.supplier_id else row for row in suppliers
    )


def find_dual_source_assortment(
    agreements: tuple[SourcingAgreement, ...],
) -> list[SourcingAgreement]:
    grouped: dict[
        str,
        list[SourcingAgreement],
    ] = {}

    for agreement in agreements:
        grouped.setdefault(
            agreement.assortment_id,
            [],
        ).append(agreement)

    return next(rows for rows in grouped.values() if len(rows) == 2)


def find_triple_source_assortment(
    agreements: tuple[SourcingAgreement, ...],
) -> list[SourcingAgreement]:
    grouped: dict[
        str,
        list[SourcingAgreement],
    ] = {}

    for agreement in agreements:
        grouped.setdefault(
            agreement.assortment_id,
            [],
        ).append(agreement)

    return next(rows for rows in grouped.values() if len(rows) == 3)


def initial_price_for(
    assortment_id: str,
    prices: tuple[ProductPrice, ...],
) -> ProductPrice:
    return next(
        price for price in prices if (price.assortment_id == assortment_id and price.version == 1)
    )


def test_valid_dataset_passes_validation(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    validate_sourcing_agreements(
        agreements,
        assortments,
        suppliers,
        prices,
        context,
    )


def test_rejects_duplicate_sourcing_id(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken = (
        *agreements,
        agreements[0],
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            broken,
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_unknown_assortment(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        assortment_id="ast_missing",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_unknown_supplier(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        supplier_id="sup_missing",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_product_mismatch(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        product_id="prd_wrong",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_sku_mismatch(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        sku="MRC-WRONG",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_market_mismatch(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        market_code="ZZ",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_supplier_code_mismatch(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        supplier_code="SUP-WRONG",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_invalid_sourcing_role(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        sourcing_role=cast(
            SourcingRole,
            "INVALID",
        ),
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_multiple_primary_suppliers(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    rows: list[SourcingAgreement] = find_dual_source_assortment(agreements)

    secondary: SourcingAgreement = next(row for row in rows if row.sourcing_role == "SECONDARY")

    broken_row: SourcingAgreement = replace(
        secondary,
        sourcing_role="PRIMARY",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_duplicate_role(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    rows: list[SourcingAgreement] = find_triple_source_assortment(agreements)

    backup: SourcingAgreement = next(row for row in rows if row.sourcing_role == "BACKUP")

    broken_row: SourcingAgreement = replace(
        backup,
        sourcing_role="SECONDARY",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_same_supplier_in_multiple_roles(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    rows: list[SourcingAgreement] = find_dual_source_assortment(agreements)

    primary: SourcingAgreement = next(row for row in rows if row.sourcing_role == "PRIMARY")

    secondary: SourcingAgreement = next(row for row in rows if row.sourcing_role == "SECONDARY")

    broken_row: SourcingAgreement = replace(
        secondary,
        supplier_id=primary.supplier_id,
        supplier_code=primary.supplier_code,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_non_decimal_cost(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        unit_cost=cast(
            Decimal,
            1.0,
        ),
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(
        Decimal(value="0"),
        Decimal(value="-1"),
    ),
)
def test_rejects_non_positive_cost(
    value: Decimal,
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        unit_cost=value,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_cost_at_or_above_retail_price(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: SourcingAgreement = agreements[0]

    initial_price: ProductPrice = initial_price_for(
        target.assortment_id,
        prices,
    )

    broken_row: SourcingAgreement = replace(
        target,
        unit_cost=initial_price.list_price,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_zero_moq(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        minimum_order_quantity=0,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_zero_lead_time(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        lead_time_days=0,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_wrong_currency(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    broken_row: SourcingAgreement = replace(
        agreements[0],
        currency="ZZZ",
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_invalid_effective_interval(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: SourcingAgreement = agreements[0]

    broken_row: SourcingAgreement = replace(
        target,
        effective_to=target.effective_from,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_wrong_agreement_start(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: SourcingAgreement = agreements[0]

    broken_row: SourcingAgreement = replace(
        target,
        effective_from=(target.effective_from + timedelta(days=1)),
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_wrong_agreement_end(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: SourcingAgreement = next(
        agreement for agreement in agreements if agreement.effective_to is None
    )

    broken_row: SourcingAgreement = replace(
        target,
        effective_to=context.config.end_date,
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            replace_agreement(
                agreements,
                broken_row,
            ),
            assortments,
            suppliers,
            prices,
            context,
        )


def test_rejects_supplier_created_after_agreement_start(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: SourcingAgreement = agreements[0]

    supplier: Supplier = next(
        supplier for supplier in suppliers if supplier.supplier_id == target.supplier_id
    )

    broken_supplier: Supplier = replace(
        supplier,
        created_at=(target.effective_from + timedelta(days=1)),
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            agreements,
            assortments,
            replace_supplier(
                suppliers,
                broken_supplier,
            ),
            prices,
            context,
        )


def test_rejects_supplier_inactive_during_open_agreement(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: SourcingAgreement = next(
        agreement for agreement in agreements if agreement.effective_to is None
    )

    supplier: Supplier = next(
        supplier for supplier in suppliers if supplier.supplier_id == target.supplier_id
    )

    broken_supplier: Supplier = replace(
        supplier,
        inactive_at=(target.effective_from + timedelta(days=30)),
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            agreements,
            assortments,
            replace_supplier(
                suppliers,
                broken_supplier,
            ),
            prices,
            context,
        )


def test_rejects_missing_sourcing_for_assortment(
    context: SimulationContext,
    agreements: tuple[SourcingAgreement, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
) -> None:
    target: ProductMarketAssortment = assortments[0]

    broken: tuple[SourcingAgreement, ...] = tuple(
        agreement for agreement in agreements if agreement.assortment_id != target.assortment_id
    )

    with pytest.raises(expected_exception=ValueError):
        validate_sourcing_agreements(
            broken,
            assortments,
            suppliers,
            prices,
            context,
        )
