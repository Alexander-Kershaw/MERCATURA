from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Supplier:
    """
    =================================================================================

    SUPPLIER MODEL

    =================================================================================

    The main supplier model object has the following attributes:

    - supplier_id: a supplier identification string
    - supplier_code: a supplier code also used for identification
    - legal_name: the name of the supplier
    - supplier_type: the type of supplier
    - country_code: the regional country code associated with the supplier
    - currency: the currency the supplier trades in
    - city: the specific city in which a supplier is based
    - region: the region in which the supplier is based
    - created_at: when the supplier was created
    - inactive_at: when a supplier has become inactive (none if still active)

    =================================================================================
    """

    supplier_id: str
    supplier_code: str
    legal_name: str
    supplier_type: str
    country_code: str
    currency: str
    city: str
    region: str
    created_at: date
    inactive_at: date | None = None

    @property
    def is_current(self) -> bool:
        return self.inactive_at is None

    def is_active_on(
        self,
        value: date,
    ) -> bool:
        return self.created_at <= value and (self.inactive_at is None or value < self.inactive_at)
