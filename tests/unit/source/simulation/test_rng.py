from random import Random

import pytest

from mercatura.source.simulation.rng import RandomStreams


def test_same_root_seed_and_namespace_produce_same_sequence() -> None:
    first = RandomStreams(root_seed=42)
    second = RandomStreams(root_seed=42)

    first_rng: Random = first.get(namespace="oms")
    second_rng: Random = second.get(namespace="oms")

    first_values: list[float] = [first_rng.random() for _ in range(10)]
    second_values: list[float] = [second_rng.random() for _ in range(10)]

    assert first_values == second_values


def test_different_namespaces_produce_different_sequences() -> None:
    streams = RandomStreams(root_seed=42)

    crm_rng: Random = streams.get(namespace="crm")
    oms_rng: Random = streams.get(namespace="oms")

    crm_values: list[float] = [crm_rng.random() for _ in range(10)]
    oms_values: list[float] = [oms_rng.random() for _ in range(10)]

    assert crm_values != oms_values


def test_get_returns_same_stateful_stream() -> None:
    streams = RandomStreams(root_seed=42)

    first_reference: Random = streams.get(namespace="crm")
    second_reference: Random = streams.get(namespace="crm")

    assert first_reference is second_reference


def test_different_root_seeds_produce_different_sequences() -> None:
    first = RandomStreams(root_seed=42)
    second = RandomStreams(root_seed=43)

    first_values: list[float] = [first.get(namespace="oms").random() for _ in range(10)]

    second_values: list[float] = [second.get(namespace="oms").random() for _ in range(10)]

    assert first_values != second_values


def test_empty_namespace_is_rejected() -> None:
    streams = RandomStreams(root_seed=42)

    with pytest.raises(
        expected_exception=ValueError,
        match="namespace must not be empty",
    ):
        streams.get(namespace="")
