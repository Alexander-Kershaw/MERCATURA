import random
import re
import unicodedata
from collections import defaultdict
from datetime import date, timedelta
from typing import Literal, Protocol, cast

from faker import Faker

from mercatura.source.reference.customer_geography import (
    CUSTOMER_GEOGRAPHIES,
    CustomerGeography,
)
from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.crm.config import (
    DEFAULT_CUSTOMER_CONFIG,
    CustomerPopulation,
    CustomerSimulationConfig,
)
from mercatura.source.systems.crm.model import (
    Customer,
)


class _CustomerFaker(Protocol):
    def seed_instance(
        self,
        seed: int,
    ) -> None: ...

    def first_name(
        self,
    ) -> str: ...

    def last_name(
        self,
    ) -> str: ...

    def postcode(
        self,
    ) -> str: ...

    def phone_number(
        self,
    ) -> str: ...


EMAIL_DOMAINS_BY_MARKET: dict[
    str,
    tuple[str, ...],
] = {
    "GB": (
        "gmail.com",
        "outlook.com",
        "hotmail.co.uk",
        "icloud.com",
        "yahoo.co.uk",
        "btinternet.com",
    ),
    "DE": (
        "gmail.com",
        "outlook.de",
        "web.de",
        "gmx.de",
        "icloud.com",
    ),
    "US": (
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "icloud.com",
        "hotmail.com",
    ),
    "CN": (
        "qq.com",
        "163.com",
        "126.com",
        "outlook.com",
        "icloud.com",
    ),
    "NO": (
        "gmail.com",
        "outlook.com",
        "online.no",
        "icloud.com",
        "hotmail.com",
    ),
    "RU": (
        "mail.ru",
        "yandex.ru",
        "gmail.com",
        "outlook.com",
    ),
    "JP": (
        "gmail.com",
        "yahoo.co.jp",
        "outlook.jp",
        "icloud.com",
    ),
    "KR": (
        "gmail.com",
        "naver.com",
        "daum.net",
        "outlook.com",
    ),
    "FR": (
        "gmail.com",
        "outlook.fr",
        "orange.fr",
        "free.fr",
        "icloud.com",
    ),
    "NL": (
        "gmail.com",
        "outlook.com",
        "ziggo.nl",
        "icloud.com",
        "hotmail.com",
    ),
    "PL": (
        "gmail.com",
        "outlook.com",
        "wp.pl",
        "onet.pl",
        "interia.pl",
    ),
}


def generate_customers(
    context: SimulationContext,
    *,
    config: CustomerSimulationConfig = (DEFAULT_CUSTOMER_CONFIG),
) -> tuple[Customer, ...]:
    active_markets: dict[str, MarketConfig] = {
        market.market_code: market for market in context.config.markets
    }

    populations: dict[str, CustomerPopulation] = {
        population.market_code: population for population in config.populations
    }

    geography_by_market: dict[str, tuple[CustomerGeography, ...]] = _group_geography_by_market()

    used_emails: set[str] = set()

    customers: list[Customer] = []

    for market_code in sorted(active_markets):
        population: CustomerPopulation | None = populations.get(market_code)

        if population is None:
            raise ValueError(f"no CRM population configured for market {market_code}")

        geography: tuple[CustomerGeography, ...] | None = geography_by_market.get(market_code)

        if not geography:
            raise ValueError(f"no customer geography configured for market {market_code}")

        market: MarketConfig = active_markets[market_code]

        fake: _CustomerFaker = cast(
            _CustomerFaker,
            Faker(locale=market.locale),
        )

        fake.seed_instance(seed=context.seed_for(namespace=f"crm:faker:{market_code}"))

        customers.extend(
            _generate_market_customers(
                context=context,
                market_code=market_code,
                population=population,
                geography=geography,
                fake=fake,
                config=config,
                used_emails=used_emails,
            )
        )

    return tuple(customers)


