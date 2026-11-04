from dataclasses import replace

import pytest

from mercatura.source.systems.wms.assortment_validation import (
    validate_warehouse_assortments,
)


def validate(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    validate_warehouse_assortments(
        warehouse_assortments,
        assortments,
        demand_profiles,
        warehouses,
    )


def test_valid_dataset_passes(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    validate(
        warehouse_assortments,
        assortments,
        demand_profiles,
        warehouses,
    )


def test_rejects_duplicate_id(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    broken = (
        *warehouse_assortments,
        warehouse_assortments[0],
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate warehouse_assortment_id",
    ):
        validate(
            broken,
            assortments,
            demand_profiles,
            warehouses,
        )


def test_rejects_duplicate_assortment_warehouse_pair(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    target = warehouse_assortments[0]

    duplicate = replace(
        target,
        warehouse_assortment_id=("wha_duplicate"),
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate assortment/warehouse",
    ):
        validate(
            (
                *warehouse_assortments,
                duplicate,
            ),
            assortments,
            demand_profiles,
            warehouses,
        )


def test_rejects_unknown_assortment(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    target = warehouse_assortments[0]

    broken_row = replace(
        target,
        assortment_id="ast_missing",
    )

    broken = tuple(
        broken_row if row.warehouse_assortment_id == target.warehouse_assortment_id else row
        for row in warehouse_assortments
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="unknown assortment",
    ):
        validate(
            broken,
            assortments,
            demand_profiles,
            warehouses,
        )


def test_rejects_wrong_market(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    target = warehouse_assortments[0]

    broken_row = replace(
        target,
        market_code="ZZ",
    )

    broken = tuple(
        broken_row if row.warehouse_assortment_id == target.warehouse_assortment_id else row
        for row in warehouse_assortments
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="market",
    ):
        validate(
            broken,
            assortments,
            demand_profiles,
            warehouses,
        )


def test_rejects_bad_priority(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    target = warehouse_assortments[0]

    broken_row = replace(
        target,
        stocking_priority=99,
    )

    broken = tuple(
        broken_row if row.warehouse_assortment_id == target.warehouse_assortment_id else row
        for row in warehouse_assortments
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="stocking priorities",
    ):
        validate(
            broken,
            assortments,
            demand_profiles,
            warehouses,
        )


def test_rejects_incorrect_stocked_from(
    warehouse_assortments,
    assortments,
    demand_profiles,
    warehouses,
) -> None:
    target = warehouse_assortments[0]

    broken_row = replace(
        target,
        stocked_from=(target.stocked_from.replace(year=(target.stocked_from.year + 1))),
    )

    broken = tuple(
        broken_row if row.warehouse_assortment_id == target.warehouse_assortment_id else row
        for row in warehouse_assortments
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="stocked_from",
    ):
        validate(
            broken,
            assortments,
            demand_profiles,
            warehouses,
        )
