import random
from collections import Counter
from datetime import date, timedelta

from mercatura.source.reference.warehouse_topology import (
    WAREHOUSE_SITES,
    WarehouseSite,
)
from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.wms.config import (
    DEFAULT_INVENTORY_ZONES,
)
from mercatura.source.systems.wms.model import (
    InventoryLocation,
    Warehouse,
)


def generate_warehouses(
    context: SimulationContext,
) -> tuple[Warehouse, ...]:
    market_codes: set[str] = {market.market_code for market in context.config.markets}

    sites: list[WarehouseSite] = [
        site for site in WAREHOUSE_SITES if site.market_code in market_codes
    ]

    counters: Counter[str] = Counter()

    warehouses: list[Warehouse] = []

    for site in sites:
        counters[site.market_code] += 1

        warehouse_number = counters[site.market_code]

        warehouses.append(
            _generate_warehouse(
                context=context,
                site=site,
                warehouse_number=(warehouse_number),
            )
        )

    return tuple(warehouses)


def _generate_warehouse(
    *,
    context: SimulationContext,
    site: WarehouseSite,
    warehouse_number: int,
) -> Warehouse:
    warehouse_code: str = f"WH-{site.market_code}-{warehouse_number:03d}"

    warehouse_id: str = context.ids.id_for(
        namespace="warehouse",
        key=warehouse_code,
        prefix="wh",
    )

    rng = random.Random(x=context.seed_for(namespace=(f"wms:warehouse:{warehouse_code}")))

    history_days: int = rng.randint(
        a=365 * 3,
        b=365 * 15,
    )

    opened_at: date = context.config.start_date - timedelta(days=history_days)

    warehouse_name: str = f"Mercatura {site.city} {_warehouse_type_name(site)}"

    return Warehouse(
        warehouse_id=warehouse_id,
        warehouse_code=warehouse_code,
        warehouse_name=warehouse_name,
        market_code=site.market_code,
        country_code=site.market_code,
        warehouse_type=(site.warehouse_type),
        city=site.city,
        region=site.region,
        timezone=site.timezone,
        opened_at=opened_at,
        closed_at=None,
        supports_store_replenishment=(site.supports_store_replenishment),
        supports_ecommerce=(site.supports_ecommerce),
    )


def _warehouse_type_name(
    site: WarehouseSite,
) -> str:
    names: dict[str, str] = {
        "NATIONAL_DC": "National Distribution Centre",
        "REGIONAL_DC": "Regional Distribution Centre",
        "ECOMMERCE_FC": "Ecommerce Fulfilment Centre",
        "HYBRID_FC": "Fulfilment Centre",
    }

    return names[site.warehouse_type]


def generate_inventory_locations(
    context: SimulationContext,
    warehouses: tuple[Warehouse, ...],
) -> tuple[InventoryLocation, ...]:
    locations: list[InventoryLocation] = []

    for warehouse in sorted(
        warehouses,
        key=lambda row: row.warehouse_code,
    ):
        for zone in DEFAULT_INVENTORY_ZONES:
            location_code: str = f"{warehouse.warehouse_code}-{zone.code_suffix}"

            location_id: str = context.ids.id_for(
                namespace="inventory_location",
                key=location_code,
                prefix="loc",
            )

            locations.append(
                InventoryLocation(
                    inventory_location_id=(location_id),
                    location_code=(location_code),
                    warehouse_id=(warehouse.warehouse_id),
                    warehouse_code=(warehouse.warehouse_code),
                    location_type=(zone.location_type),
                    is_sellable=(zone.is_sellable),
                    accepts_receipts=(zone.accepts_receipts),
                    allows_dispatch=(zone.allows_dispatch),
                )
            )

    return tuple(locations)
