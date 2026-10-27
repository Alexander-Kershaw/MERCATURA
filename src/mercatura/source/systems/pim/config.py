from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductSimulationConfig:
    """
    ==========================================================================================

    PRODUCT SIMULATION CONFIG

    ==========================================================================================

    - Considering 500 products
    - products span over 8 years
    - 80 percent of products existed before 2024
    - 20 percent launched during the 2024-2026 interval
    - 10 percent eventially are discontinued

    ==========================================================================================
    """

    product_count: int = 500
    history_years: int = 8
    launch_during_simulation_rate: float = 0.20
    discontinue_rate: float = 0.10

    def __post_init__(self) -> None:
        if self.product_count <= 0:
            raise ValueError("product_count must be positive")

        if self.history_years < 0:
            raise ValueError("history_years must be non-negative")

        for name, value in (
            (
                "launch_during_simulation_rate",
                self.launch_during_simulation_rate,
            ),
            (
                "discontinue_rate",
                self.discontinue_rate,
            ),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


DEFAULT_PRODUCT_CONFIG = ProductSimulationConfig()
