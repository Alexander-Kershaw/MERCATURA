import random
from datetime import date, timedelta

from faker import Faker

from mercatura.source.reference.product_taxonomy import (
    PRODUCT_MATERIAL_OVERRIDES,
    PRODUCT_TAXONOMY,
    ProductCategory,
)
from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.pim.config import (
    DEFAULT_PRODUCT_CONFIG,
    ProductSimulationConfig,
)
from mercatura.source.systems.pim.faker import build_pim_faker
from mercatura.source.systems.pim.model import Product

BRANDS: tuple[str, ...] = (
    "Mercatura Essentials",
    "Mercatura Studio",
    "Mercatura Home",
    "Mercatura Active",
    "Aster",
    "Axiom",
    "Kestrel",
    "Luma",
    "Northstar",
    "Orion",
    "Vela",
    "Veridian",
)

PRIVATE_LABEL_BRANDS: dict[str, str] = {
    "ELEC": "Mercatura Tech",
    "HOME": "Mercatura Home",
    "KIT": "Mercatura Kitchen",
    "APP": "Mercatura Studio",
    "BEAU": "Mercatura Beauty",
    "SPORT": "Mercatura Active",
    "TOYS": "Mercatura Play",
    "OFF": "Mercatura Office",
    "GARD": "Mercatura Living",
}

BRAND_SUFFIXES: dict[str, tuple[str, ...]] = {
    "ELEC": (
        "Labs",
        "Digital",
        "Systems",
        "Audio",
    ),
    "HOME": (
        "Living",
        "Home",
        "Studio",
        "House",
    ),
    "KIT": (
        "Kitchen",
        "Cookware",
        "House",
        "Works",
    ),
    "APP": (
        "Studio",
        "Collective",
        "London",
        "& Co.",
    ),
    "BEAU": (
        "Botanics",
        "Skin",
        "Atelier",
        "Essentials",
    ),
    "SPORT": (
        "Active",
        "Motion",
        "Performance",
        "Outdoor",
    ),
    "TOYS": (
        "Play",
        "Works",
        "Games",
        "Creative",
    ),
    "OFF": (
        "Paper",
        "Office",
        "Studio",
        "Works",
    ),
    "GARD": (
        "Garden",
        "Living",
        "Works",
        "Outdoor",
    ),
}

MODEL_FAMILIES: tuple[str, ...] = (
    "Aero",
    "Arc",
    "Axis",
    "Core",
    "Edge",
    "Element",
    "Form",
    "Halo",
    "Horizon",
    "Lumen",
    "Nova",
    "Origin",
    "Pulse",
    "Slate",
    "Sol",
    "Vertex",
)

PRODUCT_COLOURS: tuple[str, ...] = (
    "Black",
    "White",
    "Charcoal",
    "Grey",
    "Silver",
    "Navy",
    "Blue",
    "Sky Blue",
    "Green",
    "Olive",
    "Sage",
    "Red",
    "Burgundy",
    "Pink",
    "Blush",
    "Purple",
    "Cream",
    "Beige",
    "Tan",
    "Brown",
    "Orange",
    "Yellow",
)


def generate_products(
    context: SimulationContext,
    *,
    product_config: ProductSimulationConfig = DEFAULT_PRODUCT_CONFIG,
) -> tuple[Product, ...]:
    taxonomy_rng: random.Random = context.rng(namespace="pim:taxonomy")

    brand_rng: random.Random = context.rng(namespace="pim:brand")

    lifecycle_rng: random.Random = context.rng(namespace="pim:lifecycle")

    naming_rng: random.Random = context.rng(namespace="pim:naming")

    brand_pools: dict[str, tuple[str, ...]] = _build_brand_pools(context)

    model_fake: Faker = build_pim_faker(
        context,
        namespace="model",
    )

    attribute_fake: Faker = build_pim_faker(
        context,
        namespace="attributes",
    )

    products: list[Product] = [
        _generate_product(
            context=context,
            index=index,
            config=product_config,
            taxonomy_rng=taxonomy_rng,
            brand_rng=brand_rng,
            lifecycle_rng=lifecycle_rng,
            naming_rng=naming_rng,
            brand_pools=brand_pools,
            model_fake=model_fake,
            attribute_fake=attribute_fake,
        )
        for index in range(
            1,
            product_config.product_count + 1,
        )
    ]

    return tuple(products)


