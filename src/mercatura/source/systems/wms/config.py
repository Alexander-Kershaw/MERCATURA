from dataclasses import dataclass

from mercatura.source.systems.wms.model import (
    InventoryLocationType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class InventoryZoneDefinition:
    code_suffix: str
    location_type: InventoryLocationType
    is_sellable: bool
    accepts_receipts: bool
    allows_dispatch: bool


DEFAULT_INVENTORY_ZONES: tuple[InventoryZoneDefinition, ...] = (
    InventoryZoneDefinition(
        code_suffix="RCV",
        location_type="RECEIVING",
        is_sellable=False,
        accepts_receipts=True,
        allows_dispatch=False,
    ),
    InventoryZoneDefinition(
        code_suffix="BLK",
        location_type="BULK_STORAGE",
        is_sellable=True,
        accepts_receipts=False,
        allows_dispatch=False,
    ),
    InventoryZoneDefinition(
        code_suffix="PCK",
        location_type="PICK_FACE",
        is_sellable=True,
        accepts_receipts=False,
        allows_dispatch=True,
    ),
    InventoryZoneDefinition(
        code_suffix="RET",
        location_type="RETURNS",
        is_sellable=False,
        accepts_receipts=False,
        allows_dispatch=False,
    ),
    InventoryZoneDefinition(
        code_suffix="QUA",
        location_type="QUARANTINE",
        is_sellable=False,
        accepts_receipts=False,
        allows_dispatch=False,
    ),
)
