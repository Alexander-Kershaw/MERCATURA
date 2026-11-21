from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class ReturnsSimulationConfig:
    return_probability: float = 0.08
    partial_return_probability: float = 0.30
    minimum_return_delay_days: int = 2
    maximum_return_delay_days: int = 30

    def __post_init__(self) -> None:
        if not (0.0 <= self.return_probability <= 1.0):
            raise ValueError("return_probability must be between 0 and 1")

        if not (0.0 <= self.partial_return_probability <= 1.0):
            raise ValueError("partial_return_probability must be between 0 and 1")

        if self.minimum_return_delay_days < 0:
            raise ValueError("minimum return delay cannot be negative")

        if self.maximum_return_delay_days < self.minimum_return_delay_days:
            raise ValueError("maximum return delay cannot be less than minimum")


DEFAULT_RETURNS_CONFIG = ReturnsSimulationConfig()
