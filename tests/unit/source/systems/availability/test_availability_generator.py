from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import cast

import pytest

from mercatura.source.systems.availability.config import (
    DEFAULT_AVAILABILITY_CONFIG,
    AvailabilitySimulationConfig,
)
from mercatura.source.systems.availability.generator import (
    DemandProfileLike,
    generate_availability_snapshots,
)
from mercatura.source.systems.availability.model import AvailabilitySnapshot
from mercatura.source.systems.availability.validation import (
    validate_availability_snapshots,
)
from mercatura.source.systems.fulfilment.reservation_model import (
    InventoryReservation,
    ReservationStatus,
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

SNAPSHOT_DATE = date(
    2026,
    6,
    30,
)


@dataclass(
    frozen=True,
    slots=True,
)
class _DemandProfileStub:
    market_code: str
    assortment_id: str
    product_id: str
    sku: str
    average_daily_units: Decimal


@dataclass(
    frozen=True,
    slots=True,
)
class _WarehouseAssortmentStub:
    market_code: str
    assortment_id: str
    warehouse_id: str
    stocked_from: date
    stocked_to: date | None


@dataclass(
    frozen=True,
    slots=True,
)
class _LocationStub:
    inventory_location_id: str
    warehouse_id: str
    is_sellable: bool


@dataclass(
    frozen=True,
    slots=True,
)
class _MovementStub:
    movement_id: str
    market_code: str
    assortment_id: str
    inventory_location_id: str
    quantity_delta: int
    event_date: date


def _profile(
    *,
    market_code: str = "GB",
    assortment_id: str = "ast_001",
    product_id: str = "prd_001",
    sku: str = "SKU-001",
    average_daily_units: Decimal = Decimal("10.00"),
) -> DemandProfileLike:
    return _DemandProfileStub(
        market_code=market_code,
        assortment_id=assortment_id,
        product_id=product_id,
        sku=sku,
        average_daily_units=(average_daily_units),
    )


def _warehouse_assortment(
    *,
    market_code: str = "GB",
    assortment_id: str = "ast_001",
    warehouse_id: str = "wh_001",
    stocked_from: date = date(
        2024,
        1,
        1,
    ),
    stocked_to: date | None = None,
) -> WarehouseAssortment:
    return cast(
        WarehouseAssortment,
        _WarehouseAssortmentStub(
            market_code=market_code,
            assortment_id=assortment_id,
            warehouse_id=warehouse_id,
            stocked_from=stocked_from,
            stocked_to=stocked_to,
        ),
    )


def _location(
    *,
    inventory_location_id: str = "bulk_001",
    warehouse_id: str = "wh_001",
    is_sellable: bool = True,
) -> InventoryLocation:
    return cast(
        InventoryLocation,
        _LocationStub(
            inventory_location_id=(inventory_location_id),
            warehouse_id=warehouse_id,
            is_sellable=is_sellable,
        ),
    )


def _movement(
    *,
    movement_id: str = "imv_001",
    market_code: str = "GB",
    assortment_id: str = "ast_001",
    inventory_location_id: str = "bulk_001",
    quantity_delta: int = 100,
    event_date: date = date(
        2024,
        1,
        1,
    ),
) -> InventoryMovement:
    return cast(
        InventoryMovement,
        _MovementStub(
            movement_id=movement_id,
            market_code=market_code,
            assortment_id=assortment_id,
            inventory_location_id=(inventory_location_id),
            quantity_delta=quantity_delta,
            event_date=event_date,
        ),
    )


def _reservation(
    *,
    reservation_id: str = "res_001",
    reserved_quantity: int = 20,
    reserved_date: date = SNAPSHOT_DATE,
    released_date: date | None = None,
    consumed_date: date | None = None,
    status: ReservationStatus = "RESERVED",
) -> InventoryReservation:
    return InventoryReservation(
        reservation_id=reservation_id,
        allocation_id="alloc_001",
        fulfilment_request_id="req_001",
        order_id="ord_001",
        order_item_id="itm_001",
        market_code="GB",
        warehouse_assortment_id="was_001",
        warehouse_id="wh_001",
        warehouse_code="GB-WH-001",
        assortment_id="ast_001",
        product_id="prd_001",
        sku="SKU-001",
        reserved_quantity=(reserved_quantity),
        reservation_status=status,
        reserved_date=reserved_date,
        released_date=released_date,
        consumed_date=consumed_date,
    )


def _generate(
    *,
    profiles: tuple[
        DemandProfileLike,
        ...,
    ]
    | None = None,
    warehouse_assortments: tuple[
        WarehouseAssortment,
        ...,
    ]
    | None = None,
    movements: tuple[
        InventoryMovement,
        ...,
    ]
    | None = None,
    locations: tuple[
        InventoryLocation,
        ...,
    ]
    | None = None,
    reservations: tuple[
        InventoryReservation,
        ...,
    ] = (),
    config: AvailabilitySimulationConfig = DEFAULT_AVAILABILITY_CONFIG,
) -> tuple[AvailabilitySnapshot, ...]:
    return generate_availability_snapshots(
        snapshot_date=SNAPSHOT_DATE,
        demand_profiles=(profiles if profiles is not None else (_profile(),)),
        warehouse_assortments=(
            warehouse_assortments
            if warehouse_assortments is not None
            else (_warehouse_assortment(),)
        ),
        inventory_movements=(movements if movements is not None else (_movement(),)),
        locations=(locations if locations is not None else (_location(),)),
        reservations=reservations,
        config=config,
    )


def test_sellable_inventory_becomes_on_hand() -> None:
    snapshot = _generate()[0]

    assert snapshot.sellable_on_hand == 100


def test_active_reservation_reduces_atp() -> None:
    snapshot = _generate(
        reservations=(
            _reservation(
                reserved_quantity=20,
            ),
        ),
    )[0]

    assert snapshot.sellable_on_hand == 100

    assert snapshot.reserved_quantity == 20

    assert snapshot.available_to_promise == 80


def test_consumed_reservation_does_not_reduce_atp() -> None:
    snapshot = _generate(
        reservations=(
            _reservation(
                reserved_quantity=20,
                consumed_date=(SNAPSHOT_DATE),
                status="CONSUMED",
            ),
        ),
    )[0]

    assert snapshot.reserved_quantity == 0

    assert snapshot.available_to_promise == 100


def test_future_consumption_is_active_at_snapshot() -> None:
    snapshot = _generate(
        reservations=(
            _reservation(
                reserved_quantity=20,
                consumed_date=date(
                    2026,
                    7,
                    1,
                ),
                status="CONSUMED",
            ),
        ),
    )[0]

    assert snapshot.reserved_quantity == 20


def test_released_reservation_does_not_reduce_atp() -> None:
    snapshot = _generate(
        reservations=(
            _reservation(
                released_date=(SNAPSHOT_DATE),
                status="RELEASED",
            ),
        ),
    )[0]

    assert snapshot.reserved_quantity == 0


def test_future_reservation_is_not_active() -> None:
    snapshot = _generate(
        reservations=(
            _reservation(
                reserved_date=date(
                    2026,
                    7,
                    1,
                ),
            ),
        ),
    )[0]

    assert snapshot.reserved_quantity == 0


def test_non_sellable_inventory_is_excluded() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                movement_id="sellable",
                quantity_delta=100,
                inventory_location_id=("bulk_001"),
            ),
            _movement(
                movement_id="returns",
                quantity_delta=50,
                inventory_location_id=("returns_001"),
            ),
        ),
        locations=(
            _location(
                inventory_location_id=("bulk_001"),
                is_sellable=True,
            ),
            _location(
                inventory_location_id=("returns_001"),
                is_sellable=False,
            ),
        ),
    )[0]

    assert snapshot.sellable_on_hand == 100


