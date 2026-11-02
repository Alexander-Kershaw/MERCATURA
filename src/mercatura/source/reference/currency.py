from decimal import Decimal

CURRENCY_MINOR_UNITS: dict[str, Decimal] = {
    "GBP": Decimal(value="0.01"),
    "EUR": Decimal(value="0.01"),
    "USD": Decimal(value="0.01"),
    "CNY": Decimal(value="0.01"),
    "NOK": Decimal(value="0.01"),
    "RUB": Decimal(value="0.01"),
    "JPY": Decimal(value="1"),
    "KRW": Decimal(value="1"),
    "PLN": Decimal(value="0.01"),
}
