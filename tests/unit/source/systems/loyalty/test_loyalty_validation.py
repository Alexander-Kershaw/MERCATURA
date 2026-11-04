from dataclasses import replace
from datetime import timedelta
from typing import cast

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.loyalty.model import (
    LoyaltyMembership,
    LoyaltyTier,
)
from mercatura.source.systems.loyalty.validation import (
    validate_loyalty_memberships,
)


def replace_membership(
    memberships: tuple[LoyaltyMembership, ...],
    replacement: LoyaltyMembership,
) -> tuple[LoyaltyMembership, ...]:
    return tuple(
        replacement if membership.membership_id == replacement.membership_id else membership
        for membership in memberships
    )


def validate(
    *,
    memberships: tuple[LoyaltyMembership, ...],
    customers: tuple[Customer, ...],
    context: SimulationContext,
) -> None:
    validate_loyalty_memberships(
        memberships,
        customers,
        context,
    )


def test_valid_dataset_passes(
    memberships: tuple[LoyaltyMembership, ...],
    loyalty_customers: tuple[Customer, ...],
    loyalty_context: SimulationContext,
) -> None:
    validate(
        memberships=memberships,
        customers=loyalty_customers,
        context=loyalty_context,
    )


def test_rejects_duplicate_membership_id(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    broken = (
        *memberships,
        memberships[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate membership_id",
    ):
        validate(
            memberships=broken,
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_duplicate_loyalty_number(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[1]

    broken = replace(
        target,
        loyalty_number=(memberships[0].loyalty_number),
    )

    with pytest.raises(
        ValueError,
        match="duplicate loyalty_number",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_multiple_memberships_per_customer(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    duplicate = replace(
        memberships[0],
        membership_id="mem_duplicate",
        loyalty_number="LOY-DUPLICATE",
    )

    broken = (
        *memberships,
        duplicate,
    )

    with pytest.raises(
        ValueError,
        match="multiple loyalty memberships",
    ):
        validate(
            memberships=broken,
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_unknown_customer(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[0]

    broken = replace(
        target,
        customer_id="cus_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown customer",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_unknown_market(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[0]

    broken = replace(
        target,
        market_code="ZZ",
    )

    with pytest.raises(
        ValueError,
        match="unknown market",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_market_customer_mismatch(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[0]

    different_market = next(
        customer.market_code
        for customer in loyalty_customers
        if (customer.market_code != target.market_code)
    )

    broken = replace(
        target,
        market_code=different_market,
    )

    with pytest.raises(
        ValueError,
        match="does not match customer",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_invalid_tier(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[0]

    broken = replace(
        target,
        tier=cast(
            LoyaltyTier,
            "DIAMOND",
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid tier",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_wrong_loyalty_number(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[0]

    broken = replace(
        target,
        loyalty_number="LOY-WRONG",
    )

    with pytest.raises(
        ValueError,
        match="loyalty number does not match",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_enrolment_on_customer_creation_date(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = memberships[0]

    customer = next(
        customer for customer in loyalty_customers if (customer.customer_id == target.customer_id)
    )

    broken = replace(
        target,
        enrolled_at=customer.created_at,
    )

    with pytest.raises(
        ValueError,
        match="after customer creation",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_enrolment_after_simulation_end(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = next(membership for membership in memberships if membership.closed_at is None)

    broken = replace(
        target,
        enrolled_at=(loyalty_context.config.end_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="after simulation end",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_enrolment_after_customer_deactivation(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = next(membership for membership in memberships if membership.closed_at is not None)

    customer = next(
        customer for customer in loyalty_customers if (customer.customer_id == target.customer_id)
    )

    assert customer.deactivated_at is not None

    broken = replace(
        target,
        enrolled_at=(customer.deactivated_at),
    )

    with pytest.raises(
        ValueError,
        match="customer is not active",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_open_membership_for_deactivated_customer(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = next(membership for membership in memberships if membership.closed_at is not None)

    broken = replace(
        target,
        closed_at=None,
    )

    with pytest.raises(
        ValueError,
        match="closure must match customer deactivation",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_closed_membership_for_active_customer(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = next(membership for membership in memberships if membership.closed_at is None)

    broken = replace(
        target,
        closed_at=(target.enrolled_at + timedelta(days=100)),
    )

    with pytest.raises(
        ValueError,
        match="must remain open",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken,
            ),
            customers=loyalty_customers,
            context=loyalty_context,
        )


def test_rejects_membership_closure_before_enrolment(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = next(membership for membership in memberships if membership.closed_at is not None)

    customer = next(
        customer for customer in loyalty_customers if (customer.customer_id == target.customer_id)
    )

    broken_customer = replace(
        customer,
        deactivated_at=(target.enrolled_at - timedelta(days=1)),
    )

    broken_customers = tuple(
        broken_customer if row.customer_id == customer.customer_id else row
        for row in loyalty_customers
    )

    broken_membership = replace(
        target,
        closed_at=(target.enrolled_at - timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="customer is not active on loyalty enrolment date",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken_membership,
            ),
            customers=broken_customers,
            context=loyalty_context,
        )


def test_rejects_membership_shorter_than_minimum_duration(
    memberships,
    loyalty_customers,
    loyalty_context,
) -> None:
    target = next(membership for membership in memberships if membership.closed_at is not None)

    customer = next(
        customer for customer in loyalty_customers if (customer.customer_id == target.customer_id)
    )

    short_close = target.enrolled_at + timedelta(days=1)

    broken_customer = replace(
        customer,
        deactivated_at=short_close,
    )

    broken_customers = tuple(
        broken_customer if row.customer_id == customer.customer_id else row
        for row in loyalty_customers
    )

    broken_membership = replace(
        target,
        closed_at=short_close,
    )

    with pytest.raises(
        ValueError,
        match="minimum active duration",
    ):
        validate(
            memberships=replace_membership(
                memberships,
                broken_membership,
            ),
            customers=broken_customers,
            context=loyalty_context,
        )
