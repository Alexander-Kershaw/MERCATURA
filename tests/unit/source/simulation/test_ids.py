from mercatura.source.simulation.ids import (
    DeterministicIdGenerator,
)


def test_same_inputs_produce_same_id() -> None:
    first = DeterministicIdGenerator(simulation_id="sim_v1_test")
    second = DeterministicIdGenerator(simulation_id="sim_v1_test")

    assert first.id_for(
        namespace="customer",
        key="GB:000001",
        prefix="cus",
    ) == second.id_for(
        namespace="customer",
        key="GB:000001",
        prefix="cus",
    )


def test_different_keys_produce_different_ids() -> None:
    ids = DeterministicIdGenerator(simulation_id="sim_v1_test")

    assert ids.id_for(namespace="customer", key="GB:000001") != ids.id_for(
        namespace="customer", key="GB:000002"
    )


def test_namespaces_isolate_entity_types() -> None:
    ids = DeterministicIdGenerator(simulation_id="sim_v1_test")

    assert ids.id_for(namespace="customer", key="GB:000001") != ids.id_for(
        namespace="order", key="GB:000001"
    )


def test_simulations_produce_different_ids() -> None:
    first = DeterministicIdGenerator(simulation_id="sim_v1_first")
    second = DeterministicIdGenerator(simulation_id="sim_v1_second")

    assert first.id_for(namespace="customer", key="GB:000001") != second.id_for(
        namespace="customer", key="GB:000001"
    )


def test_prefix_is_applied() -> None:
    ids = DeterministicIdGenerator(simulation_id="sim_v1_test")

    customer_id: str = ids.id_for(
        namespace="customer",
        key="GB:000001",
        prefix="cus",
    )

    assert customer_id.startswith("cus_")
