from __future__ import annotations

import io
import uuid
from dataclasses import dataclass
from hashlib import blake2s

from minio import Minio
from minio.error import S3Error

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


class RunExportError(RuntimeError):
    """Base error for run export operations."""


class RunNotFoundError(RunExportError):
    pass


class RunDataUnavailableError(RunExportError):
    pass


class InsufficientBitsError(RunExportError):
    def __init__(self, available: int, required: int) -> None:
        super().__init__(f"available bits {available} less than required {required}")
        self.available = available
        self.required = required


@dataclass(slots=True)
class RunBitsExport:
    run_id: uuid.UUID
    bits_count: int
    content: bytes
    filename: str


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
        # Always obtain fresh entropy so each run is traceable to a simulation record.
        stored_entropy = await self._entropy_service.create_entropy(
            uow=uow,
            noise_seed=noise_seed,
            overrides=overrides,
        )

        run_id = uuid.uuid4()
        # ChaCha20 key/nonce pair derives from the stored seed.
        rng = await self._rng_factory.create_rng(run_id=run_id, seed=stored_entropy.seed)

        if fmt == "hex":
            data = rng.random_hex(length)
        elif fmt == "ints":
            data = rng.random_ints(length)
        else:
            raise ValueError("Unsupported format")

        # Sequence is persisted in MinIO to support later audits/export.
        checksum = self._store_sequence(run_id, data, fmt)

        repo = uow.rng
        # Persist metadata enabling reproducibility and linkage to entropy simulation.
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
        # Store opaque binary so consumers can choose export format later.
        self._storage.put_object(
            self._settings.minio_bucket,
            path,
            data=stream,
            length=len(payload),
            content_type="application/octet-stream",
        )

        digest = blake2s(payload).digest()
        return {"path": path, "digest": digest}

    async def export_bits(
        self,
        *,
        uow: UnitOfWork,
        run_id: uuid.UUID,
        min_bits: int = 1_000_000,
    ) -> RunBitsExport:
        run = await uow.rng.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"run {run_id} not found")
        if not run.export_path:
            raise RunDataUnavailableError("run has no persisted sequence to export")

        # Download the raw bytes and transform them to human-readable bit string.
        payload = self._download_sequence(run.export_path)
        bits_text = self._bytes_to_bits_text(payload)
        bits_count = len(bits_text)
        if bits_count < min_bits:
            raise InsufficientBitsError(bits_count, min_bits)

        filename = f"{run_id}_bits.txt"
        content = bits_text.encode("ascii")
        return RunBitsExport(run_id=run_id, bits_count=bits_count, content=content, filename=filename)

    def _download_sequence(self, path: str) -> bytes:
        obj = None
        try:
            obj = self._storage.get_object(self._settings.minio_bucket, path)
            data = obj.read()
        except S3Error as exc:
            raise RunDataUnavailableError(f"failed to fetch object {path}: {exc}") from exc
        finally:
            if obj is not None:
                try:
                    obj.close()
                    obj.release_conn()
                except Exception:
                    pass
        return data

    @staticmethod
    def _bytes_to_bits_text(payload: bytes) -> str:
        return "".join(f"{byte:08b}" for byte in payload)
