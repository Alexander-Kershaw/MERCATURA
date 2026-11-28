import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mercatura.discovery.model import (
    DatasetDefinition,
    SourceRegistry,
)
from mercatura.discovery.registry import (
    load_source_registry,
)


def _dataset_payload(
    *,
    dataset_name: str = "orders",
    source_system: str = "oms",
    model_name: str = "Order",
    grain: str = "One customer order",
    visibility: str = "source",
) -> dict[str, object]:
    return {
        "dataset_name": dataset_name,
        "source_system": source_system,
        "model_name": model_name,
        "grain": grain,
        "visibility": visibility,
    }


def _registry_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "datasets": [
            _dataset_payload(),
            _dataset_payload(
                dataset_name="demand_profiles",
                source_system="simulation",
                model_name="DemandProfile",
                grain="One demand profile per assortment",
                visibility="internal",
            ),
        ],
    }


def test_valid_dataset_definition() -> None:
    dataset: DatasetDefinition = DatasetDefinition.model_validate(obj=_dataset_payload())

    assert dataset.dataset_name == "orders"
    assert dataset.source_system == "oms"
    assert dataset.model_name == "Order"


def test_qualified_dataset_name() -> None:
    dataset: DatasetDefinition = DatasetDefinition.model_validate(obj=_dataset_payload())

    assert dataset.qualified_name == "oms.orders"


@pytest.mark.parametrize(
    argnames="invalid_name",
    argvalues=[
        "",
        "Orders",
        "order-items",
        "2026_orders",
        "order items",
        " orders",
    ],
)
def test_invalid_dataset_name(
    invalid_name: str,
) -> None:
    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=_dataset_payload(dataset_name=invalid_name))


def test_invalid_source_system() -> None:
    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=_dataset_payload(source_system="OMS"))


def test_invalid_model_name() -> None:
    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=_dataset_payload(model_name="order"))


@pytest.mark.parametrize(
    argnames="grain",
    argvalues=[
        "",
        "   ",
    ],
)
def test_empty_grain_is_rejected(
    grain: str,
) -> None:
    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=_dataset_payload(grain=grain))


def test_invalid_visibility_is_rejected() -> None:
    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=_dataset_payload(visibility="public"))


def test_visibility_is_mandatory() -> None:
    payload: dict[str, object] = _dataset_payload()
    payload.pop("visibility")

    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=payload)


def test_unexpected_attribute_is_rejected() -> None:
    payload: dict[str, object] = _dataset_payload()
    payload["unknown_setting"] = True

    with pytest.raises(expected_exception=ValidationError):
        DatasetDefinition.model_validate(obj=payload)


def test_registry_validates_nested_datasets() -> None:
    registry: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    assert len(registry.datasets) == 2

    assert isinstance(
        registry.datasets[0],
        DatasetDefinition,
    )


def test_registry_separates_source_datasets() -> None:
    registry: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    assert len(registry.source_datasets) == 1

    assert registry.source_datasets[0].dataset_name == "orders"


def test_registry_separates_internal_datasets() -> None:
    registry: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    assert len(registry.internal_datasets) == 1

    assert registry.internal_datasets[0].dataset_name == "demand_profiles"


def test_source_systems_exclude_internal_systems() -> None:
    registry: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    assert registry.source_systems == ("oms",)


def test_duplicate_dataset_names_are_rejected() -> None:
    payload = {
        "schema_version": 1,
        "datasets": [
            _dataset_payload(),
            _dataset_payload(),
        ],
    }

    with pytest.raises(
        expected_exception=ValidationError,
        match="duplicate dataset_name",
    ):
        SourceRegistry.model_validate(payload)


def test_empty_registry_is_rejected() -> None:
    payload = {
        "schema_version": 1,
        "datasets": [],
    }

    with pytest.raises(expected_exception=ValidationError):
        SourceRegistry.model_validate(obj=payload)


def test_unsupported_schema_version_is_rejected() -> None:
    payload: dict[str, object] = _registry_payload()
    payload["schema_version"] = 999

    with pytest.raises(expected_exception=ValidationError):
        SourceRegistry.model_validate(obj=payload)


def test_get_dataset_by_name() -> None:
    registry: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    dataset: DatasetDefinition = registry.get_dataset(dataset_name="orders")

    assert dataset.qualified_name == "oms.orders"


def test_unknown_dataset_raises_key_error() -> None:
    registry: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    with pytest.raises(
        expected_exception=KeyError,
        match="unknown dataset",
    ):
        registry.get_dataset(dataset_name="unknown")


def test_registry_can_be_loaded_from_json(
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "registry.json"

    path.write_text(
        data=json.dumps(obj=_registry_payload()),
        encoding="utf-8",
    )

    registry: SourceRegistry = load_source_registry(path)

    assert len(registry.datasets) == 2


def test_registry_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "registry.json"

    path.write_text(
        data="{invalid_json",
        encoding="utf-8",
    )

    with pytest.raises(expected_exception=ValidationError):
        load_source_registry(path)


def test_missing_registry_file(
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "missing.json"

    with pytest.raises(expected_exception=FileNotFoundError):
        load_source_registry(path)


def test_registry_serialization_round_trip() -> None:
    original: SourceRegistry = SourceRegistry.model_validate(obj=_registry_payload())

    serialized: str = original.model_dump_json()

    restored: SourceRegistry = SourceRegistry.model_validate_json(json_data=serialized)

    assert restored == original


def test_registry_models_are_frozen() -> None:
    dataset: DatasetDefinition = DatasetDefinition.model_validate(obj=_dataset_payload())

    with pytest.raises(expected_exception=ValidationError):
        dataset.dataset_name = "different_orders"


def test_canonical_mercatura_registry() -> None:
    repository_root: Path = Path(__file__).resolve().parents[3]

    path: Path = repository_root / "configs" / "discovery" / "source_registry.json"

    registry: SourceRegistry = load_source_registry(path)

    assert len(registry.datasets) == 31
    assert len(registry.source_datasets) == 30
    assert len(registry.internal_datasets) == 1
    assert len(registry.source_systems) == 14

    assert registry.get_dataset(dataset_name="demand_profiles").visibility == "internal"

    assert registry.get_dataset(dataset_name="inventory_movements").source_system == "wms"
