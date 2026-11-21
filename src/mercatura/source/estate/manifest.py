from dataclasses import dataclass
from datetime import date

from mercatura.source.estate.model import (
    ReconciliationCheck,
)
from mercatura.source.estate.source_estate import (
    SourceEstate,
)


@dataclass(frozen=True, slots=True)
class DatasetManifestEntry:
    dataset_name: str
    row_count: int
    file_name: str | None


@dataclass(frozen=True, slots=True)
class SourceEstateManifest:
    simulation_id: str
    generator_version: str
    seed: int
    start_date: date
    end_date: date
    reporting_currency: str
    scenarios: tuple[
        str,
        ...,
    ]
    defects: tuple[
        str,
        ...,
    ]
    source_datasets: tuple[
        DatasetManifestEntry,
        ...,
    ]
    internal_datasets: tuple[
        DatasetManifestEntry,
        ...,
    ]
    reconciliation_passed: bool
    reconciliation_checks: tuple[
        ReconciliationCheck,
        ...,
    ]


def build_source_estate_manifest(estate: SourceEstate) -> SourceEstateManifest:
    config = estate.context.config

    source_entries = tuple(
        DatasetManifestEntry(
            dataset_name=name,
            row_count=len(rows),
            file_name=f"data/{name}.jsonl",
        )
        for name, rows in estate.source_datasets().items()
    )

    internal_entries = tuple(
        DatasetManifestEntry(
            dataset_name=name,
            row_count=len(rows),
            file_name=None,
        )
        for name, rows in estate.internal_datasets().items()
    )

    return SourceEstateManifest(
        simulation_id=(estate.simulation_id),
        generator_version=(config.generator_version),
        seed=config.seed,
        start_date=config.start_date,
        end_date=config.end_date,
        reporting_currency=(config.reporting_currency),
        scenarios=config.scenarios,
        defects=config.defects,
        source_datasets=source_entries,
        internal_datasets=internal_entries,
        reconciliation_passed=(estate.reconciliation.passed),
        reconciliation_checks=(estate.reconciliation.checks),
    )
