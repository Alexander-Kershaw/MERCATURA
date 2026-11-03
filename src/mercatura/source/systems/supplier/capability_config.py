"""
=============================================================================

CAPABILITY RANGES FOR SUPPLIER TYPES

=============================================================================

This configuration file defines the capability ranges for different
supplier types. Each supplier type is associated with a tuple that specifies
the minimum and maximum capabilities:

MANUFACTURER: (1, 2) - Minimum capability of 1 and maximum capability of 2.
DISTRIBUTOR: (2, 4) - Minimum capability of 2 and maximum capability of 4.
WHOLESALER: (3, 6) - Minimum capability of 3 and maximum capability of 6.
IMPORTER: (2, 5) - Minimum capability of 2 and maximum capability of 5.

-----------------------------------------------------------------------------

Semantically, you can interpret these ranges as follows:

- MANUFACTURER: Can handle a small range of capabilities,
suitable for specialized production.

- DISTRIBUTOR: Can handle a moderate range of capabilities,
suitable for distributing products to various channels.

- WHOLESALER: Can handle a wide range of capabilities, a broad catalogue
suitable for managing large scale distribution networks.

- IMPORTER: Can handle a moderatly broad range of capabilities,
suitable for importing and distributing foreign products.

-----------------------------------------------------------------------------

Note: The capability ranges are defined as tuples of integers, and are not
explicit categories e.g I am not doing Chine = Electronics, or
France = Beauty.

Georaphical and product affinities are already baked into the procurement
model so tbe capability ranges really represent the commercial scope of the
supplier rather than specific product designations.

=============================================================================
"""

SUPPLIER_TYPE_CAPABILITY_RANGES: dict[
    str,
    tuple[int, int],
] = {
    "MANUFACTURER": (1, 2),
    "DISTRIBUTOR": (2, 4),
    "WHOLESALER": (3, 6),
    "IMPORTER": (2, 5),
}
