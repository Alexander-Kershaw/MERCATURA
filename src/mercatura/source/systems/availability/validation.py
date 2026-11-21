from decimal import Decimal

from mercatura.source.systems.availability.config import (
    DEFAULT_AVAILABILITY_CONFIG,
    AvailabilitySimulationConfig,
)
from mercatura.source.systems.availability.generator import (
    DemandProfileLike,
)
from mercatura.source.systems.availability.model import (
    AVAILABILITY_STATUSES,
    AvailabilitySnapshot,
)


def validate_availability_snapshots(
    snapshots: tuple[
        AvailabilitySnapshot,
        ...,
    ],
    demand_profiles: tuple[
        DemandProfileLike,
        ...,
    ],
    *,
    config: AvailabilitySimulationConfig = (DEFAULT_AVAILABILITY_CONFIG),
) -> None:
    profile_keys = {
        (
            profile.market_code,
            profile.assortment_id,
        )
        for profile in demand_profiles
    }

    snapshot_keys = {
        (
            snapshot.market_code,
            snapshot.assortment_id,
        )
        for snapshot in snapshots
    }

    if len(profile_keys) != len(demand_profiles):
        raise ValueError("duplicate demand profile key")

    if len(snapshot_keys) != len(snapshots):
        raise ValueError("duplicate availability snapshot key")

    if snapshot_keys != profile_keys:
        raise ValueError("availability snapshots do not cover every demand profile")

    snapshot_ids = [snapshot.snapshot_id for snapshot in snapshots]

    if len(snapshot_ids) != len(set(snapshot_ids)):
        raise ValueError("duplicate availability snapshot_id detected")

    profiles_by_key = {
        (
            profile.market_code,
            profile.assortment_id,
        ): profile
        for profile in demand_profiles
    }

    for snapshot in snapshots:
        profile = profiles_by_key[
            (
                snapshot.market_code,
                snapshot.assortment_id,
            )
        ]

        if snapshot.availability_status not in AVAILABILITY_STATUSES:
            raise ValueError("invalid availability status")

        if snapshot.product_id != profile.product_id or snapshot.sku != profile.sku:
            raise ValueError("availability product metadata does not match demand profile")

        if snapshot.average_daily_units != profile.average_daily_units:
            raise ValueError("availability demand does not match demand profile")

        if snapshot.sellable_on_hand < 0:
            raise ValueError("sellable on hand cannot be negative")

        if snapshot.reserved_quantity < 0:
            raise ValueError("reserved quantity cannot be negative")

        if snapshot.available_to_promise < 0:
            raise ValueError("ATP cannot be negative")

        if snapshot.active_warehouse_count < 0:
            raise ValueError("active warehouse count cannot be negative")

        _validate_state(
            snapshot,
            config,
        )


def _validate_state(
    snapshot: AvailabilitySnapshot,
    config: AvailabilitySimulationConfig,
) -> None:
    if snapshot.availability_status == "UNAVAILABLE":
        if snapshot.active_warehouse_count != 0:
            raise ValueError("UNAVAILABLE assortment cannot have active warehouses")

        if snapshot.available_to_promise != 0:
            raise ValueError("UNAVAILABLE assortment must have zero ATP")

        if snapshot.days_of_cover is not None:
            raise ValueError("UNAVAILABLE assortment must have no days_of_cover")

        return

    if snapshot.active_warehouse_count <= 0:
        raise ValueError("available assortment requires active warehouse")

    expected_atp = snapshot.sellable_on_hand - snapshot.reserved_quantity

    if snapshot.available_to_promise != expected_atp:
        raise ValueError("ATP does not reconcile to sellable on hand minus reserved")

    if snapshot.days_of_cover is None:
        raise ValueError("available assortment requires days_of_cover")

    if snapshot.available_to_promise == 0:
        if snapshot.availability_status != "OUT_OF_STOCK":
            raise ValueError("zero ATP must be OUT_OF_STOCK")

        if snapshot.days_of_cover != Decimal("0.00"):
            raise ValueError("OUT_OF_STOCK must have zero days_of_cover")

        return

    if snapshot.days_of_cover < config.low_stock_days:
        expected_status = "LOW_STOCK"
    else:
        expected_status = "IN_STOCK"

    if snapshot.availability_status != expected_status:
        raise ValueError("availability status does not match days_of_cover")
