from dataclasses import dataclass
from datetime import date
from typing import Literal

"""
========================================================================================================

WAREHOUSE MANAGEMENT SYSTEM MODEL

========================================================================================================

Warehouses may be of the following types:

- NATIONAL_DC: A national distribution center
- REGIONAL_DC: A regional distribution center
- ECOMMERCE_FC: An ecommerence fulfilment center
- HYBRID_FC: A hybrid fulfilment center

--------------------------------------------------------------------------------------------------------

InventoryLocation represents a logical WMS zone rather than an individual bin or pallet position.
This is because modelling lots of bins would be excessive for the simulation.

The InventoryLocationType details what the warehouse zone is responsible for, including:

- RECEIVING: A zone responsible for receiving shipments from suppliers
- BULK_STORAGE: A zone used for storing stock in bulk
- PICK_FACE: A zone for picking / sorting of inventory
- RETURNS: A zone for handling returned inventory
- QUARANTINE: A zone dedicated to the isolation of inventory.

--------------------------------------------------------------------------------------------------------

The Warehouse dataclass is the core modelling object for the WMS and has the following attributes:

- warehouse_id: unique identifier for the warehouse
- warehouse_code: identifying code for the warehouse (specific to the WMS)
- warehouse_name: the name of the warehouse
- market_code: the regional market the warehouse resides in
- country_code: the country code the warehouse resides in
- warehouse_type: the type are warehouse from the WarehouseType list
- city: the city the warehouse is in
- region: the region the warehouse is in
- timezone: the associated local timezone for the warehouse location
- opened_at: when the warehouse began operation
- closed_at: when the warehouse concluded operations (empty if still operational)
- supports_store_replenishment: if the warehouse supports stock replenishment 
- supports_ecommerce: if the warehouse supports ecommerce order fulfilment

--------------------------------------------------------------------------------------------------------

The InventoryLocation dataclass has the following attributes:

- inventory_location_id: Warehouse zone identification where inventory is located
- location_code: Inventory location code (for finding inventory in the WMS system)
- warehouse_id: The id of the warehouse
- warehouse_code: The warehouse code in the WMS system
- location_type: What zone the inventory is located in is responsible for
- is_sellable: If the inventory in the zone is sellable 
- accepts_receipts: If the zone accepts inventory receips 
- allows_dispatch: If the zone allows dispaching of inventory

--------------------------------------------------------------------------------------------------------

The overall topology of the model is:

              Market
                ↓
              Warehouse / Fulfilment Centre
                ├── RECEIVING
                ├── BULK_STORAGE
                ├── PICK_FACE
                ├── RETURNS
                └── QUARANTINE

--------------------------------------------------------------------------------------------------------
                
An example inventory lifecycle that will be fulfiled by this model:

                Goods receipt
                    ↓
                RECEIVING
                    ↓ PUTAWAY
                BULK_STORAGE
                    ↓ REPLENISHMENT
                PICK_FACE
                    ↓ CUSTOMER / STORE DISPATCH

Returns and damaged / suspect inventory are segrated from the sellable stock.

========================================================================================================
"""


WarehouseType = Literal[
    "NATIONAL_DC",
    "REGIONAL_DC",
    "ECOMMERCE_FC",
    "HYBRID_FC",
]


InventoryLocationType = Literal[
    "RECEIVING",
    "BULK_STORAGE",
    "PICK_FACE",
    "RETURNS",
    "QUARANTINE",
]


WAREHOUSE_TYPES: tuple[WarehouseType, ...] = (
    "NATIONAL_DC",
    "REGIONAL_DC",
    "ECOMMERCE_FC",
    "HYBRID_FC",
)


INVENTORY_LOCATION_TYPES: tuple[InventoryLocationType, ...] = (
    "RECEIVING",
    "BULK_STORAGE",
    "PICK_FACE",
    "RETURNS",
    "QUARANTINE",
)


@dataclass(frozen=True, slots=True)
class Warehouse:
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    market_code: str
    country_code: str
    warehouse_type: WarehouseType
    city: str
    region: str
    timezone: str
    opened_at: date
    closed_at: date | None
    supports_store_replenishment: bool
    supports_ecommerce: bool

    @property
    def is_current(self) -> bool:
        return self.closed_at is None

    def is_active_on(
        self,
        value: date,
    ) -> bool:
        return value >= self.opened_at and (self.closed_at is None or value < self.closed_at)


@dataclass(frozen=True, slots=True)
class InventoryLocation:
    inventory_location_id: str
    location_code: str
    warehouse_id: str
    warehouse_code: str
    location_type: InventoryLocationType
    is_sellable: bool
    accepts_receipts: bool
    allows_dispatch: bool