def _generate_market_customers(
    *,
    context: SimulationContext,
    market_code: str,
    population: CustomerPopulation,
    geography: tuple[CustomerGeography, ...],
    fake: _CustomerFaker,
    config: CustomerSimulationConfig,
    used_emails: set[str],
) -> list[Customer]:
    customers: list[Customer] = []

    for ordinal in range(
        1,
        population.customer_count + 1,
    ):
        customer_number: str = f"CUS-{market_code}-{ordinal:06d}"

        rng = random.Random(
            x=context.seed_for(namespace=(f"crm:customer:{market_code}:{ordinal:06d}"))
        )

        location: CustomerGeography = geography[rng.randrange(start=len(geography))]

        created_at: date = _generate_created_at(
            context=context,
            rng=rng,
            config=config,
        )

        deactivated_at: date | None = _generate_deactivated_at(
            context=context,
            created_at=created_at,
            rng=rng,
            config=config,
        )

        first_name: str = (fake.first_name()).strip()

        last_name: str = (fake.last_name()).strip()

        email: str | None = _generate_email(
            market_code=market_code,
            ordinal=ordinal,
            first_name=first_name,
            last_name=last_name,
            rng=rng,
            config=config,
            used_emails=used_emails,
        )

        phone: str | None = _generate_phone(
            fake=fake,
            rng=rng,
            config=config,
        )

        if email is None and phone is None:
            email = _generate_unique_email(
                market_code=market_code,
                ordinal=ordinal,
                first_name=first_name,
                last_name=last_name,
                rng=rng,
                used_emails=used_emails,
            )

        postal_code: str = str(object=fake.postcode()).strip()

        if not postal_code:
            postal_code = f"SYN-{market_code}-{ordinal:06d}"

        customer_id: str = context.ids.id_for(
            namespace="customer",
            key=customer_number,
            prefix="cus",
        )

        customers.append(
            Customer(
                customer_id=customer_id,
                customer_number=(customer_number),
                market_code=market_code,
                country_code=market_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                city=location.city,
                region=location.region,
                postal_code=postal_code,
                created_at=created_at,
                deactivated_at=(deactivated_at),
            )
        )

    return customers


