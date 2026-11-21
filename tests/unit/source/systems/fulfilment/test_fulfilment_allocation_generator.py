from dataclasses import dataclass
from datetime import date
from typing import cast

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.fulfilment.generator import (
    generate_fulfilment_allocations,
)
from mercatura.source.systems.fulfilment.model import (
    FulfilmentAllocation,
    FulfilmentRequest,
)
from mercatura.source.systems.oms.model import (
    Order,
    OrderItem,
)
from mercatura.source.systems.wms.assortment_model import (
    WarehouseAssortment,
)
from mercatura.source.systems.wms.inventory_model import (
    InventoryMovement,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
)

SIMULATION_START = date(
    2024,
    1,
    1,
)

SIMULATION_END = date(
    2026,
    12,
    31,
)

DEFAULT_ORDER_DATE = date(
    2024,
    6,
    15,
)


@dataclass(frozen=True, slots=True)
class _OrderStub:
    order_id: str
    order_number: str
    market_code: str
    channel: str
    order_date: date
    order_status: str


@dataclass(frozen=True, slots=True)
class _OrderItemStub:
    order_item_id: str
    order_id: str
    line_number: int
    assortment_id: str
    product_id: str
    sku: str
    quantity: int


@dataclass(frozen=True, slots=True)
class _WarehouseAssortmentStub:
    warehouse_assortment_id: str
    assortment_id: str
    product_id: str
    sku: str
    market_code: str
    warehouse_id: str
    warehouse_code: str
    stocking_priority: int
    stocked_from: date
    stocked_to: date | None


@dataclass(frozen=True, slots=True)
class _InventoryMovementStub:
    movement_id: str
    inventory_location_id: str
    warehouse_id: str
    assortment_id: str
    quantity_delta: int
    event_date: date


@dataclass(frozen=True, slots=True)
class _InventoryLocationStub:
    inventory_location_id: str
    is_sellable: bool


def _context() -> SimulationContext:
    return SimulationContext.create(
        SimulationConfig(
            start_date=SIMULATION_START,
            end_date=SIMULATION_END,
            seed=42,
        )
    )


def _order(
    *,
    order_id: str = "ord_001",
    order_number: str = "ORD-001",
    market_code: str = "GB",
    channel: str = "WEB",
    order_date: date = DEFAULT_ORDER_DATE,
    order_status: str = "CONFIRMED",
) -> Order:
    return cast(
        Order,
        _OrderStub(
            order_id=order_id,
            order_number=order_number,
            market_code=market_code,
            channel=channel,
            order_date=order_date,
            order_status=order_status,
        ),
    )


def _item(
    *,
    order_item_id: str = "itm_001",
    order_id: str = "ord_001",
    line_number: int = 1,
    assortment_id: str = "ast_001",
    product_id: str = "prd_001",
    sku: str = "SKU-001",
    quantity: int = 2,
) -> OrderItem:
    return cast(
        OrderItem,
        _OrderItemStub(
            order_item_id=order_item_id,
            order_id=order_id,
            line_number=line_number,
            assortment_id=assortment_id,
            product_id=product_id,
            sku=sku,
            quantity=quantity,
        ),
    )


def _warehouse_assortment(
    *,
    warehouse_assortment_id: str = "was_001",
    assortment_id: str = "ast_001",
    product_id: str = "prd_001",
    sku: str = "SKU-001",
    market_code: str = "GB",
    warehouse_id: str = "wh_001",
    warehouse_code: str = "GB-WH-001",
    stocking_priority: int = 1,
    stocked_from: date = SIMULATION_START,
    stocked_to: date | None = None,
) -> WarehouseAssortment:
    return cast(
        WarehouseAssortment,
        _WarehouseAssortmentStub(
            warehouse_assortment_id=(warehouse_assortment_id),
            assortment_id=assortment_id,
            product_id=product_id,
            sku=sku,
            market_code=market_code,
            warehouse_id=warehouse_id,
            warehouse_code=warehouse_code,
            stocking_priority=(stocking_priority),
            stocked_from=stocked_from,
            stocked_to=stocked_to,
        ),
    )


