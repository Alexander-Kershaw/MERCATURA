from dataclasses import dataclass
from datetime import date

"""
==========================================================================================

CORE PRODUCT MODEL CLASS

==========================================================================================

This dataclass details the global product master recorded owned by the PIM.

==========================================================================================
"""


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    sku: str
    product_name: str
    brand_name: str
    model_name: str
    department_code: str
    department_name: str
    category_code: str
    category_name: str
    subcategory_code: str
    subcategory_name: str
    colour: str | None
    material: str | None
    description: str
    unit_of_measure: str
    created_at: date
    discontinued_at: date | None = None

    @property
    def is_current(self) -> bool:
        return self.discontinued_at is None

    def is_active_on(
        self,
        value: date,
    ) -> bool:
        return self.created_at <= value and (
            self.discontinued_at is None or value < self.discontinued_at
        )