def test_future_inventory_movement_is_excluded() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                quantity_delta=100,
            ),
            _movement(
                movement_id="future",
                quantity_delta=50,
                event_date=date(
                    2026,
                    7,
                    1,
                ),
            ),
        ),
    )[0]

    assert snapshot.sellable_on_hand == 100


def test_inventory_ledger_net_is_respected() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                movement_id="opening",
                quantity_delta=100,
            ),
            _movement(
                movement_id="pick-out",
                quantity_delta=-20,
            ),
            _movement(
                movement_id="pick-in",
                inventory_location_id=("pick_001"),
                quantity_delta=20,
            ),
            _movement(
                movement_id="dispatch",
                inventory_location_id=("pick_001"),
                quantity_delta=-20,
            ),
        ),
        locations=(
            _location(
                inventory_location_id=("bulk_001"),
            ),
            _location(
                inventory_location_id=("pick_001"),
            ),
        ),
    )[0]

    assert snapshot.sellable_on_hand == 80


def test_restocked_return_becomes_sellable() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                movement_id="opening",
                quantity_delta=100,
            ),
            _movement(
                movement_id="dispatch",
                quantity_delta=-20,
            ),
            _movement(
                movement_id="restock",
                quantity_delta=5,
            ),
        ),
    )[0]

    assert snapshot.sellable_on_hand == 85


def test_no_active_warehouse_means_unavailable() -> None:
    snapshot = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                stocked_to=SNAPSHOT_DATE,
            ),
        ),
    )[0]

    assert snapshot.availability_status == "UNAVAILABLE"

    assert snapshot.active_warehouse_count == 0

    assert snapshot.available_to_promise == 0

    assert snapshot.days_of_cover is None


