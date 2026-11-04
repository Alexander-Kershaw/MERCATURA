from dataclasses import dataclass

"""
====================================================================================

RECEIPT ROUTING MODEL

====================================================================================

The InboundReceiptRoute dataclass contains data attributes that detail the inbound 
warehouse stocking receipt routing i.e where the inbound stock reciept actually 
goes and what data entities are associated with it.

This is at the product order line level, essentially:

- A PO order line exists
- The inbound receipt is routed
- The receipt is routed to the correct warehouse for that assortment 
- The specific RECIEVING zone of the warehouse is referenced
- All the recepts of for that PO line are routed to the correct warehouse and zone

------------------------------------------------------------------------------------

This is what helps deal with split shipments:

Assuming a split shipment of 500 total units to a Berlin warehouse

consider 300 units purchased arriving at a Berlin warehouse in the 20th May.
Then the remaining 200 units will arrive on the 27th May, also to the Berlin
warehouse.

Therefore, supply is not being randomly sent to Berlin and then to Frankfurt.


====================================================================================
"""


@dataclass(frozen=True, slots=True)
class InboundReceiptRoute:
    route_id: str
    purchase_order_id: str
    purchase_order_line_id: str
    assortment_id: str
    product_id: str
    sku: str
    market_code: str
    warehouse_assortment_id: str
    warehouse_id: str
    warehouse_code: str
    inventory_location_id: str
    location_code: str
