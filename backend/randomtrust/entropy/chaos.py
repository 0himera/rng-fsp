from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LorenzConfig:
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0
    dt: float = 1e-3
    steps: int = 10_000


class LorenzChaosSimulator:
    def __init__(self, config: LorenzConfig | None = None) -> None:
        self._config = config or LorenzConfig()

    @property
    def config(self) -> LorenzConfig:
        return self._config

    def run(self, seed_vector: np.ndarray | None = None, overrides: LorenzConfig | None = None) -> np.ndarray:
        cfg = overrides or self._config
        state = self._initial_state(seed_vector)
        trajectory = np.empty((cfg.steps, 3), dtype=np.float64)

        for i in range(cfg.steps):
            x, y, z = state
            dx = cfg.sigma * (y - x)
            dy = x * (cfg.rho - z) - y
            dz = x * y - cfg.beta * z
            state = state + cfg.dt * np.array([dx, dy, dz])
            trajectory[i] = state

        return trajectory

    def _initial_state(self, seed_vector: np.ndarray | None) -> np.ndarray:
        if seed_vector is None:
            seed_vector = np.array([1.0, 1.0, 1.0], dtype=np.float64)

        seed_vector = np.asarray(seed_vector, dtype=np.float64).flatten()
        if seed_vector.size < 3:
            padded = np.pad(seed_vector, (0, 3 - seed_vector.size), mode="wrap")
            seed_vector = padded

        # avoid zero values which can collapse dynamics
        seed_vector = np.where(np.isclose(seed_vector, 0.0), 1e-6, seed_vector)
        return seed_vector[:3]
