from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class ReconciliationCheck:
    code: str
    description: str
    actual: int
    expected: int

    @property
    def passed(self) -> bool:
        return self.actual == self.expected


@dataclass(
    frozen=True,
    slots=True,
)
class EstateReconciliationReport:
    checks: tuple[
        ReconciliationCheck,
        ...,
    ]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(
        self,
    ) -> tuple[
        ReconciliationCheck,
        ...,
    ]:
        return tuple(check for check in self.checks if not check.passed)
