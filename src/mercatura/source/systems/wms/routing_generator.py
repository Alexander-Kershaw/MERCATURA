import random
from collections import defaultdict

from mercatura.source.simulation import (
    SimulationContext,
)
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


def generate_inbound_receipt_routes(
    context: SimulationContext,
    orders: tuple[PurchaseOrder, ...],
    lines: tuple[PurchaseOrderLine, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    locations: tuple[InventoryLocation, ...],
) -> tuple[InboundReceiptRoute, ...]:
    orders_by_id: dict[str, PurchaseOrder] = {order.purchase_order_id: order for order in orders}

    stock_by_assortment: dict[
        str,
        list[WarehouseAssortment],
    ] = defaultdict(list)

    for row in warehouse_assortments:
        stock_by_assortment[row.assortment_id].append(row)

    receiving_by_warehouse: dict[str, InventoryLocation] = {
        location.warehouse_id: location
        for location in locations
        if (location.location_type == "RECEIVING")
    }

    routes: list[InboundReceiptRoute] = []

    for line in sorted(
        lines,
        key=lambda row: row.purchase_order_line_id,
    ):
        order: PurchaseOrder = orders_by_id[line.purchase_order_id]

        candidates: list[WarehouseAssortment] = [
            row
            for row in stock_by_assortment[line.assortment_id]
            if (row.is_active_on(value=order.order_date))
        ]

        if not candidates:
            raise ValueError(
                f"no active warehouse assortment for PO line {line.purchase_order_line_id}"
            )

        selected: WarehouseAssortment = _select_inbound_warehouse(
            context=context,
            line=line,
            candidates=candidates,
        )

        receiving: InventoryLocation | None = receiving_by_warehouse.get(selected.warehouse_id)

        if receiving is None:
            raise ValueError(f"{selected.warehouse_code} has no receiving location")

        stable_key: str = line.purchase_order_line_id

        route_id: str = context.ids.id_for(
            namespace="inbound_receipt_route",
            key=stable_key,
            prefix="irt",
        )

        routes.append(
            InboundReceiptRoute(
                route_id=route_id,
                purchase_order_id=(line.purchase_order_id),
                purchase_order_line_id=(line.purchase_order_line_id),
                assortment_id=(line.assortment_id),
                product_id=(line.product_id),
                sku=line.sku,
                market_code=(order.market_code),
                warehouse_assortment_id=(selected.warehouse_assortment_id),
                warehouse_id=(selected.warehouse_id),
                warehouse_code=(selected.warehouse_code),
                inventory_location_id=(receiving.inventory_location_id),
                location_code=(receiving.location_code),
            )
        )

    return tuple(routes)


def _select_inbound_warehouse(
    *,
    context: SimulationContext,
    line: PurchaseOrderLine,
    candidates: list[WarehouseAssortment],
) -> WarehouseAssortment:
    ordered: list[WarehouseAssortment] = sorted(
        candidates,
        key=lambda row: (
            row.stocking_priority,
            row.warehouse_code,
        ),
    )

    if len(ordered) == 1:
        return ordered[0]

    rng = random.Random(
        x=context.seed_for(namespace=(f"wms:inbound-route:{line.purchase_order_line_id}"))
    )

    weights: list[float] = [1.0 / float(row.stocking_priority) for row in ordered]

    return rng.choices(
        population=ordered,
        weights=weights,
        k=1,
    )[0]
