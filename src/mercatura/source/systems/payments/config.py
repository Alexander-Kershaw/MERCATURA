from dataclasses import dataclass

from mercatura.source.systems.payments.model import (
    BankPaymentRail,
    CardNetwork,
    WalletProvider,
)


def _validate_probability(
    probability: float,
    name: str,
) -> None:
    if not (0.0 <= probability <= 1.0):
        raise ValueError(f"{name} must be between 0 and 1")


def _validate_distribution(
    probabilities: tuple[float, ...],
    name: str,
) -> None:
    if not probabilities:
        raise ValueError(f"{name} cannot be empty")

    if any(probability < 0.0 or probability > 1.0 for probability in probabilities):
        raise ValueError(f"{name} must contain values between 0 and 1")

    if abs(sum(probabilities) - 1.0) > 1e-9:
        raise ValueError(f"{name} must sum to 1")


def _validate_weighted_options(
    *,
    options: tuple[str, ...],
    weights: tuple[float, ...],
    name: str,
) -> None:
    if not options:
        raise ValueError(f"{name} cannot be empty")

    if len(options) != len(weights):
        raise ValueError(f"{name} options and weights must have equal length")

    if len(options) != len(set(options)):
        raise ValueError(f"{name} options must be unique")

    _validate_distribution(
        weights,
        f"{name} weights",
    )


def _validate_positive_range(
    *,
    minimum: int,
    maximum: int,
    name: str,
) -> None:
    if minimum < 0:
        raise ValueError(f"{name} minimum must be non-negative")

    if maximum < minimum:
        raise ValueError(f"{name} maximum must not be below minimum")


@dataclass(frozen=True, slots=True)
class MarketPaymentProfile:
    market_code: str

    store_card_probability: float
    store_wallet_probability: float
    store_bank_payment_probability: float

    digital_card_probability: float
    digital_wallet_probability: float
    digital_bank_payment_probability: float

    card_networks: tuple[CardNetwork, ...]

    card_network_weights: tuple[float, ...]

    wallet_providers: tuple[WalletProvider, ...]

    wallet_provider_weights: tuple[float, ...]

    bank_payment_rails: tuple[BankPaymentRail, ...]

    bank_payment_rail_weights: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.market_code.strip():
            raise ValueError("market_code cannot be empty")

        _validate_distribution(
            (
                self.store_card_probability,
                self.store_wallet_probability,
                self.store_bank_payment_probability,
            ),
            (f"{self.market_code} store payment method probabilities"),
        )

        _validate_distribution(
            (
                self.digital_card_probability,
                self.digital_wallet_probability,
                self.digital_bank_payment_probability,
            ),
            (f"{self.market_code} digital payment method probabilities"),
        )

        _validate_weighted_options(
            options=self.card_networks,
            weights=self.card_network_weights,
            name="card_networks",
        )

        _validate_weighted_options(
            options=self.wallet_providers,
            weights=self.wallet_provider_weights,
            name="wallet_providers",
        )

        _validate_weighted_options(
            options=self.bank_payment_rails,
            weights=self.bank_payment_rail_weights,
            name="bank_payment_rails",
        )


