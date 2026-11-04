from collections import Counter, defaultdict

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    DemandProfile,
)
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.wms.assortment_generator import (
    generate_warehouse_assortments,
)
from mercatura.source.systems.wms.assortment_model import (
    WarehouseAssortment,
)
from mercatura.source.systems.wms.model import (
    Warehouse,
)


def test_generation_is_deterministic(
    wms_context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    first: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        warehouses,
    )

    second: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        warehouses,
    )

    assert first == second


def test_every_market_assortment_is_stocked(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    assert {row.assortment_id for row in warehouse_assortments} == {
        row.assortment_id for row in assortments
    }


def test_warehouse_assortment_ids_are_unique(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    ids: list[str] = [row.warehouse_assortment_id for row in warehouse_assortments]

    assert len(ids) == len(set(ids))


def test_assortment_warehouse_pairs_are_unique(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    pairs: list[tuple[str, str]] = [
        (
            row.assortment_id,
            row.warehouse_id,
        )
        for row in warehouse_assortments
    ]

    assert len(pairs) == len(set(pairs))


def test_each_assortment_has_one_priority_one(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    counts: Counter[str] = Counter(
        row.assortment_id for row in warehouse_assortments if row.stocking_priority == 1
    )

    all_assortments: set[str] = {row.assortment_id for row in warehouse_assortments}

    assert all(counts[assortment_id] == 1 for assortment_id in all_assortments)


def test_priorities_are_contiguous(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    grouped: dict[
        str,
        list[int],
    ] = defaultdict(list)

    for row in warehouse_assortments:
        grouped[row.assortment_id].append(row.stocking_priority)

    for priorities in grouped.values():
        actual: list[int] = sorted(priorities)

        assert actual == list(
            range(
                1,
                len(actual) + 1,
            )
        )


def test_norway_assortments_have_one_warehouse(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    counts: Counter[str] = Counter(
        row.assortment_id for row in warehouse_assortments if row.market_code == "NO"
    )

    assert counts

    assert all(count == 1 for count in counts.values())


def test_multi_warehouse_assortments_exist(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
) -> None:
    counts: Counter[str] = Counter(row.assortment_id for row in warehouse_assortments)

    assert any(count >= 2 for count in counts.values())

    assert any(count >= 3 for count in counts.values())


def test_warehouse_market_matches_assortment_market(
    warehouse_assortments: tuple[WarehouseAssortment, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    warehouse_by_id: dict[str, Warehouse] = {row.warehouse_id: row for row in warehouses}

    assert all(
        warehouse_by_id[row.warehouse_id].market_code == row.market_code
        for row in warehouse_assortments
    )


def test_assortment_input_order_independent(
    wms_context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    first: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        warehouses,
    )

    second: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        tuple(reversed(assortments)),
        demand_profiles,
        warehouses,
    )

    assert first == second


def test_demand_input_order_independent(
    wms_context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    first: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        warehouses,
    )

    second: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        tuple(reversed(demand_profiles)),
        warehouses,
    )

    assert first == second


def test_warehouse_input_order_independent(
    wms_context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
) -> None:
    first: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        warehouses,
    )

    second: tuple[WarehouseAssortment, ...] = generate_warehouse_assortments(
        wms_context,
        assortments,
        demand_profiles,
        tuple(reversed(warehouses)),
    )

    assert first == second
