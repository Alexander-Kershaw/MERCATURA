from collections import defaultdict
from datetime import date
from decimal import Decimal

from mercatura.source.simulation.demand import (
    DemandProfile,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.wms.assortment_config import (
    DEFAULT_WAREHOUSE_ASSORTMENT_CONFIG,
    WarehouseAssortmentSimulationConfig,
)
from mercatura.source.systems.wms.assortment_model import (
    WarehouseAssortment,
)
from mercatura.source.systems.wms.model import (
    Warehouse,
)


def validate_warehouse_assortments(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
    *,
    config: WarehouseAssortmentSimulationConfig = (DEFAULT_WAREHOUSE_ASSORTMENT_CONFIG),
) -> None:
    _validate_unique_rows(warehouse_assortments)

    _validate_references_and_metadata(
        warehouse_assortments,
        assortments,
        warehouses,
    )

    _validate_temporal_rules(
        warehouse_assortments,
        assortments,
        warehouses,
    )

    _validate_assortment_coverage(
        warehouse_assortments,
        assortments,
    )

    _validate_priorities(warehouse_assortments)

    _validate_stocking_policy(
        warehouse_assortments,
        assortments,
        demand_profiles,
        warehouses,
        config,
    )


def _validate_unique_rows(
    rows: tuple[WarehouseAssortment, ...],
) -> None:
    identifiers: list[str] = [row.warehouse_assortment_id for row in rows]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate warehouse_assortment_id detected")

    pairs: list[tuple[str, str]] = [
        (
            row.assortment_id,
            row.warehouse_id,
        )
        for row in rows
    ]

    if len(pairs) != len(set(pairs)):
        raise ValueError("duplicate assortment/warehouse stocking relationship detected")


def _validate_references_and_metadata(
    rows: tuple[WarehouseAssortment, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    assortments_by_id: dict[str, ProductMarketAssortment] = {
        row.assortment_id: row for row in assortments
    }

    warehouses_by_id: dict[str, Warehouse] = {row.warehouse_id: row for row in warehouses}

    for row in rows:
        assortment: ProductMarketAssortment | None = assortments_by_id.get(row.assortment_id)

        if assortment is None:
            raise ValueError("warehouse assortment references unknown assortment")

        warehouse: Warehouse | None = warehouses_by_id.get(row.warehouse_id)

        if warehouse is None:
            raise ValueError("warehouse assortment references unknown warehouse")

        if row.product_id != assortment.product_id:
            raise ValueError("warehouse assortment product does not match assortment")

        if row.sku != assortment.sku:
            raise ValueError("warehouse assortment SKU does not match assortment")

        if row.market_code != assortment.market_code:
            raise ValueError("warehouse assortment market does not match assortment")

        if warehouse.market_code != row.market_code:
            raise ValueError("warehouse market does not match warehouse assortment")

        if row.warehouse_code != warehouse.warehouse_code:
            raise ValueError("warehouse assortment code does not match warehouse")


def _validate_temporal_rules(
    rows: tuple[WarehouseAssortment, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    assortments_by_id: dict[str, ProductMarketAssortment] = {
        row.assortment_id: row for row in assortments
    }

    warehouses_by_id: dict[str, Warehouse] = {row.warehouse_id: row for row in warehouses}

    for row in rows:
        assortment: ProductMarketAssortment = assortments_by_id[row.assortment_id]

        warehouse: Warehouse = warehouses_by_id[row.warehouse_id]

        expected_from: date = max(
            assortment.ranged_from,
            warehouse.opened_at,
        )

        expected_to: date | None = _earliest_optional_date(
            assortment.ranged_to,
            warehouse.closed_at,
        )

        if row.stocked_from != expected_from:
            raise ValueError("warehouse assortment stocked_from is invalid")

        if row.stocked_to != expected_to:
            raise ValueError("warehouse assortment stocked_to is invalid")

        if row.stocked_to is not None and row.stocked_from >= row.stocked_to:
            raise ValueError("warehouse assortment has invalid lifecycle")


def _validate_assortment_coverage(
    rows: tuple[WarehouseAssortment, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    covered: set[str] = {row.assortment_id for row in rows}

    expected: set[str] = {row.assortment_id for row in assortments}

    if covered != expected:
        raise ValueError("warehouse assortments do not cover every market assortment")


def _validate_priorities(
    rows: tuple[WarehouseAssortment, ...],
) -> None:
    grouped: dict[
        str,
        list[WarehouseAssortment],
    ] = defaultdict(list)

    for row in rows:
        grouped[row.assortment_id].append(row)

    for assortment_id, group in grouped.items():
        priorities: list[int] = sorted(row.stocking_priority for row in group)

        expected: list[int] = list(
            range(
                1,
                len(group) + 1,
            )
        )

        if priorities != expected:
            raise ValueError(f"warehouse stocking priorities are invalid for {assortment_id}")


def _validate_stocking_policy(
    rows: tuple[WarehouseAssortment, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
    config: WarehouseAssortmentSimulationConfig,
) -> None:
    demand_by_assortment: dict[str, DemandProfile] = {
        row.assortment_id: row for row in demand_profiles
    }

    warehouses_by_market: dict[
        str,
        list[Warehouse],
    ] = defaultdict(list)

    for warehouse in warehouses:
        warehouses_by_market[warehouse.market_code].append(warehouse)

    rows_by_assortment: dict[
        str,
        list[WarehouseAssortment],
    ] = defaultdict(list)

    for row in rows:
        rows_by_assortment[row.assortment_id].append(row)

    for assortment in assortments:
        demand: DemandProfile | None = demand_by_assortment.get(assortment.assortment_id)

        if demand is None:
            raise ValueError("missing demand profile for warehouse stocking policy")

        eligible_warehouses: list[Warehouse] = [
            warehouse
            for warehouse in warehouses_by_market[assortment.market_code]
            if _warehouse_overlaps(
                warehouse=warehouse,
                assortment=assortment,
            )
        ]

        expected_count: int = min(
            _desired_count(
                demand.average_daily_units,
                config,
            ),
            len(eligible_warehouses),
        )

        actual_count: int = len(rows_by_assortment[assortment.assortment_id])

        if actual_count != expected_count:
            raise ValueError(
                "warehouse stocking count "
                "does not match demand policy "
                f"for {assortment.assortment_id}"
            )


def _desired_count(
    demand_rate: Decimal,
    config: WarehouseAssortmentSimulationConfig,
) -> int:
    if demand_rate <= config.low_demand_threshold:
        return config.low_demand_warehouse_count

    if demand_rate <= config.medium_demand_threshold:
        return config.medium_demand_warehouse_count

    if demand_rate <= config.high_demand_threshold:
        return config.high_demand_warehouse_count

    return config.very_high_demand_warehouse_count


def _warehouse_overlaps(
    *,
    warehouse: Warehouse,
    assortment: ProductMarketAssortment,
) -> bool:
    if assortment.ranged_to is not None and warehouse.opened_at >= assortment.ranged_to:
        return False

    if warehouse.closed_at is not None and warehouse.closed_at <= assortment.ranged_from:
        return False

    return True


def _earliest_optional_date(
    first: date | None,
    second: date | None,
) -> date | None:
    if first is None:
        return second

    if second is None:
        return first

    return min(
        first,
        second,
    )
