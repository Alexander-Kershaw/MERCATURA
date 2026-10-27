from mercatura.source.reference.product_taxonomy import (
    PRODUCT_TAXONOMY,
)


def test_taxonomy_subcategory_codes_are_unique() -> None:
    codes: list[str] = [category.subcategory_code for category in PRODUCT_TAXONOMY]

    assert len(codes) == len(set(codes))


def test_taxonomy_has_multiple_departments() -> None:
    departments: set[str] = {category.department_code for category in PRODUCT_TAXONOMY}

    assert len(departments) >= 8


def test_all_taxonomy_entries_have_product_terms() -> None:
    assert all(category.product_terms for category in PRODUCT_TAXONOMY)


def test_all_taxonomy_weights_are_positive() -> None:
    assert all(category.weight > 0 for category in PRODUCT_TAXONOMY)