def test_stocked_to_boundary_is_exclusive() -> None:
    snapshot = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                stocked_to=SNAPSHOT_DATE,
            ),
        ),
    )[0]

    assert snapshot.active_warehouse_count == 0


def test_future_warehouse_assortment_is_inactive() -> None:
    snapshot = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                stocked_from=date(
                    2026,
                    7,
                    1,
                ),
            ),
        ),
    )[0]

    assert snapshot.availability_status == "UNAVAILABLE"


def test_multiple_active_warehouses_are_counted() -> None:
    snapshot = _generate(
        warehouse_assortments=(
            _warehouse_assortment(
                warehouse_id="wh_001",
            ),
            _warehouse_assortment(
                warehouse_id="wh_002",
            ),
        ),
    )[0]

    assert snapshot.active_warehouse_count == 2


def test_zero_atp_is_out_of_stock() -> None:
    snapshot = _generate(
        reservations=(
            _reservation(
                reserved_quantity=100,
            ),
        ),
    )[0]

    assert snapshot.available_to_promise == 0

    assert snapshot.availability_status == "OUT_OF_STOCK"

    assert snapshot.days_of_cover == Decimal("0.00")


def test_low_stock_uses_days_of_cover() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                quantity_delta=50,
            ),
        ),
        profiles=(
            _profile(
                average_daily_units=(Decimal("10.00")),
            ),
        ),
    )[0]

    assert snapshot.days_of_cover == Decimal("5.00")

    assert snapshot.availability_status == "LOW_STOCK"


def test_in_stock_when_cover_meets_threshold() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                quantity_delta=70,
            ),
        ),
        profiles=(
            _profile(
                average_daily_units=(Decimal("10.00")),
            ),
        ),
    )[0]

    assert snapshot.days_of_cover == Decimal("7.00")

    assert snapshot.availability_status == "IN_STOCK"


def test_days_of_cover_is_decimal_and_rounded() -> None:
    snapshot = _generate(
        movements=(
            _movement(
                quantity_delta=10,
            ),
        ),
        profiles=(
            _profile(
                average_daily_units=(Decimal("3.00")),
            ),
        ),
    )[0]

    assert isinstance(
        snapshot.days_of_cover,
        Decimal,
    )

    assert snapshot.days_of_cover == Decimal("3.33")


def test_negative_sellable_balance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("sellable inventory balance cannot be negative"),
    ):
        _generate(
            movements=(
                _movement(
                    quantity_delta=-1,
                ),
            ),
        )


def test_reservations_cannot_exceed_physical_stock() -> None:
    with pytest.raises(
        ValueError,
        match=("active reservations exceed sellable physical inventory"),
    ):
        _generate(
            reservations=(
                _reservation(
                    reserved_quantity=101,
                ),
            ),
        )


def test_unknown_inventory_location_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("inventory movement references unknown inventory location"),
    ):
        _generate(
            movements=(
                _movement(
                    inventory_location_id=("missing"),
                ),
            ),
        )


def test_duplicate_demand_profile_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("duplicate demand profile for market assortment"),
    ):
        _generate(
            profiles=(
                _profile(),
                _profile(),
            ),
        )


def test_non_positive_demand_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("average daily demand must be positive"),
    ):
        _generate(
            profiles=(
                _profile(
                    average_daily_units=(Decimal("0")),
                ),
            ),
        )


def test_generation_is_deterministic() -> None:
    first = _generate(
        reservations=(_reservation(),),
    )

    second = _generate(
        reservations=(_reservation(),),
    )

    assert first == second


def test_input_order_does_not_change_results() -> None:
    movements = (
        _movement(
            movement_id="a",
            quantity_delta=100,
        ),
        _movement(
            movement_id="b",
            quantity_delta=-20,
        ),
    )

    first = _generate(
        movements=movements,
    )

    second = _generate(
        movements=tuple(reversed(movements)),
    )

    assert first == second


def test_generated_snapshots_pass_validation() -> None:
    profiles = (_profile(),)

    snapshots = _generate(
        profiles=profiles,
        reservations=(
            _reservation(
                reserved_quantity=20,
            ),
        ),
    )

    validate_availability_snapshots(
        snapshots,
        profiles,
    )


def test_validation_rejects_wrong_atp() -> None:
    profiles = (_profile(),)

    snapshots = _generate(
        profiles=profiles,
    )

    invalid = (
        replace(
            snapshots[0],
            available_to_promise=999,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("ATP does not reconcile"),
    ):
        validate_availability_snapshots(
            invalid,
            profiles,
        )


def test_config_rejects_non_positive_threshold() -> None:
    with pytest.raises(
        ValueError,
        match=("low_stock_days must be positive"),
    ):
        AvailabilitySimulationConfig(
            low_stock_days=Decimal("0"),
        )
