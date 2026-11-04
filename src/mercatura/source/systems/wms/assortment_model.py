from dataclasses import dataclass
from datetime import date

"""
================================================================================================

WAREHOUSE ASSORTMENT MODEL

================================================================================================

This model and related scripts exist because the market product assortment does not necessarily 
mean products are stored in every warehouse.

Considering this, instead every product-market assortment will get a deterministic 
warehouse stocking network with these general principles as play:

- lower demand SKUs may sit in one warehouse
- higher demand SKUs can be distributed across several warehouses
- Every inbound product order line is then routed to a valid warehouse. Specifically the
valid warehouses RECEIVING zone.

-----------------------------------------------------------------------------------------------

Another thing being considered is split shipments. A split shipment for the same product
order line should land in the same warehouse. Therefore, warehouse stocking including a bulk 
order of many products with a split shipment to Manchester, will not have one portion of the
split shipment arriving in Manchester, and other other split to Nottingham. Both split
shipments end up in the same warehouse.

Therefore, the actual inbound receipt routing happens at the product order line grain, and 
not independently for every receipt.

-----------------------------------------------------------------------------------------------

The model include the WarehouseAssortment dataclass including the following attributes:

- warehouse_assortment_id: an identifier for warehouse assortment allocation
- assortment_id: an identifier for an assortment 
- product_id: an identifer for a specific product
- sku: stock keeping unit for the product
- market_code: the warehouse regional market code
- warehouse_id: the identifier for the warehouse
- warehouse_code: the WMS system code identifying the warehouse
- stocking_priority: a priority factor influencing stocking priority for the warehouse 
- stocked_from: stocking date start
- stocked_to: stocking date expiration

-----------------------------------------------------------------------------------------------

stocking_priority in particular warrents some explanation. Take example:

stocking_priority = 1 basically means that this warehouse is the primary warehouse for that
particular market / SKU.

Additional facilities get priorities 2, 3, 4, etc...

This is not an inventory balance. Really, it represents which of the Mercatura warehouses
are operationally expected to carry this assortment of products.

================================================================================================
"""


@dataclass(frozen=True, slots=True)
class WarehouseAssortment:
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

    def is_active_on(
        self,
        value: date,
    ) -> bool:
        return value >= self.stocked_from and (self.stocked_to is None or value < self.stocked_to)
