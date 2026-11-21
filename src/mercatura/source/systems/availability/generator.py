from collections import defaultdict
from datetime import date
from decimal import (
    ROUND_HALF_UP,
    Decimal,
)
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from mercatura.source.systems.availability.config import (
    DEFAULT_AVAILABILITY_CONFIG,
    AvailabilitySimulationConfig,
)
from mercatura.source.systems.availability.model import (
    AvailabilitySnapshot,
    AvailabilityStatus,
)
from mercatura.source.systems.fulfilment.reservation_model import (
    InventoryReservation,
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


class DemandProfileLike(Protocol):
    @property
    def market_code(self) -> str: ...

    @property
    def assortment_id(self) -> str: ...

    @property
    def product_id(self) -> str: ...

    @property
    def sku(self) -> str: ...

    @property
    def average_daily_units(self) -> Decimal: ...


def generate_availability_snapshots(
    *,
    snapshot_date: date,
    demand_profiles: tuple[
        DemandProfileLike,
        ...,
    ],
    warehouse_assortments: tuple[
        WarehouseAssortment,
        ...,
    ],
    inventory_movements: tuple[
        InventoryMovement,
        ...,
    ],
    locations: tuple[
        InventoryLocation,
        ...,
    ],
    reservations: tuple[
        InventoryReservation,
        ...,
    ],
    config: AvailabilitySimulationConfig = (DEFAULT_AVAILABILITY_CONFIG),
) -> tuple[
    AvailabilitySnapshot,
    ...,
]:

    profiles_by_key = _index_profiles(demand_profiles)

    sellable_location_ids = {
        location.inventory_location_id for location in locations if location.is_sellable
    }

    known_location_ids = {location.inventory_location_id for location in locations}

    sellable_balance: dict[
        tuple[
            str,
            str,
        ],
        int,
    ] = defaultdict(int)

    for movement in inventory_movements:
        if movement.event_date > snapshot_date:
            continue

        if movement.inventory_location_id not in known_location_ids:
            raise ValueError("inventory movement references unknown inventory location")

        if movement.inventory_location_id not in sellable_location_ids:
            continue

        key = (
            movement.market_code,
            movement.assortment_id,
        )

        sellable_balance[key] += movement.quantity_delta

    active_warehouse_counts: dict[
        tuple[
            str,
            str,
        ],
        int,
    ] = defaultdict(int)

    for warehouse_assortment in warehouse_assortments:
        if not _warehouse_assortment_active(
            warehouse_assortment,
            snapshot_date,
        ):
            continue

        key = (
            warehouse_assortment.market_code,
            warehouse_assortment.assortment_id,
        )

        active_warehouse_counts[key] += 1

    active_reserved: dict[
        tuple[
            str,
            str,
        ],
        int,
    ] = defaultdict(int)

    for reservation in reservations:
        if not _reservation_active(
            reservation,
            snapshot_date,
        ):
            continue

        key = (
            reservation.market_code,
            reservation.assortment_id,
        )

        active_reserved[key] += reservation.reserved_quantity

    snapshots: list[AvailabilitySnapshot] = []

    for key in sorted(profiles_by_key):
        profile = profiles_by_key[key]

        sellable_on_hand = sellable_balance[key]

        reserved_quantity = active_reserved[key]

        active_warehouse_count = active_warehouse_counts[key]

        if sellable_on_hand < 0:
            raise ValueError("sellable inventory balance cannot be negative")

        if reserved_quantity < 0:
            raise ValueError("reserved quantity cannot be negative")

        if reserved_quantity > sellable_on_hand:
            raise ValueError("active reservations exceed sellable physical inventory")

        if profile.average_daily_units <= Decimal("0"):
            raise ValueError("average daily demand must be positive")

        if active_warehouse_count == 0:
            available_to_promise = 0
            days_of_cover = None
            status: AvailabilityStatus = "UNAVAILABLE"

        else:
            available_to_promise = sellable_on_hand - reserved_quantity

            days_of_cover = _days_of_cover(
                available_to_promise,
                profile.average_daily_units,
            )

            status = _availability_status(
                available_to_promise=(available_to_promise),
                days_of_cover=(days_of_cover),
                config=config,
            )

        snapshots.append(
            AvailabilitySnapshot(
                snapshot_id=_snapshot_id(
                    snapshot_date=(snapshot_date),
                    market_code=(profile.market_code),
                    assortment_id=(profile.assortment_id),
                ),
                snapshot_date=(snapshot_date),
                market_code=(profile.market_code),
                assortment_id=(profile.assortment_id),
                product_id=(profile.product_id),
                sku=profile.sku,
                active_warehouse_count=(active_warehouse_count),
                sellable_on_hand=(sellable_on_hand),
                reserved_quantity=(reserved_quantity),
                available_to_promise=(available_to_promise),
                average_daily_units=(profile.average_daily_units),
                days_of_cover=(days_of_cover),
                availability_status=(status),
            )
        )

    return tuple(snapshots)


def _index_profiles(
    demand_profiles: tuple[
        DemandProfileLike,
        ...,
    ],
) -> dict[
    tuple[
        str,
        str,
    ],
    DemandProfileLike,
]:
    result: dict[
        tuple[
            str,
            str,
        ],
        DemandProfileLike,
    ] = {}

    for profile in demand_profiles:
        key = (
            profile.market_code,
            profile.assortment_id,
        )

        if key in result:
            raise ValueError("duplicate demand profile for market assortment")

        result[key] = profile

    return result


def _warehouse_assortment_active(
    warehouse_assortment: WarehouseAssortment,
    snapshot_date: date,
) -> bool:
    if warehouse_assortment.stocked_from > snapshot_date:
        return False

    if (
        warehouse_assortment.stocked_to is not None
        and snapshot_date >= warehouse_assortment.stocked_to
    ):
        return False

    return True


def _reservation_active(
    reservation: InventoryReservation,
    snapshot_date: date,
) -> bool:

    if reservation.reserved_date > snapshot_date:
        return False

    if reservation.released_date is not None and reservation.released_date <= snapshot_date:
        return False

    if reservation.consumed_date is not None and reservation.consumed_date <= snapshot_date:
        return False

    return True


def _days_of_cover(
    available_to_promise: int,
    average_daily_units: Decimal,
) -> Decimal:
    if available_to_promise == 0:
        return Decimal("0.00")

    value = Decimal(available_to_promise) / average_daily_units

    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _availability_status(
    *,
    available_to_promise: int,
    days_of_cover: Decimal,
    config: AvailabilitySimulationConfig,
) -> AvailabilityStatus:
    if available_to_promise == 0:
        return "OUT_OF_STOCK"

    if days_of_cover < config.low_stock_days:
        return "LOW_STOCK"

    return "IN_STOCK"


def _snapshot_id(
    *,
    snapshot_date: date,
    market_code: str,
    assortment_id: str,
) -> str:
    value = uuid5(
        NAMESPACE_URL,
        (
            "mercatura:"
            "availability-snapshot:"
            f"{snapshot_date.isoformat()}:"
            f"{market_code}:"
            f"{assortment_id}"
        ),
    )

    return f"avs_{value.hex[:20]}"
