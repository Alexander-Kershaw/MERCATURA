from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.crm.validation import (
    validate_customers,
)


def replace_customer(
    customers: tuple[Customer, ...],
    replacement: Customer,
) -> tuple[Customer, ...]:
    return tuple(
        replacement if customer.customer_id == replacement.customer_id else customer
        for customer in customers
    )


def validate(
    *,
    customers: tuple[Customer, ...],
    context: SimulationContext,
) -> None:
    validate_customers(
        customers,
        context,
    )


def test_valid_dataset_passes(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    validate(
        customers=customers,
        context=crm_context,
    )


def test_rejects_duplicate_customer_id(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    broken = (
        *customers,
        customers[0],
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate customer_id",
    ):
        validate(
            customers=broken,
            context=crm_context,
        )


def test_rejects_duplicate_customer_number(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target: Customer = customers[1]

    broken_customer: Customer = replace(
        target,
        customer_number=(customers[0].customer_number),
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate customer_number",
    ):
        validate(
            customers=replace_customer(
                customers,
                replacement=broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_duplicate_email(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    first: Customer = next(customer for customer in customers if customer.email is not None)

    second: Customer = next(
        customer
        for customer in customers
        if (customer.customer_id != first.customer_id and customer.email is not None)
    )

    broken_customer: Customer = replace(
        second,
        email=first.email,
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="duplicate customer email",
    ):
        validate(
            customers=replace_customer(
                customers,
                replacement=broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_unknown_market(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target: Customer = customers[0]

    broken_customer: Customer = replace(
        target,
        market_code="ZZ",
        country_code="ZZ",
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="customer count outside simulation configuration",
    ):
        validate(
            customers=replace_customer(
                customers,
                replacement=broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_country_market_mismatch(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target: Customer = customers[0]

    broken_customer: Customer = replace(
        target,
        country_code="ZZ",
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="country does not match market",
    ):
        validate(
            customers=replace_customer(
                customers,
                replacement=broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_empty_first_name(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target: Customer = customers[0]

    broken_customer: Customer = replace(
        target,
        first_name="",
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="empty first_name",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_empty_last_name(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        last_name="",
    )

    with pytest.raises(
        ValueError,
        match="empty last_name",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_customer_without_contact_method(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        email=None,
        phone=None,
    )

    with pytest.raises(
        ValueError,
        match="no contact method",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_invalid_email(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        email="not-an-email",
    )

    with pytest.raises(
        ValueError,
        match="invalid email",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_creation_after_simulation_end(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        created_at=(crm_context.config.end_date + timedelta(days=1)),
        deactivated_at=None,
    )

    with pytest.raises(
        ValueError,
        match="created after simulation end",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_deactivation_before_creation(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        deactivated_at=(target.created_at),
    )

    with pytest.raises(
        ValueError,
        match="invalid lifecycle",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_deactivation_after_simulation_end(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        deactivated_at=(crm_context.config.end_date + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="deactivates after simulation end",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_too_short_customer_lifecycle(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = next(
        customer
        for customer in customers
        if (customer.created_at < crm_context.config.end_date - timedelta(days=10))
    )

    broken_customer = replace(
        target,
        deactivated_at=(target.created_at + timedelta(days=1)),
    )

    with pytest.raises(
        ValueError,
        match="minimum active duration",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_empty_city(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        city="",
    )

    with pytest.raises(
        ValueError,
        match="empty city",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )


def test_rejects_empty_postal_code(
    customers: tuple[Customer, ...],
    crm_context: SimulationContext,
) -> None:
    target = customers[0]

    broken_customer = replace(
        target,
        postal_code="",
    )

    with pytest.raises(
        ValueError,
        match="empty postal_code",
    ):
        validate(
            customers=replace_customer(
                customers,
                broken_customer,
            ),
            context=crm_context,
        )