def _movement(
    *,
    movement_id: str = "mov_001",
    inventory_location_id: str = "loc_001",
    warehouse_id: str = "wh_001",
    assortment_id: str = "ast_001",
    quantity_delta: int = 10,
    event_date: date = SIMULATION_START,
) -> InventoryMovement:
    return cast(
        InventoryMovement,
        _InventoryMovementStub(
            movement_id=movement_id,
            inventory_location_id=(inventory_location_id),
            warehouse_id=warehouse_id,
            assortment_id=assortment_id,
            quantity_delta=quantity_delta,
            event_date=event_date,
        ),
    )


def _location(
    *,
    inventory_location_id: str = "loc_001",
    is_sellable: bool = True,
) -> InventoryLocation:
    return cast(
        InventoryLocation,
        _InventoryLocationStub(
            inventory_location_id=(inventory_location_id),
            is_sellable=is_sellable,
        ),
    )


def _generate(
    *,
    orders: tuple[Order, ...] | None = None,
    items: tuple[OrderItem, ...] | None = None,
    warehouse_assortments: tuple[WarehouseAssortment, ...] | None = None,
    movements: tuple[InventoryMovement, ...] | None = None,
    locations: tuple[InventoryLocation, ...] | None = None,
) -> tuple[
    tuple[FulfilmentRequest, ...],
    tuple[FulfilmentAllocation, ...],
]:
    return generate_fulfilment_allocations(
        context=_context(),
        orders=(orders if orders is not None else (_order(),)),
        order_items=(items if items is not None else (_item(),)),
        warehouse_assortments=(
            warehouse_assortments
            if warehouse_assortments is not None
            else (_warehouse_assortment(),)
        ),
        inventory_movements=(movements if movements is not None else (_movement(),)),
        locations=(locations if locations is not None else (_location(),)),
    )


def test_confirmed_web_item_creates_request() -> None:
    requests, allocations = _generate()

    assert len(requests) == 1
    assert len(allocations) == 1

    request = requests[0]

    assert request.order_id == "ord_001"
    assert request.order_item_id == "itm_001"
    assert request.channel == "WEB"


def test_confirmed_mobile_item_creates_request() -> None:
    requests, _ = _generate(
        orders=(
            _order(
                channel="MOBILE",
            ),
        )
    )

    assert len(requests) == 1
    assert requests[0].channel == "MOBILE"


def test_store_order_does_not_create_fulfilment_request() -> None:
    requests, allocations = _generate(
        orders=(
            _order(
                channel="STORE",
            ),
        )
    )

    assert requests == ()
    assert allocations == ()


def test_cancelled_order_does_not_create_fulfilment_request() -> None:
    requests, allocations = _generate(
        orders=(
            _order(
                order_status="CANCELLED",
            ),
        )
    )

    assert requests == ()
    assert allocations == ()


def test_one_request_is_created_per_eligible_order_item() -> None:
    items = (
        _item(
            order_item_id="itm_001",
            line_number=1,
            quantity=1,
        ),
        _item(
            order_item_id="itm_002",
            line_number=2,
            quantity=1,
        ),
        _item(
            order_item_id="itm_003",
            line_number=3,
            quantity=1,
        ),
    )

    requests, _ = _generate(items=items)

    assert len(requests) == 3

    assert {request.order_item_id for request in requests} == {
        "itm_001",
        "itm_002",
        "itm_003",
    }


def test_request_is_fully_allocated_when_stock_is_sufficient() -> None:
    requests, allocations = _generate(
        items=(
            _item(
                quantity=4,
            ),
        ),
        movements=(
            _movement(
                quantity_delta=10,
            ),
        ),
    )

    assert len(requests) == 1
    assert len(allocations) == 1

    request = requests[0]

    assert request.requested_quantity == 4

    assert request.allocated_quantity == 4

    assert request.unallocated_quantity == 0

    assert request.allocation_status == "ALLOCATED"

    assert allocations[0].allocated_quantity == 4


def test_request_is_partially_allocated_when_stock_is_insufficient() -> None:
    requests, allocations = _generate(
        items=(
            _item(
                quantity=5,
            ),
        ),
        movements=(
            _movement(
                quantity_delta=3,
            ),
        ),
    )

    request = requests[0]

    assert request.requested_quantity == 5

    assert request.allocated_quantity == 3

    assert request.unallocated_quantity == 2

    assert request.allocation_status == "PARTIALLY_ALLOCATED"

    assert sum(allocation.allocated_quantity for allocation in allocations) == 3


