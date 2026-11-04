from collections import Counter

from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrderLine,
)
from mercatura.source.systems.wms.assortment_model import WarehouseAssortment
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)
from mercatura.source.systems.wms.routing_model import (
    InboundReceiptRoute,
)


def test_one_route_per_po_line(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    purchase_order_lines: tuple[PurchaseOrderLine, ...],
) -> None:
    assert len(inbound_routes) == len(purchase_order_lines)

    assert {row.purchase_order_line_id for row in inbound_routes} == {
        row.purchase_order_line_id for row in purchase_order_lines
    }


def test_route_ids_are_unique(
    inbound_routes: tuple[InboundReceiptRoute, ...],
) -> None:
    identifiers: list[str] = [row.route_id for row in inbound_routes]

    assert len(identifiers) == len(set(identifiers))


def test_every_route_targets_receiving(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    inventory_locations: tuple[InventoryLocation, ...],
) -> None:
    locations_by_id: dict[str, InventoryLocation] = {
        row.inventory_location_id: row for row in inventory_locations
    }

    for route in inbound_routes:
        location: InventoryLocation = locations_by_id[route.inventory_location_id]

        assert location.location_type == "RECEIVING"

        assert location.accepts_receipts


def test_primary_stocking_locations_receive_more_routes(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    rows_by_id: dict[str, WarehouseAssortment] = {
        row.warehouse_assortment_id: row for row in warehouse_assortments
    }

    priorities: Counter[int] = Counter(
        rows_by_id[route.warehouse_assortment_id].stocking_priority for route in inbound_routes
    )

    assert priorities[1] > priorities[2]


def test_secondary_stocking_routes_exist(
    inbound_routes: tuple[InboundReceiptRoute, ...],
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    rows_by_id: dict[str, WarehouseAssortment] = {
        row.warehouse_assortment_id: row for row in warehouse_assortments
    }

    assert any(
        rows_by_id[route.warehouse_assortment_id].stocking_priority > 1 for route in inbound_routes
    )
