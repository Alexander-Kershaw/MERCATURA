from collections import Counter
from datetime import timedelta

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.generator import (
    generate_customers,
)
from mercatura.source.systems.crm.model import (
    Customer,
)

EXPECTED_COUNTS: dict[str, int] = {
    "GB": 8_500,
    "DE": 5_200,
    "US": 8_200,
    "CN": 6_000,
    "NO": 1_200,
    "RU": 3_200,
    "JP": 4_300,
    "KR": 3_400,
    "FR": 5_000,
    "NL": 2_400,
    "PL": 2_700,
}


def test_generation_is_deterministic(
    crm_context: SimulationContext,
) -> None:
    first: tuple[Customer, ...] = generate_customers(context=crm_context)

    second: tuple[Customer, ...] = generate_customers(context=crm_context)

    assert first == second


def test_expected_customer_count(
    customers: tuple[Customer, ...],
) -> None:
    assert len(customers) == 50_100


def test_expected_counts_by_market(
    customers: tuple[Customer, ...],
) -> None:
    counts: Counter[str] = Counter(customer.market_code for customer in customers)

    assert dict(counts) == (EXPECTED_COUNTS)


def test_customer_ids_are_unique(
    customers: tuple[Customer, ...],
) -> None:
    identifiers: list[str] = [customer.customer_id for customer in customers]

    assert len(identifiers) == len(set(identifiers))


def test_customer_numbers_are_unique(
    customers: tuple[Customer, ...],
) -> None:
    numbers = [customer.customer_number for customer in customers]

    assert len(numbers) == len(set(numbers))


def test_emails_are_unique_when_present(
    customers: tuple[Customer, ...],
) -> None:
    emails: list[str] = [customer.email for customer in customers if customer.email is not None]

    assert len(emails) == len(set(emails))


def test_every_customer_has_contact_method(
    customers: tuple[Customer, ...],
) -> None:
    assert all(customer.email is not None or customer.phone is not None for customer in customers)


def test_historical_customers_exist(
    crm_context: SimulationContext,
    customers: tuple[Customer, ...],
) -> None:
    assert any(customer.created_at < crm_context.config.start_date for customer in customers)


def test_new_customers_exist_during_simulation(
    crm_context: SimulationContext,
    customers: tuple[Customer, ...],
) -> None:
    assert any((customer.created_at >= crm_context.config.start_date) for customer in customers)


def test_deactivated_customers_exist(
    customers: tuple[Customer, ...],
) -> None:
    assert any(customer.deactivated_at is not None for customer in customers)


def test_active_customers_exist(
    customers: tuple[Customer, ...],
) -> None:
    assert any(customer.is_current for customer in customers)


def test_missing_email_examples_exist(
    customers: tuple[Customer, ...],
) -> None:
    assert any(customer.email is None for customer in customers)


def test_missing_phone_examples_exist(
    customers: tuple[Customer, ...],
) -> None:
    assert any(customer.phone is None for customer in customers)


def test_country_matches_market(
    customers: tuple[Customer, ...],
) -> None:
    assert all(customer.country_code == customer.market_code for customer in customers)


def test_customer_is_active_on_creation_date(
    customers: tuple[Customer, ...],
) -> None:
    assert all(customer.is_active_on(value=customer.created_at) for customer in customers)


def test_deactivated_customer_is_not_active_on_deactivation_date(
    customers: tuple[Customer, ...],
) -> None:
    deactivated: Customer = next(
        customer for customer in customers if (customer.deactivated_at is not None)
    )

    assert deactivated.deactivated_at is not None

    assert not (deactivated.is_active_on(value=deactivated.deactivated_at))


def test_customer_not_active_before_creation(
    customers: tuple[Customer, ...],
) -> None:
    customer = customers[0]

    assert not customer.is_active_on(customer.created_at - timedelta(days=1))
