from collections import Counter
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

"""
=======================================================================================================

METADATA MODEL

=======================================================================================================

With the source registry created (in configs/discovery/source_registry.json) I am expanding the 
metadata configuration. Note: using JSON instead of YAML for the source registry for now, more 
complex contracts and ingestion definitions will use YAML, JSON is sufficient for 
the regsitry for now.

--------------------------------------------------------------------------------------------------------

IMPLEMENTATION NOTES:

- The Annotated type allows me to attach additional metadata to a type.
  Consider the RegistryIdentifier as an example. This annotation attaches metadata: 
  str declaration, and string contraint (specific regex pattern: no numbers, just words in 
  isolation, or separated with underscore) which is applied at runtime with Pydantic.

  This naming convention is important for making future configuration and path constructions, 
  and table naming more cohesive.


- The Literal usage represents a set of contrained values, it us used for controlling vocabulary 
  and selecting between source or internal visibility datasets. These are the only allowed 
  values thus far, the literal must also be present since every dataset must have an 
  explicit visibility declaration.


- extra="forbid" means any unexpected configuration properties will be rejected. This is 
  particularly important as later I will be using AI-assisted metadata generation tooling, so 
  this setting should avoid having configuration errors being caught before execution begins.

---------------------------------------------------------------------------------------------------------

PYDANTIC VALIDATION LEVELS:

Pydantic supports validation at the field-level and the model-level:

- At the field-level, validation is concentrated around attributes, in this case, the dataset 
  name must match the regex pattern, visibility must be supported, and the grain must be 
  non-empty.

- At the model-level, this is concentrated around relationships between attributes or records, 
  in this case I am validating that the dataset names are unique across the source registry.

  
=========================================================================================================
"""


RegistryIdentifier = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-z][a-z0-9_]*$",
    ),
]

ModelIdentifier = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Z][A-Za-z0-9_]*$",
    ),
]

NonEmptyTest = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

DatasetVisibility = Literal["source", "internal"]


class DatasetDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_name: RegistryIdentifier
    source_system: RegistryIdentifier
    model_name: ModelIdentifier
    grain: NonEmptyTest
    visibility: DatasetVisibility

    @property
    def qualified_name(self) -> str:
        return f"{self.source_system}.{self.dataset_name}"


class SourceRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]

    datasets: Annotated[tuple[DatasetDefinition, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_datasets(self) -> Self:
        counts: Counter[RegistryIdentifier] = Counter(
            dataset.dataset_name for dataset in self.datasets
        )

        duplicates: list[RegistryIdentifier] = sorted(
            name for name, count in counts.items() if count > 1
        )

        if duplicates:
            raise ValueError("duplicate dataset_name values: " + ", ".join(duplicates))

        return self

    @property
    def source_datasets(self) -> tuple[DatasetDefinition, ...]:
        return tuple(dataset for dataset in self.datasets if dataset.visibility == "source")

    @property
    def internal_datasets(self) -> tuple[DatasetDefinition, ...]:
        return tuple(dataset for dataset in self.datasets if dataset.visibility == "internal")

    @property
    def source_systems(self) -> tuple[str, ...]:
        return tuple(sorted({dataset.source_system for dataset in self.source_datasets}))

    def get_dataset(self, dataset_name: str) -> DatasetDefinition:
        for dataset in self.datasets:
            if dataset.dataset_name == dataset_name:
                return dataset

        raise KeyError(f"unknown dataset: {dataset_name}")
