from dataclasses import dataclass

"""
=================================================================================

SUPPLIER CAPABILITY

=================================================================================

Supplier catability is a dataclass representing which classes of products
a supplier is capable of supplying. It is used to determine which suppliers
are capable of supplying which products.

This will be wired into the sourcing engine.

Note: this does not represent what a buyer is currently sourcing from a supplier,
that is detailed in the sourcing agreement between the buyer and supplier which
is represented in the sourcing agreement dataclass.

The data in the supplier capability dataclass has a supplier x department 
granularity. This is because a supplier may have multiple departments 
that are capable of supplying different classes of products. For example:

SUP-CN-0001 x Electronics 
SUP-CN-0001 x Furniture

SUP-DE-0001 x Electronics
SUP-DE-0001 x Furniture
SUP-DE-0001 x Automotive

Different suppliers of different markets with different departments capable
of supplying different classes of products.

=================================================================================
"""


@dataclass(frozen=True, slots=True)
class SupplierCapability:
    capability_id: str
    supplier_id: str
    supplier_code: str
    department_code: str
    department_name: str
