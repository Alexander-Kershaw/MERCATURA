from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.supplier.config import (
    SUPPLIER_TYPES,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def validate_suppliers(
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_ids(suppliers)

    _validate_unique_codes(suppliers)

    _validate_required_fields(suppliers)

    _validate_supplier_types(suppliers)

    _validate_markets_and_currencies(
        suppliers,
        context,
    )

    _validate_lifecycles(
        suppliers,
        context,
    )


def _validate_unique_ids(
    suppliers: tuple[Supplier, ...],
) -> None:
    identifiers: list[str] = [supplier.supplier_id for supplier in suppliers]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate supplier_id detected")


def _validate_unique_codes(
    suppliers: tuple[Supplier, ...],
) -> None:
    codes: list[str] = [supplier.supplier_code for supplier in suppliers]

    if len(codes) != len(set(codes)):
        raise ValueError("duplicate supplier_code detected")


def _validate_required_fields(
    suppliers: tuple[Supplier, ...],
) -> None:
    for supplier in suppliers:
        values: tuple[str, str, str, str, str, str] = (
            supplier.supplier_code,
            supplier.legal_name,
            supplier.country_code,
            supplier.currency,
            supplier.city,
            supplier.region,
        )

        if any(not value.strip() for value in values):
            raise ValueError(f"supplier {supplier.supplier_code} contains empty required fields")


def _validate_supplier_types(
    suppliers: tuple[Supplier, ...],
) -> None:
    valid_types: set[str] = set(SUPPLIER_TYPES)

    for supplier in suppliers:
        if supplier.supplier_type not in valid_types:
            raise ValueError(f"invalid supplier type for {supplier.supplier_code}")


def _validate_markets_and_currencies(
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    markets: dict[str, MarketConfig] = {
        market.market_code: market for market in context.config.markets
    }

    for supplier in suppliers:
        market: MarketConfig | None = markets.get(supplier.country_code)

        if market is None:
            raise ValueError(f"unknown supplier country {supplier.country_code}")

        if supplier.currency != market.currency:
            raise ValueError(f"{supplier.supplier_code} uses incorrect currency")


def _validate_lifecycles(
    suppliers: tuple[Supplier, ...],
    context: SimulationContext,
) -> None:
    for supplier in suppliers:
        if supplier.created_at > context.config.end_date:
            raise ValueError(f"{supplier.supplier_code} created after simulation end")

        if supplier.inactive_at is not None and supplier.inactive_at <= supplier.created_at:
            raise ValueError(f"{supplier.supplier_code} has invalid lifecycle")

        if supplier.inactive_at is not None and supplier.inactive_at > context.config.end_date:
            raise ValueError(f"{supplier.supplier_code} becomes inactive after simulation end")
