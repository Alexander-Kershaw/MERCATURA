import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from mercatura.source.estate.export import (
    export_source_estate,
)
from mercatura.source.estate.reconciliation import (
    reconcile_source_estate,
    validate_source_estate_reconciliation,
)
from mercatura.source.estate.source_estate import (
    SourceEstate,
)
from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    generate_demand_profiles,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.availability.generator import (
    generate_availability_snapshots,
)
from mercatura.source.systems.crm.generator import (
    generate_customers,
)
from mercatura.source.systems.fulfilment.generator import (
    generate_fulfilment_allocations,
)
from mercatura.source.systems.fulfilment.outbound_generator import (
    generate_outbound_fulfilment,
)
from mercatura.source.systems.fulfilment.reservation_generator import (
    generate_inventory_reservations,
)
from mercatura.source.systems.loyalty.generator import (
    generate_loyalty_memberships,
)
from mercatura.source.systems.oms.generator import (
    generate_orders,
)
from mercatura.source.systems.payments.generator import (
    generate_payment_attempts,
)
from mercatura.source.systems.payments.refund_generator import (
    generate_refunds,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pricing.generator import (
    generate_prices,
)
from mercatura.source.systems.procurement.fulfilment_generator import (
    generate_fulfilment as generate_supplier_fulfilment,
)
from mercatura.source.systems.procurement.generator import (
    generate_sourcing_agreements,
)
from mercatura.source.systems.procurement.purchase_order_generator import (
    generate_purchase_orders,
)
from mercatura.source.systems.returns.disposition_generator import (
    generate_return_dispositions,
)
from mercatura.source.systems.returns.generator import (
    generate_customer_returns,
)
from mercatura.source.systems.store.generator import (
    generate_stores,
)
from mercatura.source.systems.supplier.capability_generator import (
    generate_supplier_capabilities,
)
from mercatura.source.systems.supplier.generator import (
    generate_suppliers,
)
from mercatura.source.systems.wms.assortment_generator import (
    generate_warehouse_assortments,
)
from mercatura.source.systems.wms.generator import (
    generate_inventory_locations,
    generate_warehouses,
)
from mercatura.source.systems.wms.inventory_generator import (
    generate_inventory_movements,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.opening_inventory_generator import (
    generate_opening_inventory_movements,
)
from mercatura.source.systems.wms.routing_generator import (
    generate_inbound_receipt_routes,
)


def build_source_estate(context: SimulationContext) -> SourceEstate:

    # ==================================================================================
    # Physical retail estate
    # ==================================================================================

    stores = generate_stores(context)

    products = generate_products(context)

    assortments = generate_assortments(
        context,
        products,
    )

    prices = generate_prices(
        context,
        products,
        assortments,
    )

    demand_profiles = generate_demand_profiles(
        context,
        products,
        assortments,
    )

    # ==================================================================================
    # Supplier / procurement estate
    # ==================================================================================

    suppliers = generate_suppliers(context)

    supplier_capabilities = generate_supplier_capabilities(
        context,
        suppliers,
        products,
    )

    sourcing_agreements = generate_sourcing_agreements(
        context,
        products,
        assortments,
        suppliers,
        supplier_capabilities,
        prices,
    )

    (
        purchase_orders,
        purchase_order_lines,
    ) = generate_purchase_orders(
        context,
        assortments,
        sourcing_agreements,
        demand_profiles,
    )

    (
        purchase_order_line_fulfilments,
        supplier_shipments,
        goods_receipts,
    ) = generate_supplier_fulfilment(
        context,
        purchase_orders,
        purchase_order_lines,
    )

    # ==================================================================================
    # Warehouse topology
    # ==================================================================================

    warehouses = generate_warehouses(context)

    inventory_locations = generate_inventory_locations(
        context,
        warehouses,
    )

    warehouse_assortments = generate_warehouse_assortments(
        context,
        assortments,
        demand_profiles,
        warehouses,
    )

    inbound_receipt_routes = generate_inbound_receipt_routes(
        context,
        purchase_orders,
        purchase_order_lines,
        warehouse_assortments,
        inventory_locations,
    )

    receipt_inventory_movements = generate_inventory_movements(
        context,
        goods_receipts,
        inbound_receipt_routes,
        inventory_locations,
    )

    opening_inventory_movements = generate_opening_inventory_movements(
        context,
        demand_profiles,
        warehouse_assortments,
        inventory_locations,
    )

    pre_sales_inventory_movements = _ordered_inventory_movements(
        (
            *opening_inventory_movements,
            *receipt_inventory_movements,
        )
    )

    # ==================================================================================
    # Customer estate
    # ==================================================================================

    customers = generate_customers(context)

    loyalty_memberships = generate_loyalty_memberships(
        context,
        customers,
    )

    # ==================================================================================
    # Commerce
    # ==================================================================================

    (
        orders,
        order_items,
    ) = generate_orders(
        context,
        customers,
        stores,
        assortments,
        prices,
        demand_profiles,
    )

    payment_attempts = generate_payment_attempts(
        context,
        orders,
    )

    # ==================================================================================
    # Fulfilment
    # ==================================================================================

    (
        fulfilment_requests,
        fulfilment_allocations,
    ) = generate_fulfilment_allocations(
        context,
        orders,
        order_items,
        warehouse_assortments,
        pre_sales_inventory_movements,
        inventory_locations,
    )

    initial_reservations = generate_inventory_reservations(fulfilment_allocations)

    (
        inventory_reservations,
        outbound_shipments,
        outbound_inventory_movements,
    ) = generate_outbound_fulfilment(
        initial_reservations,
        pre_sales_inventory_movements,
        inventory_locations,
    )

    # ==================================================================================
    # Reverse logistics
    # ==================================================================================

    (
        customer_returns,
        return_receipt_movements,
    ) = generate_customer_returns(
        outbound_shipments,
        inventory_locations,
    )

    (
        return_dispositions,
        return_disposition_movements,
    ) = generate_return_dispositions(
        customer_returns,
        inventory_locations,
    )

    refunds = generate_refunds(
        customer_returns,
        order_items,
        payment_attempts,
    )

    # ==================================================================================
    # Complete physical inventory ledger
    # ==================================================================================

    inventory_movements = _ordered_inventory_movements(
        (
            *pre_sales_inventory_movements,
            *outbound_inventory_movements,
            *return_receipt_movements,
            *return_disposition_movements,
        )
    )

    # ==================================================================================
    # End-of-period operational availability
    # ==================================================================================

    availability_snapshots = generate_availability_snapshots(
        snapshot_date=(context.config.end_date),
        demand_profiles=(demand_profiles),
        warehouse_assortments=(warehouse_assortments),
        inventory_movements=(inventory_movements),
        locations=(inventory_locations),
        reservations=(inventory_reservations),
    )

    # ==================================================================================
    # Estate-wide reconciliation
    # ==================================================================================

    reconciliation = reconcile_source_estate(
        orders=orders,
        order_items=order_items,
        payment_attempts=(payment_attempts),
        fulfilment_requests=(fulfilment_requests),
        allocations=(fulfilment_allocations),
        reservations=(inventory_reservations),
        shipments=(outbound_shipments),
        customer_returns=(customer_returns),
        dispositions=(return_dispositions),
        refunds=refunds,
        inventory_movements=(inventory_movements),
    )

    validate_source_estate_reconciliation(reconciliation)

    return SourceEstate(
        context=context,
        stores=stores,
        products=products,
        assortments=assortments,
        prices=prices,
        demand_profiles=(demand_profiles),
        suppliers=suppliers,
        supplier_capabilities=(supplier_capabilities),
        sourcing_agreements=(sourcing_agreements),
        purchase_orders=(purchase_orders),
        purchase_order_lines=(purchase_order_lines),
        purchase_order_line_fulfilments=(purchase_order_line_fulfilments),
        supplier_shipments=(supplier_shipments),
        goods_receipts=(goods_receipts),
        warehouses=warehouses,
        inventory_locations=(inventory_locations),
        warehouse_assortments=(warehouse_assortments),
        inbound_receipt_routes=(inbound_receipt_routes),
        customers=customers,
        loyalty_memberships=(loyalty_memberships),
        orders=orders,
        order_items=order_items,
        payment_attempts=(payment_attempts),
        fulfilment_requests=(fulfilment_requests),
        fulfilment_allocations=(fulfilment_allocations),
        inventory_reservations=(inventory_reservations),
        outbound_shipments=(outbound_shipments),
        customer_returns=(customer_returns),
        return_dispositions=(return_dispositions),
        refunds=refunds,
        inventory_movements=(inventory_movements),
        availability_snapshots=(availability_snapshots),
        reconciliation=(reconciliation),
    )


def _ordered_inventory_movements(
    movements: tuple[
        InventoryMovement,
        ...,
    ],
) -> tuple[
    InventoryMovement,
    ...,
]:
    return tuple(
        sorted(
            movements,
            key=lambda movement: (
                movement.event_date,
                movement.movement_group_id,
                movement.movement_sequence,
                movement.movement_id,
            ),
        )
    )


def _parse_date(
    value: str,
) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def main(
    argv: Sequence[str] | None = None,
) -> None:
    parser = argparse.ArgumentParser(
        description=("Build the deterministic Mercatura source estate.")
    )

    parser.add_argument(
        "--start-date",
        type=_parse_date,
        default=date(
            2024,
            1,
            1,
        ),
    )

    parser.add_argument(
        "--end-date",
        type=_parse_date,
        default=date(
            2026,
            12,
            31,
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=777,
    )

    parser.add_argument(
        "--generator-version",
        default="0.1.0",
    )

    parser.add_argument(
        "--reporting-currency",
        default="GBP",
    )

    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
    )

    parser.add_argument(
        "--defect",
        action="append",
        default=[],
    )

    parser.add_argument(
        "--output",
        type=Path,
    )

    parser.add_argument(
        "--no-export",
        action="store_true",
    )

    args = parser.parse_args(argv)

    config = SimulationConfig(
        start_date=args.start_date,
        end_date=args.end_date,
        seed=args.seed,
        generator_version=(args.generator_version),
        scenarios=tuple(args.scenario),
        defects=tuple(args.defect),
        reporting_currency=(args.reporting_currency),
    )

    context = SimulationContext.create(config)

    estate = build_source_estate(context)

    print()
    print("Mercatura source estate built successfully")

    print(f"simulation_id: {estate.simulation_id}")

    print("reconciliation: PASS")

    print()
    print("Source dataset counts:")

    for (
        name,
        rows,
    ) in estate.source_datasets().items():
        print(f"  {name:<36} {len(rows):>12,}")

    print()
    print("Internal simulator state:")

    for (
        name,
        rows,
    ) in estate.internal_datasets().items():
        print(f"  {name:<36} {len(rows):>12,}")

    if args.no_export:
        return

    output_directory = (
        args.output
        if args.output is not None
        else (Path("artifacts") / "source-estate" / estate.simulation_id)
    )

    manifest_path = export_source_estate(
        estate,
        output_directory,
    )

    print()
    print(f"Exported to: {output_directory}")

    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
