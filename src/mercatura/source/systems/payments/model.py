from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

"""
===========================================================================================

PAYMENTS MODEL

===========================================================================================

The PaymentAttempt dataclass contains attributes that retail an attempted payment 
transfer. It considers that payments may be successful, or may fail, and the processes
and actions associated with payment transfers. The card networks, wallet providers, and 
bank payment rails consider the market in which the customer is in.

------------------------------------------------------------------------------------------

PaymentMethod is a data structure holding the methods of payments being considered:

- CARD: debit or credit card payment
- DIGITAL_WALLET: payments made with a digital wallet
- BANK_PAYMENT: payments made with a bank transfer payment

------------------------------------------------------------------------------------------

PaymentStatus captures the payment status:

- DECLINE
- CAPTURED
- VOIDED

------------------------------------------------------------------------------------------

CardNetwork contains the considered Card payment networks

- VISA
- MASTERCARD
- AMEX
- DISCOVER
- JCB
- UNIONPAY
- MIR

------------------------------------------------------------------------------------------

CardFundingType describes the type of payment

- DEBIT
- CREDIT
- PREPAID

------------------------------------------------------------------------------------------

CardPresence describes if a card is present in the transaction or not

- CARD_PRESENT
- CARD_NOT_PRESENT

------------------------------------------------------------------------------------------

WalletProvider, for wallet based transactions the provider is known

- APPLE_PAY
- GOOGLE_PAY
- PAYPAL
- ALIPAY
- WECHAT_PAY
- MIR_PAY
- PAYPAY
- KAKAO_PAY
- NAVER_PAY
- SAMSUNG_PAY

------------------------------------------------------------------------------------------

BankPaymentRail, for bank payments

- FASTER_PAYMENTS
- OPEN_BANKING
- SEPA
- ACH
- LOCAL_BANK_TRANSFER
- SBP
- IDEAL
- BLIK

------------------------------------------------------------------------------------------

PaymentEntryMode, describes the actual payment entry method

- CONTACTLESS
- CHIP_PIN
- ECOMMERCE
- WALLET_TOKEN
- BANK_REDIRECT

------------------------------------------------------------------------------------------

AuthenticationResult, the authentication status of the payment

- NOT_APPLICABLE
- 3DS_FRICTIONLESS
- 3DS_CHALLENGE
- WALLET_AUTHENTICATED
- BANK_AUTHENTICATED

------------------------------------------------------------------------------------------

PaymentProcessor, these are just 3 synthetic PSP/aquirer names

- NORTHSTAR_PAYMENTS
- ATLAS_ACQUIRING
- HORIZON_PAYMENTS

------------------------------------------------------------------------------------------

DeclineType, the severity of the payment decline

- SOFT
- HARD

------------------------------------------------------------------------------------------

DeclineReason, describes the reasoning behind a declined payment

- INSUFFICIENT_FUNDS
- DO_NOT_HONOUR
- LIMIT_EXCEEDED
- PROCESSOR_ERROR
- EXPIRED_INSTRUMENT
- NVALID_DETAILS
- SUSPECTED_FRAUD

------------------------------------------------------------------------------------------

Payments is quite a rich data entity as a result of this enriched detail. I have elected
to have more complexity for payments for future financial reconcilliation, profiling, 
potential fraud detection features, and stronger exercising of data quality rules.

Since payment initiation, authorization, capture, decline, voids etc... is included in the 
model I am using datetimes rather than just date to capture the series of payment events 
that typically occur over second / minutes rather than over dates.

Furthermore, payments methods are market specific: for instance, CN/KR may favour wallets
more heavily, whereas NL/PL may have more account-to-account usage. 

===========================================================================================
"""

PaymentMethod = Literal[
    "CARD",
    "DIGITAL_WALLET",
    "BANK_PAYMENT",
]


PaymentStatus = Literal[
    "DECLINED",
    "CAPTURED",
    "VOIDED",
]


