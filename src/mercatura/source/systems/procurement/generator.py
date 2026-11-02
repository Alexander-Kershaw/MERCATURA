import random
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from mercatura.source.reference.currency import CURRENCY_MINOR_UNITS
from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.assortment.model import ProductMarketAssortment
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.pricing.model import ProductPrice
from mercatura.source.systems.procurement.config import (
    DEFAULT_PROCUREMENT_CONFIG,
    MARKET_REGIONS,
    ROLE_COST_RANGES,
    SUPPLIER_TYPE_COST_ADJUSTMENTS,
    SUPPLIER_TYPE_LOGISTICS,
    ProcurementSimulationConfig,
)
from mercatura.source.systems.procurement.model import SourcingAgreement, SourcingRole
from mercatura.source.systems.supplier.model import Supplier


def generate_sourcing_agreements(
    context: SimulationContext,
    products: tuple[Product, ...],
    assortments: tuple[ProductMarketAssortment, ...],
    suppliers: tuple[Supplier, ...],
    prices: tuple[ProductPrice, ...],
    *,
    procurement_config: ProcurementSimulationConfig = (DEFAULT_PROCUREMENT_CONFIG),
) -> tuple[SourcingAgreement, ...]:
    products_by_id: dict[str, Product] = {product.product_id: product for product in products}

    initial_prices: dict[str, ProductPrice] = _initial_prices_by_assortment(prices)

    agreements: list[SourcingAgreement] = []

    for assortment in assortments:
        product: Product = products_by_id[assortment.product_id]

        initial_price: ProductPrice = initial_prices[assortment.assortment_id]

        agreements.extend(
            _generate_assortment_sourcing(
                context=context,
                assortment=assortment,
                product=product,
                suppliers=suppliers,
                initial_price=initial_price,
                config=procurement_config,
            )
        )

    return tuple(agreements)


def _initial_prices_by_assortment(
    prices: tuple[ProductPrice, ...],
) -> dict[str, ProductPrice]:
    grouped: dict[
        str,
        list[ProductPrice],
    ] = defaultdict(list)

    for price in prices:
        grouped[price.assortment_id].append(price)

    return {
        assortment_id: min(
            history,
            key=lambda row: row.version,
        )
        for assortment_id, history in grouped.items()
    }


def _source_count(
    *,
    rng: random.Random,
    config: ProcurementSimulationConfig,
) -> int:
    value: float = rng.random()

    if value < config.single_source_probability:
        return 1

    if value < (config.single_source_probability + config.dual_source_probability):
        return 2

    return 3


def _roles_for_count(
    count: int,
) -> tuple[SourcingRole, ...]:
    if count == 1:
        return ("PRIMARY",)

    if count == 2:
        return (
            "PRIMARY",
            "SECONDARY",
        )

    if count == 3:
        return (
            "PRIMARY",
            "SECONDARY",
            "BACKUP",
        )

    raise ValueError(f"unsupported sourcing count: {count}")


def _eligible_suppliers(
    *,
    assortment: ProductMarketAssortment,
    suppliers: tuple[Supplier, ...],
) -> list[Supplier]:
    eligible: list[Supplier] = []

    for supplier in suppliers:
        if supplier.created_at > assortment.ranged_from:
            continue

        if assortment.ranged_to is None:
            if supplier.inactive_at is not None:
                continue

        elif supplier.inactive_at is not None and supplier.inactive_at < assortment.ranged_to:
            continue

        eligible.append(supplier)

    return eligible


def _supplier_weight(
    *,
    supplier: Supplier,
    assortment: ProductMarketAssortment,
    product: Product,
) -> float:
    weight = 1.0

    if supplier.country_code == assortment.market_code:
        weight += 4.0

    elif MARKET_REGIONS[supplier.country_code] == MARKET_REGIONS[assortment.market_code]:
        weight += 2.0

    if product.department_code == "ELEC" and supplier.country_code == "CN":
        weight += 2.5

    if product.department_code == "TOYS" and supplier.country_code == "CN":
        weight += 1.5

    return weight


def _select_suppliers(
    *,
    rng: random.Random,
    assortment: ProductMarketAssortment,
    product: Product,
    suppliers: list[Supplier],
    count: int,
) -> list[Supplier]:
    if len(suppliers) < count:
        raise ValueError(
            f"not enough eligible suppliers for {assortment.market_code} {assortment.sku}"
        )

    pool: list[Supplier] = sorted(
        suppliers,
        key=lambda supplier: supplier.supplier_code,
    )
    selected: list[Supplier] = []

    for _ in range(count):
        weights: list[float] = [
            _supplier_weight(
                supplier=supplier,
                assortment=assortment,
                product=product,
            )
            for supplier in pool
        ]

        index: int = rng.choices(
            population=range(len(pool)),
            weights=weights,
            k=1,
        )[0]

        selected.append(pool.pop(index))

    return selected


