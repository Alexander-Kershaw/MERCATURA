from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProductPrice:
    price_id: str
    assortment_id: str
    product_id: str
    sku: str
    market_code: str
    currency: str
    list_price: Decimal
    effective_from: date
    effective_to: date | None
    version: int

    def is_effective_on(
        self,
        value: date,
    ) -> bool:
        return self.effective_from <= value and (
            self.effective_to is None or value < self.effective_to
        )
