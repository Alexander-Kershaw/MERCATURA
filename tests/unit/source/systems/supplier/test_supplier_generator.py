from collections import Counter
from datetime import date
from typing import Any

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.supplier.config import (
    DEFAULT_MARKET_SUPPLIERS,
)
from mercatura.source.systems.supplier.generator import (
    generate_suppliers,
)
from mercatura.source.systems.supplier.model import Supplier
from mercatura.source.systems.supplier.validation import (
    validate_suppliers,
)


def build_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )


def test_default_generation_creates_expected_supplier_count() -> None:
    suppliers: tuple[Supplier, ...] = generate_suppliers(context=build_context())

    expected: int = sum(config.supplier_count for config in DEFAULT_MARKET_SUPPLIERS)

    assert len(suppliers) == expected


def test_supplier_generation_is_deterministic() -> None:
    assert generate_suppliers(context=build_context()) == generate_suppliers(
        context=build_context()
    )


def test_supplier_ids_are_unique() -> None:
    suppliers: tuple[Supplier, ...] = generate_suppliers(context=build_context())

    identifiers: list[str] = [supplier.supplier_id for supplier in suppliers]

    assert len(identifiers) == len(set(identifiers))


def test_supplier_codes_are_unique() -> None:
    suppliers: tuple[Supplier, ...] = generate_suppliers(context=build_context())

    codes: list[str] = [supplier.supplier_code for supplier in suppliers]

    assert len(codes) == len(set(codes))


def test_market_counts_match_configuration() -> None:
    suppliers: tuple[Supplier, ...] = generate_suppliers(context=build_context())

    actual: Counter[str] = Counter(supplier.country_code for supplier in suppliers)

    expected: dict[str, int] = {
        config.market_code: (config.supplier_count) for config in DEFAULT_MARKET_SUPPLIERS
    }

    assert dict(actual) == expected


def test_catalogue_contains_historical_suppliers() -> None:
    context: SimulationContext = build_context()

    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    assert any(supplier.created_at < context.config.start_date for supplier in suppliers)


def test_catalogue_contains_new_suppliers() -> None:
    context: SimulationContext = build_context()

    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    assert any(
        context.config.start_date <= supplier.created_at <= context.config.end_date
        for supplier in suppliers
    )


def test_catalogue_contains_inactive_suppliers() -> None:
    suppliers: tuple[Supplier, ...] = generate_suppliers(context=build_context())

    assert any(supplier.inactive_at is not None for supplier in suppliers)


def test_generated_suppliers_pass_validation() -> None:
    context: SimulationContext = build_context()

    suppliers: tuple[Supplier, ...] = generate_suppliers(context)

    validate_suppliers(
        suppliers,
        context,
    )


def normalize(rows: Any) -> list[Supplier]:
    return sorted(rows, key=lambda row: row.supplier_code)


def test_market_configuration_order_does_not_change_suppliers() -> None:
    first_context: SimulationContext = build_context()
    second_context: SimulationContext = build_context()

    first: tuple[Supplier, ...] = generate_suppliers(context=first_context)

    second: tuple[Supplier, ...] = generate_suppliers(
        context=second_context,
        market_configs=tuple(reversed(DEFAULT_MARKET_SUPPLIERS)),
    )

    assert normalize(rows=first) == normalize(rows=second)
