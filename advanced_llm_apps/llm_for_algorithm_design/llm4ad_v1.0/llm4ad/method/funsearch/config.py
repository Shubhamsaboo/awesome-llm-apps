from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class ProgramsDatabaseConfig:
    """Configuration of a ProgramsDatabase.

    Attributes:
        functions_per_prompt: Number of previous programs to include in prompts.
        num_islands: Number of islands to maintain as a diversity mechanism.
        reset_period: How often (in seconds) the weakest islands should be reset.
        cluster_sampling_temperature_init: Initial temperature for softmax sampling
            of clusters within an island.
        cluster_sampling_temperature_period: Period of linear decay of the cluster
            sampling temperature.
    """
    functions_per_prompt: int = 2
    num_islands: int = 10
    reset_period: int = 4 * 60 * 60
    cluster_sampling_temperature_init: float = 0.1
    cluster_sampling_temperature_period: int = 30_000