DEFAULT_MARKET_PAYMENT_PROFILES: tuple[MarketPaymentProfile, ...] = (
    MarketPaymentProfile(
        market_code="GB",
        store_card_probability=0.76,
        store_wallet_probability=0.23,
        store_bank_payment_probability=0.01,
        digital_card_probability=0.58,
        digital_wallet_probability=0.34,
        digital_bank_payment_probability=0.08,
        card_networks=(
            "VISA",
            "MASTERCARD",
            "AMEX",
        ),
        card_network_weights=(
            0.59,
            0.39,
            0.02,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
            "PAYPAL",
        ),
        wallet_provider_weights=(
            0.40,
            0.30,
            0.30,
        ),
        bank_payment_rails=(
            "FASTER_PAYMENTS",
            "OPEN_BANKING",
        ),
        bank_payment_rail_weights=(
            0.45,
            0.55,
        ),
    ),
    MarketPaymentProfile(
        market_code="DE",
        store_card_probability=0.78,
        store_wallet_probability=0.21,
        store_bank_payment_probability=0.01,
        digital_card_probability=0.52,
        digital_wallet_probability=0.33,
        digital_bank_payment_probability=0.15,
        card_networks=(
            "VISA",
            "MASTERCARD",
            "AMEX",
        ),
        card_network_weights=(
            0.52,
            0.45,
            0.03,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
            "PAYPAL",
        ),
        wallet_provider_weights=(
            0.35,
            0.25,
            0.40,
        ),
        bank_payment_rails=("SEPA",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="US",
        store_card_probability=0.80,
        store_wallet_probability=0.19,
        store_bank_payment_probability=0.01,
        digital_card_probability=0.63,
        digital_wallet_probability=0.34,
        digital_bank_payment_probability=0.03,
        card_networks=(
            "VISA",
            "MASTERCARD",
            "AMEX",
            "DISCOVER",
        ),
        card_network_weights=(
            0.66,
            0.27,
            0.05,
            0.02,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
            "PAYPAL",
        ),
        wallet_provider_weights=(
            0.45,
            0.25,
            0.30,
        ),
        bank_payment_rails=("ACH",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="CN",
        store_card_probability=0.35,
        store_wallet_probability=0.63,
        store_bank_payment_probability=0.02,
        digital_card_probability=0.25,
        digital_wallet_probability=0.70,
        digital_bank_payment_probability=0.05,
        card_networks=(
            "UNIONPAY",
            "VISA",
            "MASTERCARD",
        ),
        card_network_weights=(
            0.85,
            0.08,
            0.07,
        ),
        wallet_providers=(
            "ALIPAY",
            "WECHAT_PAY",
        ),
        wallet_provider_weights=(
            0.52,
            0.48,
        ),
        bank_payment_rails=("LOCAL_BANK_TRANSFER",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="NO",
        store_card_probability=0.72,
        store_wallet_probability=0.27,
        store_bank_payment_probability=0.01,
        digital_card_probability=0.48,
        digital_wallet_probability=0.37,
        digital_bank_payment_probability=0.15,
        card_networks=(
            "VISA",
            "MASTERCARD",
        ),
        card_network_weights=(
            0.60,
            0.40,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
        ),
        wallet_provider_weights=(
            0.55,
            0.45,
        ),
        bank_payment_rails=(
            "SEPA",
            "LOCAL_BANK_TRANSFER",
        ),
        bank_payment_rail_weights=(
            0.70,
            0.30,
        ),
    ),
    MarketPaymentProfile(
        market_code="RU",
        store_card_probability=0.72,
        store_wallet_probability=0.25,
        store_bank_payment_probability=0.03,
        digital_card_probability=0.45,
        digital_wallet_probability=0.35,
        digital_bank_payment_probability=0.20,
        card_networks=(
            "MIR",
            "VISA",
            "MASTERCARD",
        ),
        card_network_weights=(
            0.85,
            0.08,
            0.07,
        ),
        wallet_providers=("MIR_PAY",),
        wallet_provider_weights=(1.0,),
        bank_payment_rails=("SBP",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="JP",
        store_card_probability=0.70,
        store_wallet_probability=0.28,
        store_bank_payment_probability=0.02,
        digital_card_probability=0.45,
        digital_wallet_probability=0.50,
        digital_bank_payment_probability=0.05,
        card_networks=(
            "VISA",
            "MASTERCARD",
            "JCB",
            "AMEX",
        ),
        card_network_weights=(
            0.45,
            0.30,
            0.20,
            0.05,
        ),
        wallet_providers=(
            "PAYPAY",
            "APPLE_PAY",
            "GOOGLE_PAY",
        ),
        wallet_provider_weights=(
            0.50,
            0.30,
            0.20,
        ),
        bank_payment_rails=("LOCAL_BANK_TRANSFER",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="KR",
        store_card_probability=0.55,
        store_wallet_probability=0.43,
        store_bank_payment_probability=0.02,
        digital_card_probability=0.35,
        digital_wallet_probability=0.60,
        digital_bank_payment_probability=0.05,
        card_networks=(
            "VISA",
            "MASTERCARD",
            "AMEX",
        ),
        card_network_weights=(
            0.55,
            0.40,
            0.05,
        ),
        wallet_providers=(
            "KAKAO_PAY",
            "NAVER_PAY",
            "SAMSUNG_PAY",
        ),
        wallet_provider_weights=(
            0.40,
            0.30,
            0.30,
        ),
        bank_payment_rails=("LOCAL_BANK_TRANSFER",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="FR",
        store_card_probability=0.78,
        store_wallet_probability=0.21,
        store_bank_payment_probability=0.01,
        digital_card_probability=0.55,
        digital_wallet_probability=0.35,
        digital_bank_payment_probability=0.10,
        card_networks=(
            "VISA",
            "MASTERCARD",
            "AMEX",
        ),
        card_network_weights=(
            0.55,
            0.42,
            0.03,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
            "PAYPAL",
        ),
        wallet_provider_weights=(
            0.40,
            0.30,
            0.30,
        ),
        bank_payment_rails=("SEPA",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="NL",
        store_card_probability=0.72,
        store_wallet_probability=0.27,
        store_bank_payment_probability=0.01,
        digital_card_probability=0.28,
        digital_wallet_probability=0.32,
        digital_bank_payment_probability=0.40,
        card_networks=(
            "VISA",
            "MASTERCARD",
        ),
        card_network_weights=(
            0.55,
            0.45,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
            "PAYPAL",
        ),
        wallet_provider_weights=(
            0.35,
            0.25,
            0.40,
        ),
        bank_payment_rails=("IDEAL",),
        bank_payment_rail_weights=(1.0,),
    ),
    MarketPaymentProfile(
        market_code="PL",
        store_card_probability=0.72,
        store_wallet_probability=0.25,
        store_bank_payment_probability=0.03,
        digital_card_probability=0.35,
        digital_wallet_probability=0.30,
        digital_bank_payment_probability=0.35,
        card_networks=(
            "VISA",
            "MASTERCARD",
        ),
        card_network_weights=(
            0.55,
            0.45,
        ),
        wallet_providers=(
            "APPLE_PAY",
            "GOOGLE_PAY",
        ),
        wallet_provider_weights=(
            0.55,
            0.45,
        ),
        bank_payment_rails=(
            "BLIK",
            "LOCAL_BANK_TRANSFER",
        ),
        bank_payment_rail_weights=(
            0.75,
            0.25,
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class PaymentSimulationConfig:
    market_profiles: tuple[MarketPaymentProfile, ...] = DEFAULT_MARKET_PAYMENT_PROFILES

    failed_attempt_count_probabilities: tuple[float, ...] = (
        0.92,
        0.07,
        0.01,
    )

    debit_probability: float = 0.62
    credit_probability: float = 0.34
    prepaid_probability: float = 0.04

    northstar_processor_probability: float = 0.70
    atlas_processor_probability: float = 0.20
    horizon_processor_probability: float = 0.10

    store_contactless_probability: float = 0.72

    three_ds_challenge_probability: float = 0.18

    insufficient_funds_probability: float = 0.40
    do_not_honour_probability: float = 0.30
    limit_exceeded_probability: float = 0.20
    processor_error_probability: float = 0.10

    minimum_retry_delay_seconds: int = 30
    maximum_retry_delay_seconds: int = 600

    minimum_store_capture_delay_seconds: int = 5
    maximum_store_capture_delay_seconds: int = 90

    minimum_digital_capture_delay_seconds: int = 30
    maximum_digital_capture_delay_seconds: int = 600

    def __post_init__(self) -> None:
        market_codes = [profile.market_code for profile in self.market_profiles]

        if len(market_codes) != len(set(market_codes)):
            raise ValueError("payment market profiles must be unique")

        _validate_distribution(
            self.failed_attempt_count_probabilities,
            "failed attempt count probabilities",
        )

        _validate_distribution(
            (
                self.debit_probability,
                self.credit_probability,
                self.prepaid_probability,
            ),
            "card funding probabilities",
        )

        _validate_distribution(
            (
                self.northstar_processor_probability,
                self.atlas_processor_probability,
                self.horizon_processor_probability,
            ),
            "processor probabilities",
        )

        _validate_probability(
            self.store_contactless_probability,
            "store_contactless_probability",
        )

        _validate_probability(
            self.three_ds_challenge_probability,
            "three_ds_challenge_probability",
        )

        _validate_distribution(
            (
                self.insufficient_funds_probability,
                self.do_not_honour_probability,
                self.limit_exceeded_probability,
                self.processor_error_probability,
            ),
            "decline reason probabilities",
        )

        _validate_positive_range(
            minimum=(self.minimum_retry_delay_seconds),
            maximum=(self.maximum_retry_delay_seconds),
            name="retry delay",
        )

        _validate_positive_range(
            minimum=(self.minimum_store_capture_delay_seconds),
            maximum=(self.maximum_store_capture_delay_seconds),
            name="store capture delay",
        )

        _validate_positive_range(
            minimum=(self.minimum_digital_capture_delay_seconds),
            maximum=(self.maximum_digital_capture_delay_seconds),
            name="digital capture delay",
        )


DEFAULT_PAYMENT_CONFIG = PaymentSimulationConfig()
