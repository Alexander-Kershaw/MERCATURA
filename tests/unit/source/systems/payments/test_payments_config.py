from dataclasses import replace

import pytest

from mercatura.source.systems.payments.config import (
    DEFAULT_MARKET_PAYMENT_PROFILES,
    MarketPaymentProfile,
    PaymentSimulationConfig,
)


def test_default_market_profiles_cover_11_markets() -> None:
    assert len(DEFAULT_MARKET_PAYMENT_PROFILES) == 11


def test_market_codes_are_unique() -> None:
    market_codes = [profile.market_code for profile in DEFAULT_MARKET_PAYMENT_PROFILES]

    assert len(market_codes) == len(set(market_codes))


def test_rejects_empty_market_code() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="market_code",
    ):
        replace(
            profile,
            market_code="",
        )


def test_rejects_invalid_store_method_distribution() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="store payment method probabilities",
    ):
        replace(
            profile,
            store_card_probability=0.90,
            store_wallet_probability=0.20,
            store_bank_payment_probability=0.10,
        )


def test_rejects_invalid_digital_method_distribution() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="digital payment method probabilities",
    ):
        replace(
            profile,
            digital_card_probability=0.10,
            digital_wallet_probability=0.10,
            digital_bank_payment_probability=0.10,
        )


def test_rejects_empty_card_networks() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="card_networks",
    ):
        replace(
            profile,
            card_networks=(),
        )


def test_rejects_empty_wallet_providers() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="wallet_providers",
    ):
        replace(
            profile,
            wallet_providers=(),
        )


def test_rejects_empty_bank_payment_rails() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="bank_payment_rails",
    ):
        replace(
            profile,
            bank_payment_rails=(),
        )


def test_rejects_duplicate_market_profiles() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="must be unique",
    ):
        PaymentSimulationConfig(
            market_profiles=(
                profile,
                profile,
            )
        )


def test_rejects_bad_failed_attempt_distribution() -> None:
    with pytest.raises(
        ValueError,
        match="failed attempt count probabilities",
    ):
        PaymentSimulationConfig(
            failed_attempt_count_probabilities=(
                0.50,
                0.20,
            )
        )


def test_rejects_bad_card_funding_distribution() -> None:
    with pytest.raises(
        ValueError,
        match="card funding probabilities",
    ):
        PaymentSimulationConfig(
            debit_probability=0.5,
            credit_probability=0.5,
            prepaid_probability=0.5,
        )


def test_rejects_bad_processor_distribution() -> None:
    with pytest.raises(
        ValueError,
        match="processor probabilities",
    ):
        PaymentSimulationConfig(
            northstar_processor_probability=0.5,
            atlas_processor_probability=0.5,
            horizon_processor_probability=0.5,
        )


def test_rejects_invalid_contactless_probability() -> None:
    with pytest.raises(
        ValueError,
        match="store_contactless_probability",
    ):
        PaymentSimulationConfig(store_contactless_probability=1.01)


def test_rejects_invalid_3ds_probability() -> None:
    with pytest.raises(
        ValueError,
        match="three_ds_challenge_probability",
    ):
        PaymentSimulationConfig(three_ds_challenge_probability=-0.01)


def test_rejects_retry_range_inversion() -> None:
    with pytest.raises(
        ValueError,
        match="retry delay maximum",
    ):
        PaymentSimulationConfig(
            minimum_retry_delay_seconds=600,
            maximum_retry_delay_seconds=30,
        )


def test_rejects_negative_capture_delay() -> None:
    with pytest.raises(
        ValueError,
        match="store capture delay minimum",
    ):
        PaymentSimulationConfig(minimum_store_capture_delay_seconds=-1)


def test_market_profile_can_be_constructed() -> None:
    profile = MarketPaymentProfile(
        market_code="XX",
        store_card_probability=0.7,
        store_wallet_probability=0.2,
        store_bank_payment_probability=0.1,
        digital_card_probability=0.5,
        digital_wallet_probability=0.3,
        digital_bank_payment_probability=0.2,
        card_networks=("VISA",),
        card_network_weights=(1.0,),
        wallet_providers=("APPLE_PAY",),
        wallet_provider_weights=(1.0,),
        bank_payment_rails=("SEPA",),
        bank_payment_rail_weights=(1.0,),
    )

    assert profile.market_code == "XX"


def test_rejects_card_network_weight_length_mismatch() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="options and weights must have equal length",
    ):
        replace(
            profile,
            card_network_weights=(1.0,),
        )


def test_rejects_wallet_weight_length_mismatch() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="options and weights must have equal length",
    ):
        replace(
            profile,
            wallet_provider_weights=(1.0,),
        )


def test_rejects_bank_rail_weight_length_mismatch() -> None:
    profile = DEFAULT_MARKET_PAYMENT_PROFILES[0]

    with pytest.raises(
        ValueError,
        match="options and weights must have equal length",
    ):
        replace(
            profile,
            bank_payment_rail_weights=(),
        )