def test_request_is_backordered_when_no_stock_is_available() -> None:
    requests, allocations = _generate(movements=())

    assert len(requests) == 1
    assert allocations == ()

    request = requests[0]

    assert request.allocated_quantity == 0

    assert request.unallocated_quantity == request.requested_quantity

    assert request.allocation_status == "BACKORDERED"


def test_highest_priority_warehouse_is_used_first() -> None:
    warehouse_assortments = (
        _warehouse_assortment(
            warehouse_assortment_id=("was_priority_2"),
            warehouse_id="wh_002",
            warehouse_code="GB-WH-002",
            stocking_priority=2,
        ),
        _warehouse_assortment(
            warehouse_assortment_id=("was_priority_1"),
            warehouse_id="wh_001",
            warehouse_code="GB-WH-001",
            stocking_priority=1,
        ),
    )

    movements = (
        _movement(
            movement_id="mov_wh_001",
            warehouse_id="wh_001",
            inventory_location_id=("loc_001"),
            quantity_delta=10,
        ),
        _movement(
            movement_id="mov_wh_002",
            warehouse_id="wh_002",
            inventory_location_id=("loc_002"),
            quantity_delta=10,
        ),
    )

    locations = (
        _location(
            inventory_location_id=("loc_001"),
        ),
        _location(
            inventory_location_id=("loc_002"),
        ),
    )

    _, allocations = _generate(
        items=(
            _item(
                quantity=3,
            ),
        ),
        warehouse_assortments=(warehouse_assortments),
        movements=movements,
        locations=locations,
    )

    assert len(allocations) == 1

    assert allocations[0].warehouse_id == "wh_001"

    assert allocations[0].warehouse_assortment_id == "was_priority_1"


def test_request_can_split_across_multiple_warehouses() -> None:
    warehouse_assortments = (
        _warehouse_assortment(
            warehouse_assortment_id=("was_001"),
            warehouse_id="wh_001",
            warehouse_code="GB-WH-001",
            stocking_priority=1,
        ),
        _warehouse_assortment(
            warehouse_assortment_id=("was_002"),
            warehouse_id="wh_002",
            warehouse_code="GB-WH-002",
            stocking_priority=2,
        ),
    )

    movements = (
        _movement(
            movement_id="mov_001",
            inventory_location_id=("loc_001"),
            warehouse_id="wh_001",
            quantity_delta=3,
        ),
        _movement(
            movement_id="mov_002",
            inventory_location_id=("loc_002"),
            warehouse_id="wh_002",
            quantity_delta=5,
        ),
    )

    locations = (
        _location(
            inventory_location_id=("loc_001"),
        ),
        _location(
            inventory_location_id=("loc_002"),
        ),
    )

    requests, allocations = _generate(
        items=(
            _item(
                quantity=5,
            ),
        ),
        warehouse_assortments=(warehouse_assortments),
        movements=movements,
        locations=locations,
    )

    assert len(requests) == 1
    assert len(allocations) == 2

    request = requests[0]

    assert request.allocation_status == "ALLOCATED"

    assert request.allocated_quantity == 5

    assert [allocation.allocated_quantity for allocation in allocations] == [
        3,
        2,
    ]

    assert [allocation.allocation_sequence for allocation in allocations] == [
        1,
        2,
    ]

    assert [allocation.warehouse_id for allocation in allocations] == [
        "wh_001",
        "wh_002",
    ]


def test_allocation_does_not_double_allocate_inventory() -> None:
    orders = (
        _order(
            order_id="ord_001",
            order_number="ORD-001",
        ),
        _order(
            order_id="ord_002",
            order_number="ORD-002",
        ),
    )

    items = (
        _item(
            order_item_id="itm_001",
            order_id="ord_001",
            quantity=4,
        ),
        _item(
            order_item_id="itm_002",
            order_id="ord_002",
            quantity=4,
        ),
    )

    requests, allocations = _generate(
        orders=orders,
        items=items,
        movements=(
            _movement(
                quantity_delta=5,
            ),
        ),
    )

    requests_by_item = {request.order_item_id: request for request in requests}

    first = requests_by_item["itm_001"]

    second = requests_by_item["itm_002"]

    assert first.allocated_quantity == 4

    assert first.allocation_status == "ALLOCATED"

    assert second.allocated_quantity == 1

    assert second.unallocated_quantity == 3

    assert second.allocation_status == "PARTIALLY_ALLOCATED"

    assert sum(allocation.allocated_quantity for allocation in allocations) == 5


