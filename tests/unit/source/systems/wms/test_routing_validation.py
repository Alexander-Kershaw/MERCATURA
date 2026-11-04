from dataclasses import replace
from datetime import timedelta

import pytest

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
from mercatura.source.systems.wms.routing_validation import (
    validate_inbound_receipt_routes,
)


def replace_route(
    routes: tuple[InboundReceiptRoute, ...],
    replacement: InboundReceiptRoute,
) -> tuple[InboundReceiptRoute, ...]:
    return tuple(
        replacement if route.route_id == replacement.route_id else route for route in routes
    )


def replace_warehouse_assortment(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    replacement: WarehouseAssortment,
) -> tuple[WarehouseAssortment, ...]:
    return tuple(
        replacement if row.warehouse_assortment_id == replacement.warehouse_assortment_id else row
        for row in warehouse_assortments
    )


def replace_location(
    locations: tuple[InventoryLocation, ...],
    replacement: InventoryLocation,
) -> tuple[InventoryLocation, ...]:
    return tuple(
        replacement
        if location.inventory_location_id == replacement.inventory_location_id
        else location
        for location in locations
    )


def validate(
    *,
    routes: tuple[InboundReceiptRoute, ...],
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    locations: tuple[InventoryLocation, ...],
) -> None:
    validate_inbound_receipt_routes(
        routes,
        orders,
        lines,
        warehouse_assortments,
        locations,
    )


def test_valid_routes_pass_validation(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    validate(
        routes=inbound_routes,
        orders=purchase_orders,
        lines=purchase_order_lines,
        warehouse_assortments=(warehouse_assortments),
        locations=inventory_locations,
    )


def test_rejects_duplicate_route_id(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    broken = (
        *inbound_routes,
        inbound_routes[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate inbound route_id",
    ):
        validate(
            routes=broken,
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_multiple_routes_for_same_po_line(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    duplicate = replace(
        inbound_routes[0],
        route_id="irt_duplicate",
    )

    broken = (
        *inbound_routes,
        duplicate,
    )

    with pytest.raises(
        ValueError,
        match="multiple inbound routes",
    ):
        validate(
            routes=broken,
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_missing_route(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    broken = inbound_routes[1:]

    with pytest.raises(
        ValueError,
        match="do not cover every purchase order line",
    ):
        validate(
            routes=broken,
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_unknown_po_line_via_coverage_check(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        purchase_order_line_id="pol_missing",
    )

    broken = replace_route(
        inbound_routes,
        broken_route,
    )

    with pytest.raises(
        ValueError,
        match="do not cover every purchase order line",
    ):
        validate(
            routes=broken,
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_unknown_purchase_order(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        purchase_order_id="po_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown purchase order",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_purchase_order_mismatch(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    alternative_order = next(
        order for order in purchase_orders if (order.purchase_order_id != target.purchase_order_id)
    )

    broken_route = replace(
        target,
        purchase_order_id=(alternative_order.purchase_order_id),
    )

    with pytest.raises(
        ValueError,
        match="does not match line",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_unknown_warehouse_assortment(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        warehouse_assortment_id=("wha_missing"),
    )

    with pytest.raises(
        ValueError,
        match="unknown warehouse assortment",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_wrong_route_assortment(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        assortment_id="ast_wrong",
    )

    with pytest.raises(
        ValueError,
        match="route assortment does not match line",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_wrong_route_product(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        product_id="prd_wrong",
    )

    with pytest.raises(
        ValueError,
        match="route product does not match line",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_wrong_route_sku(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        sku="MRC-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="route SKU does not match line",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_wrong_route_market(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        market_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="route market does not match purchase order",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_warehouse_assortment_for_wrong_po_line(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    alternative = next(
        row for row in warehouse_assortments if (row.assortment_id != target.assortment_id)
    )

    broken_route = replace(
        target,
        warehouse_assortment_id=(alternative.warehouse_assortment_id),
    )

    with pytest.raises(
        ValueError,
        match="warehouse assortment does not match purchase order line",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_route_warehouse_id_mismatch(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    alternative_location = next(
        location
        for location in inventory_locations
        if (location.warehouse_id != target.warehouse_id)
    )

    broken_route = replace(
        target,
        warehouse_id=(alternative_location.warehouse_id),
    )

    with pytest.raises(
        ValueError,
        match="route warehouse does not match warehouse assortment",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_route_warehouse_code_mismatch(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        warehouse_code="WH-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="warehouse code does not match warehouse assortment",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_unknown_inventory_location(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        inventory_location_id="loc_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown inventory location",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_location_from_another_warehouse(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    alternative = next(
        location
        for location in inventory_locations
        if (location.warehouse_id != target.warehouse_id and location.location_type == "RECEIVING")
    )

    broken_route = replace(
        target,
        inventory_location_id=(alternative.inventory_location_id),
        location_code=(alternative.location_code),
    )

    with pytest.raises(
        ValueError,
        match="does not belong to routed warehouse",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_location_code_mismatch(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    broken_route = replace(
        target,
        location_code="WH-WRONG-RCV",
    )

    with pytest.raises(
        ValueError,
        match="location code does not match location",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_non_receiving_location(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    alternative = next(
        location
        for location in inventory_locations
        if (location.warehouse_id == target.warehouse_id and location.location_type == "PICK_FACE")
    )

    broken_route = replace(
        target,
        inventory_location_id=(alternative.inventory_location_id),
        location_code=(alternative.location_code),
    )

    with pytest.raises(
        ValueError,
        match="must target RECEIVING location",
    ):
        validate(
            routes=replace_route(
                inbound_routes,
                broken_route,
            ),
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=inventory_locations,
        )


def test_rejects_receiving_location_that_does_not_accept_receipts(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    location = next(
        row
        for row in inventory_locations
        if (row.inventory_location_id == target.inventory_location_id)
    )

    broken_location = replace(
        location,
        accepts_receipts=False,
    )

    broken_locations = replace_location(
        inventory_locations,
        broken_location,
    )

    with pytest.raises(
        ValueError,
        match="does not accept receipts",
    ):
        validate(
            routes=inbound_routes,
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(warehouse_assortments),
            locations=broken_locations,
        )


def test_rejects_inactive_warehouse_assortment_on_po_date(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_orders: tuple[PurchaseOrder, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    target = inbound_routes[0]

    order = next(
        row for row in purchase_orders if (row.purchase_order_id == target.purchase_order_id)
    )

    warehouse_assortment = next(
        row
        for row in warehouse_assortments
        if (row.warehouse_assortment_id == target.warehouse_assortment_id)
    )

    broken_warehouse_assortment = replace(
        warehouse_assortment,
        stocked_from=(order.order_date + timedelta(days=1)),
    )

    broken_assortments = replace_warehouse_assortment(
        warehouse_assortments,
        broken_warehouse_assortment,
    )

    with pytest.raises(
        ValueError,
        match="not active on purchase order date",
    ):
        validate(
            routes=inbound_routes,
            orders=purchase_orders,
            lines=purchase_order_lines,
            warehouse_assortments=(broken_assortments),
            locations=inventory_locations,
        )


def test_cancelled_po_lines_still_have_planned_routes(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    route_line_ids = {route.purchase_order_line_id for route in inbound_routes}

    line_ids = {line.purchase_order_line_id for line in purchase_order_lines}

    assert route_line_ids == line_ids
