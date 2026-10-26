from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True, slots=True)
class MarketConfig:
    market_code: str
    country_name: str
    legal_entity: str
    currency: str
    locale: str
    timezone: str
    tax_regime: str

    def __post_init__(self) -> None:
        if len(self.market_code) != 2 or not self.market_code.isupper():
            raise ValueError("market_code must be a two-character uppercase country code")

        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("currency must be a three-character uppercase currency code")

        if not self.country_name.strip():
            raise ValueError("country_name must not be empty")

        if not self.legal_entity.strip():
            raise ValueError("legal_entity must not be empty")

        if not self.locale.strip():
            raise ValueError("locale must not be empty")

        if not self.tax_regime.strip():
            raise ValueError("tax_regime must not be empty")

        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {self.timezone}") from exc

    def canonical_payload(self) -> dict[str, str]:
        return {
            "market_code": self.market_code,
            "country_name": self.country_name,
            "legal_entity": self.legal_entity,
            "currency": self.currency,
            "locale": self.locale,
            "timezone": self.timezone,
            "tax_regime": self.tax_regime,
        }


"""
========================================================================================

MARKETS

========================================================================================

Markets being used throughout the project include:

- United Kingdom
- Germany
- United States
- China
- Norway
- Russia

========================================================================================
"""

DEFAULT_MARKETS: tuple[MarketConfig, ...] = (
    MarketConfig(
        market_code="GB",
        country_name="United Kingdom",
        legal_entity="Mercatura UK Ltd",
        currency="GBP",
        locale="en_GB",
        timezone="Europe/London",
        tax_regime="GB_VAT",
    ),
    MarketConfig(
        market_code="DE",
        country_name="Germany",
        legal_entity="Mercatura Deutschland GmbH",
        currency="EUR",
        locale="de_DE",
        timezone="Europe/Berlin",
        tax_regime="DE_VAT",
    ),
    MarketConfig(
        market_code="US",
        country_name="United States",
        legal_entity="Mercatura USA Inc",
        currency="USD",
        locale="en_US",
        timezone="America/New_York",
        tax_regime="US_SALES_TAX",
    ),
    MarketConfig(
        market_code="CN",
        country_name="China",
        legal_entity="Mercatura China Co Ltd",
        currency="CNY",
        locale="zh_CN",
        timezone="Asia/Shanghai",
        tax_regime="CN_VAT",
    ),
    MarketConfig(
        market_code="NO",
        country_name="Norway",
        legal_entity="Mercatura Norge AS",
        currency="NOK",
        locale="no_NO",
        timezone="Europe/Oslo",
        tax_regime="NO_VAT",
    ),
    MarketConfig(
        market_code="RU",
        country_name="Russia",
        legal_entity="Mercatura Russia LLC",
        currency="RUB",
        locale="ru_RU",
        timezone="Europe/Moscow",
        tax_regime="RU_VAT",
    ),
    MarketConfig(
        market_code="JP",
        country_name="Japan",
        legal_entity="Mercatura Japan Co Ltd",
        currency="JPY",
        locale="ja_JP",
        timezone="Asia/Tokyo",
        tax_regime="JP_CONSUMPTION_TAX",
    ),
    MarketConfig(
        market_code="KR",
        country_name="South Korea",
        legal_entity="Mercatura Korea Co Ltd",
        currency="KRW",
        locale="ko_KR",
        timezone="Asia/Seoul",
        tax_regime="KR_VAT",
    ),
    MarketConfig(
        market_code="FR",
        country_name="France",
        legal_entity="Mercatura France SAS",
        currency="EUR",
        locale="fr_FR",
        timezone="Europe/Paris",
        tax_regime="FR_VAT",
    ),
    MarketConfig(
        market_code="NL",
        country_name="Netherlands",
        legal_entity="Mercatura Nederland BV",
        currency="EUR",
        locale="nl_NL",
        timezone="Europe/Amsterdam",
        tax_regime="NL_VAT",
    ),
    MarketConfig(
        market_code="PL",
        country_name="Poland",
        legal_entity="Mercatura Polska Sp z oo",
        currency="PLN",
        locale="pl_PL",
        timezone="Europe/Warsaw",
        tax_regime="PL_VAT",
    ),
)
