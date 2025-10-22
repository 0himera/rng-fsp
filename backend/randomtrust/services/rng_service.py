from __future__ import annotations

import io
import uuid
from hashlib import blake2s

from minio import Minio

from randomtrust.core import Settings
from randomtrust.rng.generator import ChaCha20RNGFactory

from .entropy_service import EntropyService
from .unit_of_work import UnitOfWork


class GeneratedSequence:
    def __init__(
        self,
        *,
        run_id: uuid.UUID,
        data: str | list[int],
        format: str,
        metrics: dict[str, float],
    ) -> None:
        self.run_id = run_id
        self.data = data
        self.format = format
        self.metrics = metrics


class RNGService:
    def __init__(
        self,
        *,
        entropy_service: EntropyService,
        rng_factory: ChaCha20RNGFactory,
        storage: Minio,
        settings: Settings,
    ) -> None:
        self._entropy_service = entropy_service
        self._rng_factory = rng_factory
        self._storage = storage
        self._settings = settings

    async def generate(
        self,
        *,
        uow: UnitOfWork,
        length: int,
        fmt: str,
        noise_seed: int | None,
        overrides: dict[str, float] | None,
    ) -> GeneratedSequence:
        stored_entropy = await self._entropy_service.create_entropy(
            uow=uow,
            noise_seed=noise_seed,
            overrides=overrides,
        )

        run_id = uuid.uuid4()
        rng = await self._rng_factory.create_rng(run_id=run_id, seed=stored_entropy.seed)

        if fmt == "hex":
            data = rng.random_hex(length)
        elif fmt == "ints":
            data = rng.random_ints(length)
        else:
            raise ValueError("Unsupported format")

        checksum = self._store_sequence(run_id, data, fmt)

        repo = uow.rng
        await repo.add_run(
            run_id=run_id,
            entropy_simulation_id=stored_entropy.simulation_id,
            run_format=fmt,
            length=length,
            entropy_metrics=stored_entropy.metrics,
            seed_hash=blake2s(stored_entropy.seed).hexdigest(),
            export_path=checksum["path"],
            run_checksum=checksum["digest"],
        )

        return GeneratedSequence(
            run_id=run_id,
            data=data,
            format=fmt,
            metrics=stored_entropy.metrics,
        )

    def _store_sequence(self, run_id: uuid.UUID, data: str | list[int], fmt: str) -> dict[str, bytes | str]:
        if isinstance(data, list):
            payload = bytes(data)
        else:
            payload = bytes.fromhex(data) if fmt == "hex" else data.encode()

        path = f"runs/{run_id}/sequence.bin"
        stream = io.BytesIO(payload)
        self._storage.put_object(
            self._settings.minio_bucket,
            path,
            data=stream,
            length=len(payload),
            content_type="application/octet-stream",
        )

        digest = blake2s(payload).digest()
        return {"path": path, "digest": digest}
