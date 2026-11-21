import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from mercatura.source.estate.export import (
    export_source_estate,
)
from mercatura.source.estate.manifest import (
    build_source_estate_manifest,
)
from mercatura.source.estate.model import (
    EstateReconciliationReport,
    ReconciliationCheck,
)
from mercatura.source.estate.source_estate import (
    SourceEstate,
)
from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)


@dataclass(
    frozen=True,
    slots=True,
)
class _TestOrder:
    order_id: str
    amount: Decimal
    event_date: date


def _estate() -> SourceEstate:
    config = SimulationConfig(
        start_date=date(
            2024,
            1,
            1,
        ),
        end_date=date(
            2024,
            1,
            31,
        ),
    )

    context = SimulationContext.create(config)

    reconciliation = EstateReconciliationReport(
        checks=(
            ReconciliationCheck(
                code="TEST",
                description=("test reconciliation"),
                actual=0,
                expected=0,
            ),
        )
    )

    return SourceEstate(
        context=context,
        stores=(),
        products=(),
        assortments=(),
        prices=(),
        demand_profiles=(
            _TestOrder(
                order_id="latent",
                amount=Decimal(value="1.00"),
                event_date=date(year=2024, month=1, day=1),
            ),
        ),
        suppliers=(),
        supplier_capabilities=(),
        sourcing_agreements=(),
        purchase_orders=(),
        purchase_order_lines=(),
        purchase_order_line_fulfilments=(),
        supplier_shipments=(),
        goods_receipts=(),
        warehouses=(),
        inventory_locations=(),
        warehouse_assortments=(),
        inbound_receipt_routes=(),
        customers=(),
        loyalty_memberships=(),
        orders=(
            _TestOrder(
                order_id="ord_001",
                amount=Decimal("19.99"),
                event_date=date(
                    2024,
                    1,
                    15,
                ),
            ),
        ),
        order_items=(),
        payment_attempts=(),
        fulfilment_requests=(),
        fulfilment_allocations=(),
        inventory_reservations=(),
        outbound_shipments=(),
        customer_returns=(),
        return_dispositions=(),
        refunds=(),
        inventory_movements=(),
        availability_snapshots=(),
        reconciliation=(reconciliation),
    )


def test_demand_profiles_are_internal_only() -> None:
    estate = _estate()

    assert "demand_profiles" not in estate.source_datasets()

    assert "demand_profiles" in estate.internal_datasets()


def test_orders_are_source_dataset() -> None:
    estate = _estate()

    assert "orders" in estate.source_datasets()

    assert len(estate.source_datasets()["orders"]) == 1


def test_manifest_contains_source_counts() -> None:
    manifest = build_source_estate_manifest(_estate())

    entries = {entry.dataset_name: entry for entry in manifest.source_datasets}

    assert entries["orders"].row_count == 1

    assert entries["orders"].file_name == "data/orders.jsonl"


def test_manifest_contains_internal_counts() -> None:
    manifest = build_source_estate_manifest(_estate())

    entries = {entry.dataset_name: entry for entry in manifest.internal_datasets}

    assert entries["demand_profiles"].row_count == 1

    assert entries["demand_profiles"].file_name is None


def test_manifest_records_reconciliation() -> None:
    manifest = build_source_estate_manifest(_estate())

    assert manifest.reconciliation_passed

    assert manifest.reconciliation_checks[0].code == "TEST"


def test_export_writes_manifest(
    tmp_path: Path,
) -> None:
    manifest_path = export_source_estate(
        _estate(),
        tmp_path,
    )

    assert manifest_path == tmp_path / "manifest.json"

    assert manifest_path.exists()


def test_export_writes_source_dataset(
    tmp_path: Path,
) -> None:
    export_source_estate(
        _estate(),
        tmp_path,
    )

    order_path = tmp_path / "data" / "orders.jsonl"

    assert order_path.exists()

    lines = order_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    record = json.loads(lines[0])

    assert record["order_id"] == "ord_001"


def test_export_serializes_decimal_as_string(
    tmp_path: Path,
) -> None:
    export_source_estate(
        _estate(),
        tmp_path,
    )

    record = json.loads((tmp_path / "data" / "orders.jsonl").read_text(encoding="utf-8").strip())

    assert record["amount"] == "19.99"


def test_export_serializes_date_as_iso_string(
    tmp_path: Path,
) -> None:
    export_source_estate(
        _estate(),
        tmp_path,
    )

    record = json.loads((tmp_path / "data" / "orders.jsonl").read_text(encoding="utf-8").strip())

    assert record["event_date"] == "2024-01-15"


def test_internal_demand_is_not_exported(
    tmp_path: Path,
) -> None:
    export_source_estate(
        _estate(),
        tmp_path,
    )

    assert not (tmp_path / "data" / "demand_profiles.jsonl").exists()


def test_export_removes_stale_dataset_file(
    tmp_path: Path,
) -> None:
    data_directory = tmp_path / "data"

    data_directory.mkdir(parents=True)

    stale = data_directory / "stale.jsonl"

    stale.write_text(
        "{}\n",
        encoding="utf-8",
    )

    export_source_estate(
        _estate(),
        tmp_path,
    )

    assert not stale.exists()
