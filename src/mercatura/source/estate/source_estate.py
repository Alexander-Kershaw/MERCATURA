from dataclasses import dataclass

from mercatura.source.estate.model import (
    EstateReconciliationReport,
)
from mercatura.source.simulation import (
    SimulationContext,
)

SourceRows = tuple[object, ...]


@dataclass(
    frozen=True,
    slots=True,
)
class SourceEstate:
    context: SimulationContext
    stores: SourceRows
    products: SourceRows
    assortments: SourceRows
    prices: SourceRows
    demand_profiles: SourceRows
    suppliers: SourceRows
    supplier_capabilities: SourceRows
    sourcing_agreements: SourceRows
    purchase_orders: SourceRows
    purchase_order_lines: SourceRows
    purchase_order_line_fulfilments: SourceRows
    supplier_shipments: SourceRows
    goods_receipts: SourceRows
    warehouses: SourceRows
    inventory_locations: SourceRows
    warehouse_assortments: SourceRows
    inbound_receipt_routes: SourceRows
    customers: SourceRows
    loyalty_memberships: SourceRows
    orders: SourceRows
    order_items: SourceRows
    payment_attempts: SourceRows
    fulfilment_requests: SourceRows
    fulfilment_allocations: SourceRows
    inventory_reservations: SourceRows
    outbound_shipments: SourceRows
    customer_returns: SourceRows
    return_dispositions: SourceRows
    refunds: SourceRows
    inventory_movements: SourceRows
    availability_snapshots: SourceRows
    reconciliation: EstateReconciliationReport

    @property
    def simulation_id(self) -> str:
        return self.context.simulation_id

    def source_datasets(self) -> dict[str, SourceRows]:

        return {
            "stores": self.stores,
            "products": self.products,
            "assortments": self.assortments,
            "prices": self.prices,
            "suppliers": self.suppliers,
            "supplier_capabilities": (self.supplier_capabilities),
            "sourcing_agreements": (self.sourcing_agreements),
            "purchase_orders": (self.purchase_orders),
            "purchase_order_lines": (self.purchase_order_lines),
            "purchase_order_line_fulfilments": (self.purchase_order_line_fulfilments),
            "supplier_shipments": (self.supplier_shipments),
            "goods_receipts": (self.goods_receipts),
            "warehouses": self.warehouses,
            "inventory_locations": (self.inventory_locations),
            "warehouse_assortments": (self.warehouse_assortments),
            "inbound_receipt_routes": (self.inbound_receipt_routes),
            "customers": self.customers,
            "loyalty_memberships": (self.loyalty_memberships),
            "orders": self.orders,
            "order_items": self.order_items,
            "payment_attempts": (self.payment_attempts),
            "fulfilment_requests": (self.fulfilment_requests),
            "fulfilment_allocations": (self.fulfilment_allocations),
            "inventory_reservations": (self.inventory_reservations),
            "outbound_shipments": (self.outbound_shipments),
            "customer_returns": (self.customer_returns),
            "return_dispositions": (self.return_dispositions),
            "refunds": self.refunds,
            "inventory_movements": (self.inventory_movements),
            "availability_snapshots": (self.availability_snapshots),
        }

    def internal_datasets(self) -> dict[str, SourceRows]:

        return {
            "demand_profiles": (self.demand_profiles),
        }