CardNetwork = Literal[
    "VISA",
    "MASTERCARD",
    "AMEX",
    "DISCOVER",
    "JCB",
    "UNIONPAY",
    "MIR",
]


CardFundingType = Literal[
    "DEBIT",
    "CREDIT",
    "PREPAID",
]


CardPresence = Literal[
    "CARD_PRESENT",
    "CARD_NOT_PRESENT",
]


WalletProvider = Literal[
    "APPLE_PAY",
    "GOOGLE_PAY",
    "PAYPAL",
    "ALIPAY",
    "WECHAT_PAY",
    "MIR_PAY",
    "PAYPAY",
    "KAKAO_PAY",
    "NAVER_PAY",
    "SAMSUNG_PAY",
]


BankPaymentRail = Literal[
    "FASTER_PAYMENTS",
    "OPEN_BANKING",
    "SEPA",
    "ACH",
    "LOCAL_BANK_TRANSFER",
    "SBP",
    "IDEAL",
    "BLIK",
]


PaymentEntryMode = Literal[
    "CONTACTLESS",
    "CHIP_PIN",
    "ECOMMERCE",
    "WALLET_TOKEN",
    "BANK_REDIRECT",
]


AuthenticationResult = Literal[
    "NOT_APPLICABLE",
    "3DS_FRICTIONLESS",
    "3DS_CHALLENGE",
    "WALLET_AUTHENTICATED",
    "BANK_AUTHENTICATED",
]


PaymentProcessor = Literal[
    "NORTHSTAR_PAYMENTS",
    "ATLAS_ACQUIRING",
    "HORIZON_PAYMENTS",
]


DeclineType = Literal[
    "SOFT",
    "HARD",
]


DeclineReason = Literal[
    "INSUFFICIENT_FUNDS",
    "DO_NOT_HONOUR",
    "LIMIT_EXCEEDED",
    "PROCESSOR_ERROR",
    "EXPIRED_INSTRUMENT",
    "INVALID_DETAILS",
    "SUSPECTED_FRAUD",
]


PAYMENT_METHODS: tuple[PaymentMethod, ...] = (
    "CARD",
    "DIGITAL_WALLET",
    "BANK_PAYMENT",
)


PAYMENT_STATUSES: tuple[PaymentStatus, ...] = (
    "DECLINED",
    "CAPTURED",
    "VOIDED",
)


CARD_NETWORKS: tuple[CardNetwork, ...] = (
    "VISA",
    "MASTERCARD",
    "AMEX",
    "DISCOVER",
    "JCB",
    "UNIONPAY",
    "MIR",
)


CARD_FUNDING_TYPES: tuple[CardFundingType, ...] = (
    "DEBIT",
    "CREDIT",
    "PREPAID",
)


PAYMENT_PROCESSORS: tuple[PaymentProcessor, ...] = (
    "NORTHSTAR_PAYMENTS",
    "ATLAS_ACQUIRING",
    "HORIZON_PAYMENTS",
)


@dataclass(frozen=True, slots=True)
class PaymentAttempt:
    payment_id: str
    payment_reference: str
    processor_reference: str
    order_id: str
    attempt_number: int
    market_code: str
    currency: str
    amount: Decimal
    payment_method: PaymentMethod
    processor: PaymentProcessor
    card_network: CardNetwork | None
    card_funding_type: CardFundingType | None
    card_last_four: str | None
    card_presence: CardPresence | None
    wallet_provider: WalletProvider | None
    bank_payment_rail: BankPaymentRail | None
    payment_token: str | None
    entry_mode: PaymentEntryMode
    authentication_result: AuthenticationResult
    payment_status: PaymentStatus
    decline_reason: DeclineReason | None
    decline_type: DeclineType | None
    initiated_at: datetime
    authorized_at: datetime | None
    captured_at: datetime | None
    declined_at: datetime | None
    voided_at: datetime | None
