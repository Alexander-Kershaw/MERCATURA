from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrder,
    PurchaseOrderLine,
)
from mercatura.source.systems.wms.assortment_model import (
    WarehouseAssortment,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)


def validate_inbound_receipt_routes(
    routes: tuple[InboundReceiptRoute, ...],
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    locations: tuple[InventoryLocation, ...],
) -> None:
    _validate_unique_routes(routes)

    _validate_route_coverage(
        routes,
        lines,
    )

    _validate_route_references(
        routes,
        orders,
        lines,
        warehouse_assortments,
        locations,
    )


def _validate_unique_routes(
    routes: tuple[InboundReceiptRoute, ...],
) -> None:
    route_ids: list[str] = [route.route_id for route in routes]

    if len(route_ids) != len(set(route_ids)):
        raise ValueError("duplicate inbound route_id detected")

    line_ids: list[str] = [route.purchase_order_line_id for route in routes]

    if len(line_ids) != len(set(line_ids)):
        raise ValueError("multiple inbound routes exist for purchase order line")


def _validate_route_coverage(
    routes: tuple[InboundReceiptRoute, ...],
    lines: tuple[PurchaseOrderLine, ...],
) -> None:
    actual: set[str] = {route.purchase_order_line_id for route in routes}

    expected: set[str] = {line.purchase_order_line_id for line in lines}

    if actual != expected:
        raise ValueError("inbound routes do not cover every purchase order line")


def _validate_route_references(
    routes: tuple[InboundReceiptRoute, ...],
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    locations: tuple[InventoryLocation, ...],
) -> None:
    orders_by_id: dict[str, PurchaseOrder] = {order.purchase_order_id: order for order in orders}

    lines_by_id: dict[str, PurchaseOrderLine] = {
        line.purchase_order_line_id: line for line in lines
    }

    warehouse_assortments_by_id: dict[str, WarehouseAssortment] = {
        row.warehouse_assortment_id: row for row in warehouse_assortments
    }

    locations_by_id: dict[str, InventoryLocation] = {
        location.inventory_location_id: location for location in locations
    }

    for route in routes:
        line: PurchaseOrderLine | None = lines_by_id.get(route.purchase_order_line_id)

        if line is None:
            raise ValueError("inbound route references unknown purchase order line")

        order: PurchaseOrder | None = orders_by_id.get(route.purchase_order_id)

        if order is None:
            raise ValueError("inbound route references unknown purchase order")

        if route.purchase_order_id != line.purchase_order_id:
            raise ValueError("inbound route purchase order does not match line")

        warehouse_assortment: WarehouseAssortment | None = warehouse_assortments_by_id.get(
            route.warehouse_assortment_id
        )

        if warehouse_assortment is None:
            raise ValueError("inbound route references unknown warehouse assortment")

        location: InventoryLocation | None = locations_by_id.get(route.inventory_location_id)

        if location is None:
            raise ValueError("inbound route references unknown inventory location")

        _validate_route_metadata(
            route=route,
            line=line,
            order=order,
            warehouse_assortment=(warehouse_assortment),
            location=location,
        )

        if not warehouse_assortment.is_active_on(value=order.order_date):
            raise ValueError("warehouse assortment is not active on purchase order date")


def _validate_route_metadata(
    *,
    route: InboundReceiptRoute,
    line: PurchaseOrderLine,
    order: PurchaseOrder,
    warehouse_assortment: WarehouseAssortment,
    location: InventoryLocation,
) -> None:
    if route.assortment_id != line.assortment_id:
        raise ValueError("inbound route assortment does not match line")

    if route.product_id != line.product_id:
        raise ValueError("inbound route product does not match line")

    if route.sku != line.sku:
        raise ValueError("inbound route SKU does not match line")

    if route.market_code != order.market_code:
        raise ValueError("inbound route market does not match purchase order")

    if warehouse_assortment.assortment_id != line.assortment_id:
        raise ValueError("warehouse assortment does not match purchase order line")

    if warehouse_assortment.product_id != line.product_id:
        raise ValueError("warehouse assortment product does not match line")

    if warehouse_assortment.sku != line.sku:
        raise ValueError("warehouse assortment SKU does not match line")

    if warehouse_assortment.market_code != route.market_code:
        raise ValueError("warehouse assortment market does not match route")

    if route.warehouse_id != warehouse_assortment.warehouse_id:
        raise ValueError("inbound route warehouse does not match warehouse assortment")

    if route.warehouse_code != warehouse_assortment.warehouse_code:
        raise ValueError("inbound route warehouse code does not match warehouse assortment")

    if location.warehouse_id != route.warehouse_id:
        raise ValueError("receiving location does not belong to routed warehouse")

    if location.location_code != route.location_code:
        raise ValueError("inbound route location code does not match location")

    if location.location_type != "RECEIVING":
        raise ValueError("inbound route must target RECEIVING location")

    if not location.accepts_receipts:
        raise ValueError("inbound route location does not accept receipts")
