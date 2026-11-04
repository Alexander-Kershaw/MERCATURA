from datetime import date, timedelta

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.loyalty.config import (
    DEFAULT_LOYALTY_CONFIG,
    LoyaltySimulationConfig,
)
from mercatura.source.systems.loyalty.model import (
    LOYALTY_TIERS,
    LoyaltyMembership,
)


def validate_loyalty_memberships(
    memberships: tuple[LoyaltyMembership, ...],
    customers: tuple[Customer, ...],
    context: SimulationContext,
    *,
    config: LoyaltySimulationConfig = (DEFAULT_LOYALTY_CONFIG),
) -> None:
    _validate_uniqueness(memberships)

    _validate_references(
        memberships,
        customers,
        context,
        config,
    )


def _validate_uniqueness(
    memberships: tuple[LoyaltyMembership, ...],
) -> None:
    membership_ids: list[str] = [membership.membership_id for membership in memberships]

    if len(membership_ids) != len(set(membership_ids)):
        raise ValueError("duplicate membership_id detected")

    loyalty_numbers: list[str] = [membership.loyalty_number for membership in memberships]

    if len(loyalty_numbers) != len(set(loyalty_numbers)):
        raise ValueError("duplicate loyalty_number detected")

    customer_ids: list[str] = [membership.customer_id for membership in memberships]

    if len(customer_ids) != len(set(customer_ids)):
        raise ValueError("multiple loyalty memberships exist for customer")


def _validate_references(
    memberships: tuple[LoyaltyMembership, ...],
    customers: tuple[Customer, ...],
    context: SimulationContext,
    config: LoyaltySimulationConfig,
) -> None:
    customers_by_id: dict[str, Customer] = {
        customer.customer_id: customer for customer in customers
    }

    valid_markets: set[str] = {market.market_code for market in context.config.markets}

    valid_tiers = set(LOYALTY_TIERS)

    for membership in memberships:
        customer: Customer | None = customers_by_id.get(membership.customer_id)

        if customer is None:
            raise ValueError("loyalty membership references unknown customer")

        if membership.market_code not in valid_markets:
            raise ValueError("loyalty membership references unknown market")

        if membership.market_code != customer.market_code:
            raise ValueError("loyalty membership market does not match customer")

        if membership.tier not in valid_tiers:
            raise ValueError("loyalty membership has invalid tier")

        expected_number: str = _expected_loyalty_number(customer)

        if membership.loyalty_number != expected_number:
            raise ValueError("loyalty number does not match customer")

        if membership.enrolled_at <= customer.created_at:
            raise ValueError("loyalty enrolment must occur after customer creation")

        if membership.enrolled_at > context.config.end_date:
            raise ValueError("loyalty enrolment occurs after simulation end")

        if not customer.is_active_on(value=membership.enrolled_at):
            raise ValueError("customer is not active on loyalty enrolment date")

        maximum_enrolment_date: date = customer.created_at + timedelta(
            days=(config.maximum_enrolment_lag_days)
        )

        if membership.enrolled_at > maximum_enrolment_date:
            raise ValueError("loyalty enrolment exceeds configured maximum lag")

        _validate_closure(
            membership=membership,
            customer=customer,
            config=config,
        )


def _validate_closure(
    *,
    membership: LoyaltyMembership,
    customer: Customer,
    config: LoyaltySimulationConfig,
) -> None:
    customer_deactivated_at: date | None = customer.deactivated_at

    if customer_deactivated_at is None:
        if membership.closed_at is not None:
            raise ValueError("active customer loyalty membership must remain open")

        return

    membership_closed_at: date | None = membership.closed_at

    if membership_closed_at != customer_deactivated_at:
        raise ValueError("loyalty membership closure must match customer deactivation")

    if membership_closed_at is None:
        raise ValueError("loyalty membership closure must match customer deactivation")

    if membership_closed_at <= membership.enrolled_at:
        raise ValueError("loyalty membership has invalid lifecycle")

    active_days: int = (membership_closed_at - membership.enrolled_at).days

    if active_days < (config.minimum_membership_days_before_closure):
        raise ValueError("loyalty membership does not satisfy minimum active duration")


def _expected_loyalty_number(
    customer: Customer,
) -> str:
    prefix = "CUS-"

    if not (customer.customer_number.startswith(prefix)):
        raise ValueError("customer_number does not use expected CRM format")

    return "LOY-" + customer.customer_number[len(prefix) :]