def test_same_day_sellable_stock_is_available_for_allocation() -> None:
    order_date = date(
        2024,
        7,
        10,
    )

    requests, _ = _generate(
        orders=(
            _order(
                order_date=order_date,
            ),
        ),
        movements=(
            _movement(
                quantity_delta=5,
                event_date=order_date,
            ),
        ),
    )

    assert requests[0].allocation_status == "ALLOCATED"


def test_future_stock_is_not_available_for_earlier_order() -> None:
    requests, allocations = _generate(
        orders=(
            _order(
                order_date=date(
                    2024,
                    7,
                    10,
                ),
            ),
        ),
        movements=(
            _movement(
                quantity_delta=10,
                event_date=date(
                    2024,
                    7,
                    11,
                ),
            ),
        ),
    )

    assert allocations == ()

    assert requests[0].allocation_status == "BACKORDERED"


def test_non_sellable_location_stock_is_not_allocated() -> None:
    requests, allocations = _generate(
        movements=(
            _movement(
                inventory_location_id=("loc_receiving"),
                quantity_delta=10,
            ),
        ),
        locations=(
            _location(
                inventory_location_id=("loc_receiving"),
                is_sellable=False,
            ),
        ),
    )

    assert allocations == ()

    assert requests[0].allocation_status == "BACKORDERED"


def test_future_warehouse_assortment_is_not_eligible() -> None:
    requests, allocations = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                stocked_from=date(
                    2024,
                    6,
                    16,
                ),
            ),
        ),
        movements=(
            _movement(
                quantity_delta=10,
            ),
        ),
    )

    assert allocations == ()

    assert requests[0].allocation_status == "BACKORDERED"


def test_expired_warehouse_assortment_is_not_eligible() -> None:
    requests, allocations = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                stocked_from=(SIMULATION_START),
                stocked_to=date(
                    2024,
                    6,
                    15,
                ),
            ),
        ),
        movements=(
            _movement(
                quantity_delta=10,
            ),
        ),
    )

    assert allocations == ()

    assert requests[0].allocation_status == "BACKORDERED"


def test_active_warehouse_assortment_is_eligible() -> None:
    requests, allocations = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                stocked_from=date(
                    2024,
                    1,
                    1,
                ),
                stocked_to=date(
                    2024,
                    6,
                    16,
                ),
            ),
        ),
        movements=(
            _movement(
                quantity_delta=10,
            ),
        ),
    )

    assert len(allocations) == 1

    assert requests[0].allocation_status == "ALLOCATED"


def test_cross_market_warehouse_is_not_eligible() -> None:
    requests, allocations = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                market_code="US",
            ),
        ),
        movements=(
            _movement(
                quantity_delta=10,
            ),
        ),
    )

    assert allocations == ()

    assert requests[0].allocation_status == "BACKORDERED"


def test_allocation_metadata_matches_order_item_and_warehouse() -> None:
    requests, allocations = _generate()

    request = requests[0]
    allocation = allocations[0]

    assert request.order_id == "ord_001"

    assert request.order_item_id == "itm_001"

    assert request.assortment_id == "ast_001"

    assert request.product_id == "prd_001"

    assert request.sku == "SKU-001"

    assert allocation.order_id == "ord_001"

    assert allocation.order_item_id == "itm_001"

    assert allocation.assortment_id == "ast_001"

    assert allocation.product_id == "prd_001"

    assert allocation.sku == "SKU-001"

    assert allocation.market_code == "GB"

    assert allocation.warehouse_id == "wh_001"


def test_request_quantities_reconcile() -> None:
    requests, allocations = _generate(
        items=(
            _item(
                quantity=5,
            ),
        ),
        movements=(
            _movement(
                quantity_delta=3,
            ),
        ),
    )

    request = requests[0]

    assert request.requested_quantity == (request.allocated_quantity + request.unallocated_quantity)

    assert request.allocated_quantity == sum(
        allocation.allocated_quantity for allocation in allocations
    )


