from decimal import Decimal

import pytest

from mercatura.source.simulation.market import (
    DEFAULT_MARKETS,
)
from mercatura.source.systems.procurement.config import (
    MARKET_REGIONS,
    ROLE_COST_RANGES,
    SOURCING_ROLES,
    SUPPLIER_TYPE_COST_ADJUSTMENTS,
    SUPPLIER_TYPE_LOGISTICS,
    ProcurementSimulationConfig,
)
from mercatura.source.systems.supplier.config import (
    SUPPLIER_TYPES,
)


def test_default_source_probabilities_sum_to_one() -> None:
    config = ProcurementSimulationConfig()

    assert (
        config.single_source_probability
        + config.dual_source_probability
        + config.triple_source_probability
    ) == pytest.approx(expected=1.0)


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_single_source_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        ProcurementSimulationConfig(
            single_source_probability=value,
        )


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_dual_source_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        ProcurementSimulationConfig(
            dual_source_probability=value,
        )


@pytest.mark.parametrize(
    argnames="value",
    argvalues=(-0.01, 1.01),
)
def test_rejects_invalid_triple_source_probability(
    value: float,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        ProcurementSimulationConfig(
            triple_source_probability=value,
        )


def test_rejects_probabilities_not_summing_to_one() -> None:
    with pytest.raises(expected_exception=ValueError):
        ProcurementSimulationConfig(
            single_source_probability=0.50,
            dual_source_probability=0.40,
            triple_source_probability=0.20,
        )


def test_expected_sourcing_roles_exist() -> None:
    assert SOURCING_ROLES == (
        "PRIMARY",
        "SECONDARY",
        "BACKUP",
    )


def test_every_role_has_cost_range() -> None:
    assert set(ROLE_COST_RANGES) == set(SOURCING_ROLES)


def test_role_cost_ranges_are_valid() -> None:
    for minimum, maximum in ROLE_COST_RANGES.values():
        assert isinstance(
            minimum,
            Decimal,
        )

        assert isinstance(
            maximum,
            Decimal,
        )

        assert Decimal("0") < minimum <= maximum
        assert maximum < Decimal("1")


def test_supplier_type_configurations_are_complete() -> None:
    expected: set[str] = set(SUPPLIER_TYPES)

    assert set(SUPPLIER_TYPE_COST_ADJUSTMENTS) == expected

    assert set(SUPPLIER_TYPE_LOGISTICS) == expected


def test_supplier_logistics_ranges_are_valid() -> None:
    for (
        minimum_lead,
        maximum_lead,
        minimum_moq,
        maximum_moq,
    ) in SUPPLIER_TYPE_LOGISTICS.values():
        assert minimum_lead > 0
        assert maximum_lead >= minimum_lead

        assert minimum_moq > 0
        assert maximum_moq >= minimum_moq


def test_every_market_has_logistics_region() -> None:
    markets = {market.market_code for market in DEFAULT_MARKETS}

    assert set(MARKET_REGIONS) == markets