def _generate_product(
    *,
    context: SimulationContext,
    index: int,
    config: ProductSimulationConfig,
    taxonomy_rng: random.Random,
    brand_rng: random.Random,
    lifecycle_rng: random.Random,
    naming_rng: random.Random,
    brand_pools: dict[
        str,
        tuple[str, ...],
    ],
    model_fake: Faker,
    attribute_fake: Faker,
) -> Product:
    category: ProductCategory = _choose_category(rng=taxonomy_rng)

    sku: str = f"MRC-{index:06d}"

    product_id: str = context.ids.id_for(
        namespace="product",
        key=sku,
        prefix="prd",
    )

    brand_name: str = brand_rng.choice(seq=brand_pools[category.department_code])

    model_name: str = _generate_model_name(
        rng=naming_rng,
    )

    product_term: str = naming_rng.choice(seq=category.product_terms)

    product_name: str = f"{brand_name} {model_name} {product_term}"

    materials: tuple[str, ...] = PRODUCT_MATERIAL_OVERRIDES.get(
        product_term,
        category.materials,
    )

    material: str | None = naming_rng.choice(seq=materials) if materials else None

    colour: str | None = (
        naming_rng.choice(seq=PRODUCT_COLOURS) if category.colour_applicable else None
    )

    description: str = _build_description(
        product_term=product_term,
        brand_name=brand_name,
        model_name=model_name,
        material=material,
        colour=colour,
    )

    created_at: date = _generate_created_at(
        context=context,
        config=config,
        rng=lifecycle_rng,
    )

    discontinued_at: date | None = _generate_discontinued_at(
        context=context,
        created_at=created_at,
        config=config,
        rng=lifecycle_rng,
    )

    return Product(
        product_id=product_id,
        sku=sku,
        product_name=product_name,
        brand_name=brand_name,
        model_name=model_name,
        department_code=category.department_code,
        department_name=category.department_name,
        category_code=category.category_code,
        category_name=category.category_name,
        subcategory_code=category.subcategory_code,
        subcategory_name=category.subcategory_name,
        colour=colour,
        material=material,
        description=description,
        unit_of_measure=category.unit_of_measure,
        created_at=created_at,
        discontinued_at=discontinued_at,
    )


def _generate_created_at(
    *,
    context: SimulationContext,
    config: ProductSimulationConfig,
    rng: random.Random,
) -> date:
    if rng.random() < config.launch_during_simulation_rate:
        return _random_date(
            rng=rng,
            start=context.config.start_date,
            end=context.config.end_date,
        )

    historical_start: date = context.config.start_date - timedelta(days=365 * config.history_years)

    return _random_date(
        rng=rng,
        start=historical_start,
        end=context.config.start_date - timedelta(days=1),
    )


def _generate_discontinued_at(
    *,
    context: SimulationContext,
    created_at: date,
    config: ProductSimulationConfig,
    rng: random.Random,
) -> date | None:
    if rng.random() >= config.discontinue_rate:
        return None

    earliest_discontinuation: date = max(
        created_at + timedelta(days=30),
        context.config.start_date,
    )

    if earliest_discontinuation > context.config.end_date:
        return None

    return _random_date(
        rng=rng,
        start=earliest_discontinuation,
        end=context.config.end_date,
    )


def _random_date(
    *,
    rng: random.Random,
    start: date,
    end: date,
) -> date:
    if end < start:
        raise ValueError("end must be on or after start")

    day_count: int = (end - start).days

    return start + timedelta(
        days=rng.randint(
            a=0,
            b=day_count,
        )
    )


def _build_brand_pools(
    context: SimulationContext,
) -> dict[str, tuple[str, ...]]:
    fake: Faker = build_pim_faker(
        context,
        namespace="brand",
    )

    departments: set[str] = {category.department_code for category in PRODUCT_TAXONOMY}

    pools: dict[str, tuple[str, ...]] = {}

    for department_code in sorted(departments):
        brands: list[str] = [PRIVATE_LABEL_BRANDS[department_code]]

        suffixes: tuple[str, ...] = BRAND_SUFFIXES[department_code]

        while len(brands) < 7:
            candidate: str = f"{fake.last_name()} {fake.random_element(elements=suffixes)}"

            if candidate not in brands:
                brands.append(candidate)

        pools[department_code] = tuple(brands)

    return pools


def _choose_category(
    rng: random.Random,
) -> ProductCategory:
    return rng.choices(
        population=PRODUCT_TAXONOMY,
        weights=[category.weight for category in PRODUCT_TAXONOMY],
        k=1,
    )[0]


def _generate_model_name(
    *,
    rng: random.Random,
) -> str:
    family: str = rng.choice(seq=MODEL_FAMILIES)

    series: int = rng.randint(
        a=100,
        b=999,
    )

    return f"{family} {series}"


def _build_description(
    *,
    product_term: str,
    brand_name: str,
    model_name: str,
    material: str | None,
    colour: str | None,
) -> str:
    attributes: list[str] = [
        value
        for value in (
            colour,
            material,
        )
        if value is not None
    ]

    attribute_text: str = ", ".join(attributes) if attributes else "standard specification"

    return f"{brand_name} {model_name} {product_term.lower()} with {attribute_text}."
