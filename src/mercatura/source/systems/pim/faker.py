from faker import Faker

from mercatura.source.simulation import SimulationContext

PIM_FAKER_LOCALE = "en_GB"


def build_pim_faker(context: SimulationContext, namespace: str) -> Faker:
    fake = Faker(locale=PIM_FAKER_LOCALE)

    fake.seed_instance(seed=context.seed_for(namespace=f"faker:pim:{namespace}"))

    return fake
