from __future__ import annotations

import io
import uuid

from minio import Minio

from randomtrust.core import Settings
from randomtrust.entropy import EntropyMixer

from .unit_of_work import UnitOfWork


class StoredEntropy:
    def __init__(
        self,
        *,
        simulation_id: uuid.UUID,
        seed: bytes,
        metrics: dict[str, float],
    ) -> None:
        self.simulation_id = simulation_id
        self.seed = seed
        self.metrics = metrics

    @property
    def seed_hex(self) -> str:
        return self.seed.hex()


class EntropyService:
    def __init__(
        self,
        *,
        mixer: EntropyMixer,
        storage: Minio,
        settings: Settings,
    ) -> None:
        self._mixer = mixer
        self._storage = storage
        self._settings = settings

    async def create_entropy(
        self,
        *,
        uow: UnitOfWork,
        noise_seed: int | None,
        overrides: dict[str, float] | None,
    ) -> StoredEntropy:
        result = self._mixer.mix_entropy(noise_seed=noise_seed, parameter_overrides=overrides)
        simulation_id = uuid.uuid4()

        noise_path = self._upload_buffer(result.noise_sample.signal.tobytes(), f"entropy/sim_raw/{simulation_id}.bin")
        chaos_path = self._upload_buffer(
            result.chaos_trajectory.astype("<f4").tobytes(),
            f"chaos/{simulation_id}.bin",
        )

        repo = uow.entropy
        await repo.add_simulation(
            simulation_id=simulation_id,
            noise_seed=noise_seed,
            noise_config=result.noise_config,
            metrics={
                "snr_db": result.metrics.snr_db,
                "spectral_deviation_percent": result.metrics.spectral_deviation_percent,
                "lyapunov_exponent": result.metrics.lyapunov_exponent,
            },
            seed_hex=result.seed.hex(),
            pool_hash=result.pool_hash,
            chaos_checksum=result.chaos_checksum,
            noise_raw_path=noise_path,
            chaos_raw_path=chaos_path,
        )

        await repo.add_chaos_run(
            simulation_id=simulation_id,
            config=result.chaos_config,
            lyapunov_exponent=result.metrics.lyapunov_exponent,
            trajectory_checksum=result.chaos_checksum,
        )

        return StoredEntropy(
            simulation_id=simulation_id,
            seed=result.seed,
            metrics={
                "snr_db": result.metrics.snr_db,
                "spectral_deviation_percent": result.metrics.spectral_deviation_percent,
                "lyapunov_exponent": result.metrics.lyapunov_exponent,
            },
        )

    def _upload_buffer(self, data: bytes, path: str) -> str:
        stream = io.BytesIO(data)
        self._storage.put_object(
            self._settings.minio_bucket,
            path,
            data=stream,
            length=len(data),
            content_type="application/octet-stream",
        )
        return path
