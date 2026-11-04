from collections import Counter
from datetime import date, timedelta

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.config import (
    DEFAULT_CUSTOMER_CONFIG,
    CustomerSimulationConfig,
)
from mercatura.source.systems.crm.model import (
    Customer,
)


def validate_customers(
    customers: tuple[Customer, ...],
    context: SimulationContext,
    *,
    config: CustomerSimulationConfig = (DEFAULT_CUSTOMER_CONFIG),
) -> None:
    _validate_uniqueness(customers)

    _validate_market_counts(
        customers,
        context,
        config,
    )

    _validate_customer_rows(
        customers,
        context,
        config,
    )


def _validate_uniqueness(
    customers: tuple[Customer, ...],
) -> None:
    customer_ids: list[str] = [customer.customer_id for customer in customers]

    if len(customer_ids) != len(set(customer_ids)):
        raise ValueError("duplicate customer_id detected")

    customer_numbers: list[str] = [customer.customer_number for customer in customers]

    if len(customer_numbers) != len(set(customer_numbers)):
        raise ValueError("duplicate customer_number detected")

    emails: list[str] = [
        customer.email.lower() for customer in customers if customer.email is not None
    ]

    if len(emails) != len(set(emails)):
        raise ValueError("duplicate customer email detected")


def _validate_market_counts(
    customers: tuple[Customer, ...],
    context: SimulationContext,
    config: CustomerSimulationConfig,
) -> None:
    configured_counts: dict[str, int] = {
        population.market_code: population.customer_count for population in config.populations
    }

    actual_counts: Counter[str] = Counter(customer.market_code for customer in customers)

    active_markets: set[str] = {market.market_code for market in context.config.markets}

    for market_code in active_markets:
        expected: int | None = configured_counts.get(market_code)

        if expected is None:
            raise ValueError(f"missing customer population configuration for {market_code}")

        actual: int = actual_counts[market_code]

        if actual != expected:
            raise ValueError("customer count outside simulation configuration")

    unexpected_markets: set[str] = set(actual_counts) - active_markets

    if unexpected_markets:
        raise ValueError("customers reference markets outside simulation configuration")


def _validate_customer_rows(
    customers: tuple[Customer, ...],
    context: SimulationContext,
    config: CustomerSimulationConfig,
) -> None:
    market_codes: set[str] = {market.market_code for market in context.config.markets}

    historical_start: date = context.config.start_date - timedelta(days=365 * config.history_years)

    for customer in customers:
        if customer.market_code not in market_codes:
            raise ValueError(f"{customer.customer_number} references unknown market")

        if customer.country_code != customer.market_code:
            raise ValueError(f"{customer.customer_number} country does not match market")

        if not (customer.customer_number.strip()):
            raise ValueError("customer_number cannot be empty")

        if not (customer.first_name.strip()):
            raise ValueError(f"{customer.customer_number} has empty first_name")

        if not (customer.last_name.strip()):
            raise ValueError(f"{customer.customer_number} has empty last_name")

        if not customer.city.strip():
            raise ValueError(f"{customer.customer_number} has empty city")

        if not customer.region.strip():
            raise ValueError(f"{customer.customer_number} has empty region")

        if not (customer.postal_code.strip()):
            raise ValueError(f"{customer.customer_number} has empty postal_code")

        if customer.email is None and customer.phone is None:
            raise ValueError(f"{customer.customer_number} has no contact method")

        if customer.email is not None and "@" not in customer.email:
            raise ValueError(f"{customer.customer_number} has invalid email")

        if customer.phone is not None and not customer.phone.strip():
            raise ValueError(f"{customer.customer_number} has empty phone")

        if customer.created_at < historical_start:
            raise ValueError(f"{customer.customer_number} was created before configured history")

        if customer.created_at > context.config.end_date:
            raise ValueError(f"{customer.customer_number} was created after simulation end")

        if customer.deactivated_at is not None:
            if customer.deactivated_at <= customer.created_at:
                raise ValueError(f"{customer.customer_number} has invalid lifecycle")

            if customer.deactivated_at > context.config.end_date:
                raise ValueError(f"{customer.customer_number} deactivates after simulation end")

            active_days: int = (customer.deactivated_at - customer.created_at).days

            if active_days < config.minimum_active_days:
                raise ValueError(
                    f"{customer.customer_number} does not satisfy minimum active duration"
                )
