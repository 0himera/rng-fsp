from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NoiseConfig:
    sample_rate: int = 48_000
    duration_ms: int = 200
    hum_frequencies: tuple[float, float] = (50.0, 60.0)
    hum_amplitude: float = 0.35
    noise_bandwidth: tuple[float, float] = (40.0, 1_200.0)
    noise_amplitude: float = 0.45
    spike_density: float = 0.01
    spike_amplitude: float = 0.2


@dataclass(frozen=True)
class NoiseSample:
    signal: np.ndarray
    hum_component: np.ndarray
    noise_component: np.ndarray
    spike_component: np.ndarray


class NoiseSimulator:
    def __init__(self, config: NoiseConfig | None = None) -> None:
        self._config = config or NoiseConfig()

    @property
    def config(self) -> NoiseConfig:
        return self._config

    def generate(
        self,
        seed: int | None = None,
        overrides: NoiseConfig | None = None,
    ) -> NoiseSample:
        cfg = overrides or self._config
        rng = np.random.default_rng(seed)
        sample_count = max(int(cfg.sample_rate * cfg.duration_ms / 1_000), 1)

        t = np.linspace(0, cfg.duration_ms / 1_000, sample_count, endpoint=False)
        hum = np.zeros_like(t)
        for freq in cfg.hum_frequencies:
            phase = rng.uniform(0, 2 * np.pi)
            hum += cfg.hum_amplitude * np.sin(2 * np.pi * freq * t + phase)

        # Band-limited white noise via frequency domain shaping
        white_noise = rng.standard_normal(sample_count)
        spectrum = np.fft.rfft(white_noise)
        freqs = np.fft.rfftfreq(sample_count, d=1 / cfg.sample_rate)
        band_mask = (freqs >= cfg.noise_bandwidth[0]) & (freqs <= cfg.noise_bandwidth[1])
        spectrum *= band_mask.astype(float)
        shaped_noise = np.fft.irfft(spectrum, n=sample_count)
        shaped_noise = cfg.noise_amplitude * shaped_noise / (np.linalg.norm(shaped_noise) + 1e-12)

        spikes = np.zeros_like(t)

        spike_count = int(cfg.spike_density * sample_count)
        if spike_count > 0:
            spike_positions = rng.choice(sample_count, size=spike_count, replace=False)
            spike_values = cfg.spike_amplitude * rng.uniform(-1.0, 1.0, size=spike_count)
            spikes[spike_positions] = spike_values

        signal = hum + shaped_noise + spikes

        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val
            hum = hum / max_val
            shaped_noise = shaped_noise / max_val
            spikes = spikes / max_val

        return NoiseSample(
            signal=signal.astype(np.float32),
            hum_component=hum.astype(np.float32),
            noise_component=shaped_noise.astype(np.float32),
            spike_component=spikes.astype(np.float32),
        )
