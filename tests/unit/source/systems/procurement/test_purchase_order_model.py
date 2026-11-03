from datetime import date
from decimal import Decimal

from mercatura.source.systems.procurement.purchase_order_model import (
    PurchaseOrderLine,
)


def test_line_value_is_quantity_times_unit_cost() -> None:
    line = PurchaseOrderLine(
        purchase_order_line_id="pol_test",
        purchase_order_id="po_test",
        line_number=1,
        assortment_id="ast_test",
        product_id="prd_test",
        sku="MRC-000001",
        sourcing_id="src_test",
        ordered_quantity=25,
        unit_cost=Decimal(value="12.50"),
        currency="GBP",
        expected_delivery_date=date(
            year=2025,
            month=1,
            day=10,
        ),
    )

    assert line.line_value == Decimal(value="312.50")
