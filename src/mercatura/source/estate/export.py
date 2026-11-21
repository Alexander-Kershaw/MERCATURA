import json
from dataclasses import (
    asdict,
    is_dataclass,
)
from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from mercatura.source.estate.manifest import (
    build_source_estate_manifest,
)
from mercatura.source.estate.source_estate import (
    SourceEstate,
)


def export_source_estate(estate: SourceEstate, output_directory: Path) -> Path:

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_directory = output_directory / "data"

    data_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    datasets = estate.source_datasets()

    expected_files = {f"{name}.jsonl" for name in datasets}

    _remove_stale_jsonl_files(
        data_directory,
        expected_files,
    )

    for (
        dataset_name,
        rows,
    ) in datasets.items():
        _write_jsonl(
            path=(data_directory / f"{dataset_name}.jsonl"),
            rows=rows,
        )

    manifest = build_source_estate_manifest(estate)

    manifest_path = output_directory / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            _dataclass_to_jsonable(manifest),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return manifest_path


def _write_jsonl(
    *,
    path: Path,
    rows: tuple[
        object,
        ...,
    ],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for row in rows:
            document = _dataclass_to_jsonable(row)

            handle.write(
                json.dumps(
                    document,
                    sort_keys=True,
                    separators=(
                        ",",
                        ":",
                    ),
                    ensure_ascii=False,
                )
            )

            handle.write("\n")


def _dataclass_to_jsonable(
    value: object,
) -> object:
    if not is_dataclass(value) or isinstance(
        value,
        type,
    ):
        raise TypeError("source estate export expects dataclass instances")

    raw = asdict(
        cast(
            Any,
            value,
        )
    )

    return _convert_value(raw)


def _convert_value(
    value: object,
) -> object:
    if isinstance(
        value,
        Decimal,
    ):
        return str(value)

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        tuple,
    ):
        return [_convert_value(item) for item in value]

    if isinstance(
        value,
        list,
    ):
        return [_convert_value(item) for item in value]

    if isinstance(
        value,
        dict,
    ):
        return {str(key): _convert_value(item) for key, item in value.items()}

    return value


def _remove_stale_jsonl_files(
    directory: Path,
    expected_files: set[str],
) -> None:
    for path in directory.glob("*.jsonl"):
        if path.name not in expected_files:
            path.unlink()
