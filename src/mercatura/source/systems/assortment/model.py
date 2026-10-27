from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ProductMarketAssortment:
    assortment_id: str
    product_id: str
    sku: str
    market_code: str
    ranged_from: date
    ranged_to: date | None = None

    def is_active_on(self, value: date) -> bool:
        return self.ranged_from <= value and (self.ranged_to is None or value < self.ranged_to)
