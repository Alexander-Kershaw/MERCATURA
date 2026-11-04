from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InventoryMovementSimulationConfig:
    same_day_putaway_probability: float = 0.85
    next_day_putaway_probability: float = 0.12
    two_day_putaway_probability: float = 0.03

    def __post_init__(self) -> None:
        probabilities: tuple[float, float, float] = (
            self.same_day_putaway_probability,
            self.next_day_putaway_probability,
            self.two_day_putaway_probability,
        )

        if any(probability < 0.0 or probability > 1.0 for probability in probabilities):
            raise ValueError("putaway probabilities must be between 0 and 1")

        if abs(sum(probabilities) - 1.0) > 1e-9:
            raise ValueError("putaway probabilities must sum to 1")


DEFAULT_INVENTORY_MOVEMENT_CONFIG = InventoryMovementSimulationConfig()
