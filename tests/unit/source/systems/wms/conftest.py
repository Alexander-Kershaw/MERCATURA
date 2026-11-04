from datetime import date

import pytest

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    DemandProfile,
    generate_demand_profiles,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import (
    Product,
)
from mercatura.source.systems.pricing.generator import (
    generate_prices,
)
from mercatura.source.systems.pricing.model import (
    ProductPrice,
)
from mercatura.source.systems.procurement.fulfilment_generator import (
    generate_fulfilment,
)
from mercatura.source.systems.procurement.fulfilment_model import (
    GoodsReceipt,
    PurchaseOrderLineFulfilment,
    SupplierShipment,
)
from mercatura.source.systems.procurement.generator import (
    generate_sourcing_agreements,
)
from mercatura.source.systems.procurement.model import (
    SourcingAgreement,
)
from mercatura.source.systems.procurement.purchase_order_generator import (
    generate_purchase_orders,
)
from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)
from mercatura.source.systems.supplier.capability_generator import (
    generate_supplier_capabilities,
)
from mercatura.source.systems.supplier.capability_model import (
    SupplierCapability,
)
from mercatura.source.systems.supplier.generator import (
    generate_suppliers,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)
from mercatura.source.systems.wms.assortment_generator import (
    generate_warehouse_assortments,
)
from mercatura.source.systems.wms.assortment_model import (
    WarehouseAssortment,
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
from mercatura.source.systems.wms.model import (
    InventoryLocation,
    Warehouse,
)
from mercatura.source.systems.wms.routing_generator import (
    generate_inbound_receipt_routes,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)


@pytest.fixture(scope="session")
def wms_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(
                year=2024,
                month=1,
                day=1,
            ),
            end_date=date(
                year=2026,
                month=12,
                day=31,
            ),
            seed=42,
        )
    )


@pytest.fixture(scope="session")
def warehouses(
    wms_context: SimulationContext,
) -> tuple[Warehouse, ...]:
    return generate_warehouses(context=wms_context)


@pytest.fixture(scope="session")
def inventory_locations(
    wms_context: SimulationContext,
    warehouses: tuple[Warehouse, ...],
) -> tuple[InventoryLocation, ...]:
    return generate_inventory_locations(
        wms_context,
        warehouses,
    )


@pytest.fixture(scope="session")
def products(
    wms_context: SimulationContext,
) -> tuple[Product, ...]:
    return generate_products(wms_context)


@pytest.fixture(scope="session")
def assortments(
    wms_context: SimulationContext,
    products: tuple[Product, ...],
) -> tuple[ProductMarketAssortment, ...]:
    return generate_assortments(
        wms_context,
        products,
    )


@pytest.fixture(scope="session")
def demand_profiles(
    wms_context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[DemandProfile, ...]:
    return generate_demand_profiles(
        wms_context,
        products,
        assortments,
    )


@pytest.fixture(scope="session")
def prices(
    wms_context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> tuple[ProductPrice, ...]:
    return generate_prices(
        wms_context,
        products,
        assortments,
    )


@pytest.fixture(scope="session")
def suppliers(
    wms_context: SimulationContext,
) -> tuple[Supplier, ...]:
    return generate_suppliers(wms_context)


@pytest.fixture(scope="session")
def capabilities(
    wms_context: SimulationContext,
    suppliers: tuple[Supplier, ...],
    products: tuple[Product, ...],
) -> tuple[SupplierCapability, ...]:
    return generate_supplier_capabilities(
        wms_context,
        suppliers,
        products,
    )


@pytest.fixture(scope="session")
def agreements(
    wms_context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    capabilities: tuple[SupplierCapability, ...],
    prices: tuple[ProductPrice, ...],
) -> tuple[SourcingAgreement, ...]:
    return generate_sourcing_agreements(
        wms_context,
        products,
        assortments,
        suppliers,
        capabilities,
        prices,
    )


@pytest.fixture(scope="session")
def purchase_order_dataset(
    wms_context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    agreements: tuple[SourcingAgreement, ...],
    demand_profiles: tuple[DemandProfile, ...],
) -> tuple[
    tuple[PurchaseOrder, ...],
    tuple[PurchaseOrderLine, ...],
]:
    return generate_purchase_orders(
        wms_context,
        assortments,
        agreements,
        demand_profiles,
    )


@pytest.fixture(scope="session")
def purchase_orders(
    purchase_order_dataset: tuple[tuple[PurchaseOrder, ...], tuple[PurchaseOrderLine, ...]],
) -> tuple[PurchaseOrder, ...]:
    return purchase_order_dataset[0]


@pytest.fixture(scope="session")
def purchase_order_lines(
    purchase_order_dataset: tuple[tuple[PurchaseOrder, ...], tuple[PurchaseOrderLine, ...]],
) -> tuple[PurchaseOrderLine, ...]:
    return purchase_order_dataset[1]


@pytest.fixture(scope="session")
def warehouse_assortments(
    wms_context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
) -> tuple[WarehouseAssortment, ...]:
    return generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        warehouses,
    )


@pytest.fixture(scope="session")
def inbound_routes(
    wms_context: SimulationContext,
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> tuple[InboundReceiptRoute, ...]:
    return generate_inbound_receipt_routes(
        wms_context,
        purchase_orders,
        purchase_order_lines,
        warehouse_assortments,
        inventory_locations,
    )


@pytest.fixture(scope="session")
def fulfilment_dataset(
    wms_context: SimulationContext,
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> tuple[
    tuple[PurchaseOrderLineFulfilment, ...],
    tuple[SupplierShipment, ...],
    tuple[GoodsReceipt, ...],
]:
    return generate_fulfilment(
        wms_context,
        purchase_orders,
        purchase_order_lines,
    )


@pytest.fixture(scope="session")
def goods_receipts(
    fulfilment_dataset: tuple[
        tuple[PurchaseOrderLineFulfilment, ...],
        tuple[SupplierShipment, ...],
        tuple[GoodsReceipt, ...],
    ],
) -> tuple[GoodsReceipt, ...]:
    return fulfilment_dataset[2]


@pytest.fixture(scope="session")
def inventory_movements(
    wms_context: SimulationContext,
    goods_receipts: tuple[GoodsReceipt, ...],
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> tuple[InventoryMovement, ...]:
    return generate_inventory_movements(
        wms_context,
        goods_receipts,
        inbound_routes,
        inventory_locations,
    )
