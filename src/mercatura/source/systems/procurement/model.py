from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

"""
==============================================================================

SOURCING MODEL

==============================================================================

A procurement source may be of three types:

- PRIMARY: the main source of procurement
- SECONDARY: an additional source of producrement
- BACKUP: another additional procurement source

The SourcingAgreement dataclass details what an aggreement with a
a supplier of a product would look like.

Importantly. the unit_cost field represents the negotiated landing unit cost
in the buying market's currency.

Therefore, for example a Chinese supplier with market code CN serving a GB
buyer will have a GBP landing unit_cost. 

Potentially, later purchase orders could introduce supplier invoice 
currencies and FX seperately.

==============================================================================
"""
SourcingRole = Literal[
    "PRIMARY",
    "SECONDARY",
    "BACKUP",
]


@dataclass(frozen=True, slots=True)
class SourcingAgreement:
    sourcing_id: str
    assortment_id: str
    product_id: str
    sku: str
    market_code: str
    supplier_id: str
    supplier_code: str
    sourcing_role: SourcingRole
    unit_cost: Decimal
    currency: str
    minimum_order_quantity: int
    lead_time_days: int
    effective_from: date
    effective_to: date | None

    def is_effective_on(
        self,
        value: date,
    ) -> bool:
        return self.effective_from <= value and (
            self.effective_to is None or value < self.effective_to
        )
