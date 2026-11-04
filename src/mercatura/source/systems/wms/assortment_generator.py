import random
from collections import defaultdict
from datetime import date
from decimal import Decimal

from mercatura.source.simulation import (
    SimulationContext,
)
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


def generate_warehouse_assortments(
    context: SimulationContext,
    assortments: tuple[ProductMarketAssortment, ...],
    demand_profiles: tuple[DemandProfile, ...],
    warehouses: tuple[Warehouse, ...],
    *,
    config: WarehouseAssortmentSimulationConfig = (DEFAULT_WAREHOUSE_ASSORTMENT_CONFIG),
) -> tuple[WarehouseAssortment, ...]:
    demand_by_assortment: dict[str, DemandProfile] = {
        profile.assortment_id: profile for profile in demand_profiles
    }

    warehouses_by_market: dict[
        str,
        list[Warehouse],
    ] = defaultdict(list)

    for warehouse in warehouses:
        warehouses_by_market[warehouse.market_code].append(warehouse)

    rows: list[WarehouseAssortment] = []

    for assortment in sorted(
        assortments,
        key=lambda row: (
            row.market_code,
            row.sku,
        ),
    ):
        demand: DemandProfile = demand_by_assortment[assortment.assortment_id]

        candidates: list[Warehouse] = sorted(
            (
                warehouse
                for warehouse in warehouses_by_market[assortment.market_code]
                if _warehouse_overlaps_assortment(
                    warehouse=warehouse,
                    assortment=assortment,
                )
            ),
            key=lambda row: row.warehouse_code,
        )

        selected: list[Warehouse] = _select_warehouses(
            context=context,
            assortment=assortment,
            demand=demand,
            warehouses=candidates,
            config=config,
        )

        for priority, warehouse in enumerate(
            iterable=selected,
            start=1,
        ):
            stocked_from: date = max(
                assortment.ranged_from,
                warehouse.opened_at,
            )

            stocked_to: date | None = _earliest_optional_date(
                first=assortment.ranged_to,
                second=warehouse.closed_at,
            )

            if stocked_to is not None and stocked_from >= stocked_to:
                continue

            stable_key: str = f"{assortment.assortment_id}:{warehouse.warehouse_code}"

            warehouse_assortment_id: str = context.ids.id_for(
                namespace="warehouse_assortment",
                key=stable_key,
                prefix="wha",
            )

            rows.append(
                WarehouseAssortment(
                    warehouse_assortment_id=(warehouse_assortment_id),
                    assortment_id=(assortment.assortment_id),
                    product_id=(assortment.product_id),
                    sku=assortment.sku,
                    market_code=(assortment.market_code),
                    warehouse_id=(warehouse.warehouse_id),
                    warehouse_code=(warehouse.warehouse_code),
                    stocking_priority=priority,
                    stocked_from=stocked_from,
                    stocked_to=stocked_to,
                )
            )

    return tuple(rows)


def _desired_warehouse_count(
    *,
    demand: DemandProfile,
    config: WarehouseAssortmentSimulationConfig,
) -> int:
    rate: Decimal = demand.average_daily_units

    if rate <= config.low_demand_threshold:
        return config.low_demand_warehouse_count

    if rate <= config.medium_demand_threshold:
        return config.medium_demand_warehouse_count

    if rate <= config.high_demand_threshold:
        return config.high_demand_warehouse_count

    return config.very_high_demand_warehouse_count


def _warehouse_weight(
    *,
    warehouse: Warehouse,
    config: WarehouseAssortmentSimulationConfig,
) -> float:
    weights: dict[str, float] = {
        "NATIONAL_DC": config.national_dc_weight,
        "HYBRID_FC": config.hybrid_fc_weight,
        "REGIONAL_DC": config.regional_dc_weight,
        "ECOMMERCE_FC": config.ecommerce_fc_weight,
    }

    return weights[warehouse.warehouse_type]


def _select_warehouses(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    demand: DemandProfile,
    warehouses: list[Warehouse],
    config: WarehouseAssortmentSimulationConfig,
) -> list[Warehouse]:
    if not warehouses:
        raise ValueError(f"no warehouses available for market {assortment.market_code}")

    desired: int = min(
        _desired_warehouse_count(
            demand=demand,
            config=config,
        ),
        len(warehouses),
    )

    rng = random.Random(
        x=context.seed_for(
            namespace=(f"wms:warehouse-assortment:{assortment.market_code}:{assortment.sku}")
        )
    )

    remaining: list[Warehouse] = list(
        sorted(
            warehouses,
            key=lambda row: row.warehouse_code,
        )
    )

    selected: list[Warehouse] = []

    while remaining and len(selected) < desired:
        weights: list[float] = [
            _warehouse_weight(
                warehouse=warehouse,
                config=config,
            )
            for warehouse in remaining
        ]

        choice: Warehouse = rng.choices(
            population=remaining,
            weights=weights,
            k=1,
        )[0]

        selected.append(choice)

        remaining.remove(choice)

    return selected


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


def _warehouse_overlaps_assortment(
    *,
    warehouse: Warehouse,
    assortment: ProductMarketAssortment,
) -> bool:
    if warehouse.opened_at >= (assortment.ranged_to or date.max):
        return False

    if warehouse.closed_at is not None and warehouse.closed_at <= assortment.ranged_from:
        return False

    return True