def test_allocation_quantities_are_positive() -> None:
    _, allocations = _generate(
        items=(
            _item(
                quantity=8,
            ),
        ),
        movements=(
            _movement(
                quantity_delta=3,
            ),
        ),
    )

    assert all(allocation.allocated_quantity > 0 for allocation in allocations)


def test_request_ids_are_unique() -> None:
    items = (
        _item(
            order_item_id="itm_001",
            line_number=1,
            quantity=1,
        ),
        _item(
            order_item_id="itm_002",
            line_number=2,
            quantity=1,
        ),
    )

    requests, _ = _generate(items=items)

    ids = [request.fulfilment_request_id for request in requests]

    assert len(ids) == len(set(ids))


def test_allocation_ids_are_unique() -> None:
    warehouse_assortments = (
        _warehouse_assortment(
            warehouse_assortment_id=("was_001"),
            warehouse_id="wh_001",
            warehouse_code="GB-WH-001",
            stocking_priority=1,
        ),
        _warehouse_assortment(
            warehouse_assortment_id=("was_002"),
            warehouse_id="wh_002",
            warehouse_code="GB-WH-002",
            stocking_priority=2,
        ),
    )

    movements = (
        _movement(
            movement_id="mov_001",
            inventory_location_id=("loc_001"),
            warehouse_id="wh_001",
            quantity_delta=1,
        ),
        _movement(
            movement_id="mov_002",
            inventory_location_id=("loc_002"),
            warehouse_id="wh_002",
            quantity_delta=10,
        ),
    )

    locations = (
        _location(
            inventory_location_id=("loc_001"),
        ),
        _location(
            inventory_location_id=("loc_002"),
        ),
    )

    _, allocations = _generate(
        items=(
            _item(
                quantity=4,
            ),
        ),
        warehouse_assortments=(warehouse_assortments),
        movements=movements,
        locations=locations,
    )

    ids = [allocation.allocation_id for allocation in allocations]

    assert len(ids) == len(set(ids))


def test_generation_is_deterministic() -> None:
    first = _generate()
    second = _generate()

    assert first == second


def test_order_input_order_does_not_change_results() -> None:
    orders = (
        _order(
            order_id="ord_001",
            order_number="ORD-001",
        ),
        _order(
            order_id="ord_002",
            order_number="ORD-002",
        ),
    )

    items = (
        _item(
            order_item_id="itm_001",
            order_id="ord_001",
            quantity=2,
        ),
        _item(
            order_item_id="itm_002",
            order_id="ord_002",
            quantity=2,
        ),
    )

    first = _generate(
        orders=orders,
        items=items,
    )

    second = _generate(
        orders=tuple(reversed(orders)),
        items=tuple(reversed(items)),
    )

    assert first == second


def test_warehouse_assortment_input_order_does_not_change_results() -> None:
    warehouse_assortments = (
        _warehouse_assortment(
            warehouse_assortment_id=("was_001"),
            warehouse_id="wh_001",
            warehouse_code="GB-WH-001",
            stocking_priority=1,
        ),
        _warehouse_assortment(
            warehouse_assortment_id=("was_002"),
            warehouse_id="wh_002",
            warehouse_code="GB-WH-002",
            stocking_priority=2,
        ),
    )

    movements = (
        _movement(
            movement_id="mov_001",
            inventory_location_id=("loc_001"),
            warehouse_id="wh_001",
            quantity_delta=1,
        ),
        _movement(
            movement_id="mov_002",
            inventory_location_id=("loc_002"),
            warehouse_id="wh_002",
            quantity_delta=10,
        ),
    )

    locations = (
        _location(
            inventory_location_id=("loc_001"),
        ),
        _location(
            inventory_location_id=("loc_002"),
        ),
    )

    first = _generate(
        items=(
            _item(
                quantity=4,
            ),
        ),
        warehouse_assortments=(warehouse_assortments),
        movements=movements,
        locations=locations,
    )

    second = _generate(
        items=(
            _item(
                quantity=4,
            ),
        ),
        warehouse_assortments=tuple(reversed(warehouse_assortments)),
        movements=tuple(reversed(movements)),
        locations=tuple(reversed(locations)),
    )

    assert first == second
