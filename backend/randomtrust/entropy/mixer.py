from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .chaos import LorenzChaosSimulator, LorenzConfig
from .simulator import NoiseConfig, NoiseSample, NoiseSimulator

_EPS = 1e-12


@dataclass(frozen=True)
class EntropyMetricsData:
    snr_db: float
    spectral_deviation_percent: float
    lyapunov_exponent: float


@dataclass(frozen=True)
class EntropyMixResult:
    seed: bytes
    pool_hash: bytes
    chaos_checksum: str
    noise_config: dict[str, Any]
    chaos_config: dict[str, Any]
    metrics: EntropyMetricsData
    noise_sample: NoiseSample
    chaos_trajectory: np.ndarray


class EntropyMixer:
    def __init__(
        self,
        noise_simulator: NoiseSimulator,
        chaos_simulator: LorenzChaosSimulator,
    ) -> None:
        self._noise_simulator = noise_simulator
        self._chaos_simulator = chaos_simulator

    def mix_entropy(
        self,
        noise_seed: int | None = None,
        parameter_overrides: dict[str, Any] | None = None,
    ) -> EntropyMixResult:
        noise_config = self._build_noise_config(parameter_overrides)
        noise_sample = self._noise_simulator.generate(seed=noise_seed, overrides=noise_config)

        seed_vector = self._build_seed_vector(noise_sample.signal)
        chaos_cfg = self._chaos_simulator.config
        chaos_trajectory = self._chaos_simulator.run(seed_vector=seed_vector, overrides=None)

        pool_hash, chaos_checksum = self._combine_entropy(noise_sample, chaos_trajectory)
        seed = self._derive_seed(pool_hash)
        metrics = self._calculate_metrics(noise_sample, chaos_trajectory, chaos_cfg)

        return EntropyMixResult(
            seed=seed,
            pool_hash=pool_hash,
            chaos_checksum=chaos_checksum,
            noise_config=asdict(noise_config),
            chaos_config=asdict(chaos_cfg),
            metrics=metrics,
            noise_sample=noise_sample,
            chaos_trajectory=chaos_trajectory,
        )

    def _build_noise_config(self, overrides: dict[str, Any] | None) -> NoiseConfig:
        if not overrides:
            return self._noise_simulator.config

        valid_keys = {field for field in NoiseConfig.__dataclass_fields__.keys()}
        filtered: dict[str, Any] = {k: v for k, v in overrides.items() if k in valid_keys and v is not None}
        return replace(self._noise_simulator.config, **filtered)

    def _build_seed_vector(self, signal: np.ndarray) -> np.ndarray:
        if signal.size < 6:
            padded = np.pad(signal, (0, 6 - signal.size), mode="wrap")
        else:
            padded = signal[:6]
        reshaped = padded.reshape(2, 3).mean(axis=0)
        reshaped = np.where(np.abs(reshaped) < 1e-6, 1e-6, reshaped)
        return reshaped.astype(np.float64)

    def _combine_entropy(self, noise_sample: NoiseSample, chaos_trajectory: np.ndarray) -> tuple[bytes, str]:
        noise_bytes = np.clip((noise_sample.signal + 1.0) * 127.5, 0, 255).astype(np.uint8).tobytes()
        chaos_bytes = chaos_trajectory.astype(np.float32).tobytes()
        mix_buffer = noise_bytes + chaos_bytes
        digest = hashes.Hash(hashes.SHA3_512())
        digest.update(mix_buffer)
        pool_hash = digest.finalize()

        checksum = hashes.Hash(hashes.BLAKE2s(32))
        checksum.update(chaos_bytes)
        chaos_checksum = checksum.finalize().hex()

        return pool_hash, chaos_checksum

    def _derive_seed(self, pool_hash: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.BLAKE2s(32),
            length=32,
            salt=pool_hash[:16],
            info=b"RandomTrustEntropyMix",
        )
        return hkdf.derive(pool_hash)

    def _calculate_metrics(
        self,
        noise_sample: NoiseSample,
        chaos_trajectory: np.ndarray,
        chaos_config: LorenzConfig,
    ) -> EntropyMetricsData:
        signal_power = float(np.mean(np.square(noise_sample.signal)) + _EPS)
        noise_power = float(
            np.mean(np.square(noise_sample.noise_component + noise_sample.spike_component)) + _EPS
        )
        snr_db = 10.0 * np.log10(signal_power / noise_power)

        spectrum = np.abs(np.fft.rfft(noise_sample.signal))
        avg_magnitude = np.mean(spectrum) + _EPS
        spectral_deviation_percent = float(np.mean(np.abs(spectrum - avg_magnitude) / avg_magnitude) * 100.0)

        lyapunov = self._estimate_lyapunov(chaos_trajectory, chaos_config.dt)

        return EntropyMetricsData(
            snr_db=float(snr_db),
            spectral_deviation_percent=spectral_deviation_percent,
            lyapunov_exponent=lyapunov,
        )

    def _estimate_lyapunov(self, trajectory: np.ndarray, dt: float) -> float:
        shifted = trajectory[:-1]
        next_state = trajectory[1:]
        if shifted.size == 0:
            return 0.0
        diffs = np.linalg.norm(next_state - shifted, axis=1)
        diffs = np.where(diffs <= _EPS, _EPS, diffs)
        lyapunov = np.mean(np.log(diffs / dt))
        return float(max(lyapunov, 0.0))