def _generate_assortment_sourcing(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    product: Product,
    suppliers: tuple[Supplier, ...],
    initial_price: ProductPrice,
    config: ProcurementSimulationConfig,
) -> list[SourcingAgreement]:
    rng = random.Random(
        x=context.seed_for(
            namespace=(f"procurement:sourcing:{assortment.market_code}:{product.sku}")
        )
    )

    count: int = _source_count(
        rng=rng,
        config=config,
    )

    roles: tuple[Literal["PRIMARY"] | Literal["SECONDARY"] | Literal["BACKUP"], ...] = (
        _roles_for_count(count)
    )

    eligible: list[Supplier] = _eligible_suppliers(
        assortment=assortment,
        suppliers=suppliers,
    )

    selected: list[Supplier] = _select_suppliers(
        rng=rng,
        assortment=assortment,
        product=product,
        suppliers=eligible,
        count=count,
    )

    return [
        _build_agreement(
            context=context,
            assortment=assortment,
            product=product,
            supplier=supplier,
            role=role,
            initial_price=initial_price,
            rng=rng,
        )
        for supplier, role in zip(
            selected,
            roles,
            strict=True,
        )
    ]


def _build_agreement(
    *,
    context: SimulationContext,
    assortment: ProductMarketAssortment,
    product: Product,
    supplier: Supplier,
    role: SourcingRole,
    initial_price: ProductPrice,
    rng: random.Random,
) -> SourcingAgreement:
    sourcing_id: str = context.ids.id_for(
        namespace="sourcing",
        key=(f"{assortment.market_code}:{product.sku}:{supplier.supplier_code}"),
        prefix="src",
    )

    unit_cost: Decimal = _generate_unit_cost(
        initial_price=initial_price,
        supplier=supplier,
        role=role,
        rng=rng,
    )

    minimum_order_quantity: int = _generate_moq(
        supplier=supplier,
        rng=rng,
    )

    lead_time_days: int = _generate_lead_time(
        supplier=supplier,
        market_code=(assortment.market_code),
        rng=rng,
    )

    return SourcingAgreement(
        sourcing_id=sourcing_id,
        assortment_id=(assortment.assortment_id),
        product_id=product.product_id,
        sku=product.sku,
        market_code=(assortment.market_code),
        supplier_id=supplier.supplier_id,
        supplier_code=(supplier.supplier_code),
        sourcing_role=role,
        unit_cost=unit_cost,
        currency=initial_price.currency,
        minimum_order_quantity=(minimum_order_quantity),
        lead_time_days=lead_time_days,
        effective_from=(assortment.ranged_from),
        effective_to=(assortment.ranged_to),
    )


def _generate_unit_cost(
    *,
    initial_price: ProductPrice,
    supplier: Supplier,
    role: SourcingRole,
    rng: random.Random,
) -> Decimal:
    minimum: Decimal
    maximum: Decimal
    minimum, maximum = ROLE_COST_RANGES[role]

    ratio = Decimal(
        value=str(
            object=rng.uniform(
                a=float(minimum),
                b=float(maximum),
            )
        )
    )

    ratio += SUPPLIER_TYPE_COST_ADJUSTMENTS[supplier.supplier_type]

    ratio: Decimal = min(
        ratio,
        Decimal(value="0.85"),
    )

    ratio = max(
        ratio,
        Decimal(value="0.25"),
    )

    raw_cost: Decimal = initial_price.list_price * ratio

    minor_unit: Decimal = CURRENCY_MINOR_UNITS[initial_price.currency]

    return _round_money(
        raw_cost,
        minor_unit,
    )


def _generate_moq(
    *,
    supplier: Supplier,
    rng: random.Random,
) -> int:
    (
        _,
        _,
        minimum_moq,
        maximum_moq,
    ) = SUPPLIER_TYPE_LOGISTICS[supplier.supplier_type]

    return rng.randint(
        a=minimum_moq,
        b=maximum_moq,
    )


def _generate_lead_time(
    *,
    supplier: Supplier,
    market_code: str,
    rng: random.Random,
) -> int:
    (
        minimum_lead,
        maximum_lead,
        _,
        _,
    ) = SUPPLIER_TYPE_LOGISTICS[supplier.supplier_type]

    lead_time: int = rng.randint(
        minimum_lead,
        maximum_lead,
    )

    supplier_region: str = MARKET_REGIONS[supplier.country_code]

    buyer_region: str = MARKET_REGIONS[market_code]

    if supplier.country_code == market_code:
        logistics_penalty: int = rng.randint(
            a=0,
            b=3,
        )

    elif supplier_region == buyer_region:
        logistics_penalty = rng.randint(
            a=3,
            b=10,
        )

    else:
        logistics_penalty = rng.randint(
            a=10,
            b=30,
        )

    return lead_time + logistics_penalty


def _round_money(
    value: Decimal,
    minor_unit: Decimal,
) -> Decimal:
    return (value / minor_unit).quantize(
        exp=Decimal(value="1"),
        rounding=ROUND_HALF_UP,
    ) * minor_unit