def _generate_created_at(
    *,
    context: SimulationContext,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> date:
    if rng.random() < config.created_during_simulation_share:
        return _random_date(
            rng=rng,
            start=context.config.start_date,
            end=context.config.end_date,
        )

    historical_start: date = context.config.start_date - timedelta(days=365 * config.history_years)

    historical_end: date = context.config.start_date - timedelta(days=1)

    return _random_date(
        rng=rng,
        start=historical_start,
        end=historical_end,
    )


def _generate_deactivated_at(
    *,
    context: SimulationContext,
    created_at: date,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> date | None:
    if rng.random() >= config.deactivation_probability:
        return None

    earliest: date = max(
        created_at + timedelta(days=config.minimum_active_days),
        context.config.start_date,
    )

    if earliest > context.config.end_date:
        return None

    return _random_date(
        rng=rng,
        start=earliest,
        end=context.config.end_date,
    )


def _generate_email(
    *,
    market_code: str,
    ordinal: int,
    first_name: str,
    last_name: str,
    rng: random.Random,
    config: CustomerSimulationConfig,
    used_emails: set[str],
) -> str | None:
    if rng.random() < config.missing_email_probability:
        return None

    return _generate_unique_email(
        market_code=market_code,
        ordinal=ordinal,
        first_name=first_name,
        last_name=last_name,
        rng=rng,
        used_emails=used_emails,
    )


def _generate_unique_email(
    *,
    market_code: str,
    ordinal: int,
    first_name: str,
    last_name: str,
    rng: random.Random,
    used_emails: set[str],
) -> str:
    domains: tuple[str, ...] | None = EMAIL_DOMAINS_BY_MARKET.get(market_code)

    if not domains:
        raise ValueError(f"no email domains configured for market {market_code}")

    domain: str = rng.choice(seq=domains)

    base_local_part: str = _generate_local_part(
        market_code=market_code,
        ordinal=ordinal,
        first_name=first_name,
        last_name=last_name,
        rng=rng,
    )

    candidate: str = (f"{base_local_part}@{domain}").lower()

    if candidate not in used_emails:
        used_emails.add(candidate)

        return candidate

    suffix: int = ordinal % 100

    candidate = (f"{base_local_part}{suffix:02d}@{domain}").lower()

    if candidate not in used_emails:
        used_emails.add(candidate)

        return candidate

    candidate = (f"{base_local_part}{ordinal:06d}@{domain}").lower()

    if candidate in used_emails:
        raise ValueError(
            f"unable to generate unique customer email for {market_code}-{ordinal:06d}"
        )

    used_emails.add(candidate)

    return candidate


def _generate_local_part(
    *,
    market_code: str,
    ordinal: int,
    first_name: str,
    last_name: str,
    rng: random.Random,
) -> str:
    first: str = _ascii_email_token(value=first_name)

    last: str = _ascii_email_token(value=last_name)

    if first and last:
        styles = (
            f"{first}.{last}",
            f"{first}{last}",
            f"{first}_{last}",
            f"{first[0]}{last}",
            f"{last}.{first}",
        )

        return rng.choice(seq=styles)

    if first:
        return f"{first}{rng.randint(a=10, b=99)}"

    if last:
        return f"{last}{rng.randint(a=10, b=99)}"

    return _fallback_email_handle(
        market_code=market_code,
        ordinal=ordinal,
        rng=rng,
    )


def _ascii_email_token(
    value: str,
) -> str:
    normalised: str = unicodedata.normalize(
        "NFKD",
        value,
    )

    ascii_value: str = (
        normalised.encode(
            encoding="ascii",
            errors="ignore",
        )
        .decode(encoding="ascii")
        .lower()
    )

    return re.sub(
        pattern=r"[^a-z0-9]",
        repl="",
        string=ascii_value,
    )


def _fallback_email_handle(
    *,
    market_code: str,
    ordinal: int,
    rng: random.Random,
) -> str:
    prefixes_by_market: dict[str, tuple[str, str, str, str, str, str]] = {
        "CN": (
            "lin",
            "chen",
            "wei",
            "ming",
            "yu",
            "xin",
        ),
        "JP": (
            "haru",
            "yuki",
            "ren",
            "aoi",
            "sora",
            "kei",
        ),
        "KR": (
            "min",
            "jin",
            "seo",
            "hyun",
            "ji",
            "young",
        ),
        "RU": (
            "alex",
            "misha",
            "nik",
            "katya",
            "dima",
            "anya",
        ),
    }

    prefixes: (
        tuple[str, str, str, str, str, str]
        | tuple[Literal["user"], Literal["member"], Literal["hello"]]
    ) = prefixes_by_market.get(
        market_code,
        (
            "user",
            "member",
            "hello",
        ),
    )

    prefix: str = rng.choice(seq=prefixes)

    discriminator: int = (
        ordinal * 37
        + rng.randint(
            a=0,
            b=999,
        )
    ) % 10_000

    return f"{prefix}{discriminator:04d}"


def _generate_phone(
    *,
    fake: _CustomerFaker,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> str | None:
    if rng.random() < config.missing_phone_probability:
        return None

    phone: str = (fake.phone_number()).strip()

    if not phone:
        return None

    return phone


def _random_date(
    *,
    rng: random.Random,
    start: date,
    end: date,
) -> date:
    if start > end:
        raise ValueError("random date start must not be after end")

    span: int = (end - start).days

    return start + timedelta(
        days=rng.randint(
            a=0,
            b=span,
        )
    )


def _group_geography_by_market() -> dict[
    str,
    tuple[CustomerGeography, ...],
]:
    grouped: dict[
        str,
        list[CustomerGeography],
    ] = defaultdict(list)

    for geography in CUSTOMER_GEOGRAPHIES:
        grouped[geography.market_code].append(geography)

    return {market_code: tuple(rows) for market_code, rows in grouped.items()}
