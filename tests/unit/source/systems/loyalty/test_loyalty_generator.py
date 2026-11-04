from collections import Counter
from datetime import timedelta

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.loyalty.generator import (
    generate_loyalty_memberships,
)
from mercatura.source.systems.loyalty.model import (
    LoyaltyMembership,
)


def test_generation_is_deterministic(
    loyalty_context: SimulationContext,
    loyalty_customers: tuple[Customer, ...],
) -> None:
    first = generate_loyalty_memberships(
        loyalty_context,
        loyalty_customers,
    )

    second = generate_loyalty_memberships(
        loyalty_context,
        loyalty_customers,
    )

    assert first == second


def test_membership_ids_are_unique(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    identifiers = [membership.membership_id for membership in memberships]

    assert len(identifiers) == len(set(identifiers))


def test_loyalty_numbers_are_unique(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    numbers = [membership.loyalty_number for membership in memberships]

    assert len(numbers) == len(set(numbers))


def test_maximum_one_membership_per_customer(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    customer_ids = [membership.customer_id for membership in memberships]

    assert len(customer_ids) == len(set(customer_ids))


def test_memberships_reference_existing_customers(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
) -> None:
    customer_ids = {customer.customer_id for customer in loyalty_customers}

    assert all(membership.customer_id in customer_ids for membership in memberships)


def test_enrolment_occurs_after_customer_creation(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
) -> None:
    customers_by_id = {customer.customer_id: customer for customer in loyalty_customers}

    assert all(
        membership.enrolled_at > customers_by_id[membership.customer_id].created_at
        for membership in memberships
    )


def test_enrolment_occurs_while_customer_active(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
) -> None:
    customers_by_id = {customer.customer_id: customer for customer in loyalty_customers}

    assert all(
        customers_by_id[membership.customer_id].is_active_on(membership.enrolled_at)
        for membership in memberships
    )


def test_deactivated_memberships_close_with_customer(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
) -> None:
    customers_by_id = {customer.customer_id: customer for customer in loyalty_customers}

    for membership in memberships:
        customer = customers_by_id[membership.customer_id]

        if customer.deactivated_at is not None:
            assert membership.closed_at == customer.deactivated_at


def test_current_customer_memberships_remain_open(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
) -> None:
    customers_by_id = {customer.customer_id: customer for customer in loyalty_customers}

    for membership in memberships:
        customer = customers_by_id[membership.customer_id]

        if customer.is_current:
            assert membership.closed_at is None


def test_all_tiers_are_present(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    tiers = {membership.tier for membership in memberships}

    assert tiers == {
        "STANDARD",
        "SILVER",
        "GOLD",
        "PLATINUM",
    }


def test_tier_distribution_is_ordered(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    counts = Counter(membership.tier for membership in memberships)

    assert counts["STANDARD"] > counts["SILVER"] > counts["GOLD"] > counts["PLATINUM"]


def test_membership_penetration_is_reasonable(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
) -> None:
    penetration = len(memberships) / len(loyalty_customers)

    assert 0.35 < penetration < 0.50


def test_historical_enrolments_exist(
    loyalty_context: SimulationContext,
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    assert any(
        membership.enrolled_at < loyalty_context.config.start_date for membership in memberships
    )


def test_enrolments_during_simulation_exist(
    loyalty_context: SimulationContext,
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    assert any(
        membership.enrolled_at >= loyalty_context.config.start_date for membership in memberships
    )


def test_closed_memberships_exist(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    assert any(membership.closed_at is not None for membership in memberships)


def test_open_memberships_exist(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    assert any(membership.is_current for membership in memberships)


def test_membership_not_active_before_enrolment(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    membership = memberships[0]

    assert not membership.is_active_on(membership.enrolled_at - timedelta(days=1))


def test_membership_active_on_enrolment_date(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    assert all(membership.is_active_on(membership.enrolled_at) for membership in memberships)


def test_closed_membership_not_active_on_closure_date(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    membership = next(row for row in memberships if row.closed_at is not None)

    assert membership.closed_at is not None

    assert not membership.is_active_on(membership.closed_at)


def test_customer_input_order_independent(
    loyalty_context: SimulationContext,
    loyalty_customers: tuple[Customer, ...],
) -> None:
    first = generate_loyalty_memberships(
        loyalty_context,
        loyalty_customers,
    )

    second = generate_loyalty_memberships(
        loyalty_context,
        tuple(reversed(loyalty_customers)),
    )

    assert first == second
