from datetime import date
from decimal import Decimal

from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)


def build_agreement(
    *,
    effective_from: date = date(year=2024, month=1, day=1),
    effective_to: date | None = date(year=2025, month=1, day=1),
) -> SourcingAgreement:
    return SourcingAgreement(
        sourcing_id="src_test",
        assortment_id="ast_test",
        product_id="prd_test",
        sku="MRC-000001",
        market_code="GB",
        supplier_id="sup_test",
        supplier_code="SUP-GB-0001",
        sourcing_role="PRIMARY",
        unit_cost=Decimal(value="20.00"),
        currency="GBP",
        minimum_order_quantity=10,
        lead_time_days=7,
        effective_from=effective_from,
        effective_to=effective_to,
    )


def test_agreement_not_effective_before_start() -> None:
    agreement: SourcingAgreement = build_agreement()

    assert not agreement.is_effective_on(value=date(year=2023, month=12, day=31))


def test_effective_from_is_inclusive() -> None:
    agreement: SourcingAgreement = build_agreement()

    assert agreement.is_effective_on(value=date(year=2024, month=1, day=1))


def test_agreement_effective_inside_interval() -> None:
    agreement: SourcingAgreement = build_agreement()

    assert agreement.is_effective_on(value=date(year=2024, month=6, day=1))


def test_effective_to_is_exclusive() -> None:
    agreement: SourcingAgreement = build_agreement()

    assert not agreement.is_effective_on(value=date(year=2025, month=1, day=1))


def test_open_ended_agreement_remains_effective() -> None:
    agreement: SourcingAgreement = build_agreement(effective_to=None)

    assert agreement.is_effective_on(value=date(year=2035, month=1, day=1))
