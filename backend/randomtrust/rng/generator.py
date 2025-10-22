from __future__ import annotations

import math
from dataclasses import dataclass
from hashlib import blake2s
from typing import Literal
from uuid import UUID

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms


@dataclass(slots=True)
class ChaCha20RNG:
    key: bytes
    nonce: bytes
    counter: int = 0

    def random_bytes(self, length: int) -> bytes:
        if length <= 0:
            return b""
        # cryptography's ChaCha20 implementation always starts from counter 0, so we
        # simulate an arbitrary starting counter by consuming blocks equal to the
        # current counter and discarding the bytes.
        algorithm = algorithms.ChaCha20(self.key, self.nonce)
        cipher = Cipher(algorithm, mode=None)
        encryptor = cipher.encryptor()

        if self.counter:
            discard = encryptor.update(b"\x00" * (self.counter * 64))
            # Ensure the discard occurs even if not used, satisfying counter advance.
            _ = discard

        data = encryptor.update(b"\x00" * length) + encryptor.finalize()
        blocks = math.ceil(length / 64)
        self.counter += blocks
        return data

    def random_hex(self, length: int) -> str:
        return self.random_bytes(length).hex()

    def random_ints(self, length: int) -> list[int]:
        return list(self.random_bytes(length))


class ChaCha20RNGFactory:
    def __init__(self, redis_client, namespace: str = "rng_runs") -> None:
        self._redis = redis_client
        self._namespace = namespace

    async def create_rng(self, run_id: UUID, seed: bytes) -> ChaCha20RNG:
        key = seed[:32]
        nonce = self._derive_nonce(run_id, seed)
        rng = ChaCha20RNG(key=key, nonce=nonce)
        await self._store_metadata(run_id, seed, nonce)
        return rng

    def _derive_nonce(self, run_id: UUID, seed: bytes) -> bytes:
        digest = blake2s(run_id.bytes + seed, digest_size=16)
        return digest.digest()

    async def _store_metadata(self, run_id: UUID, seed: bytes, nonce: bytes) -> None:
        key = f"{self._namespace}:{run_id}"
        await self._redis.hset(
            key,
            mapping={
                "seed_hex": seed.hex(),
                "nonce_hex": nonce.hex(),
                "counter": "0",
            },
        )

    async def increment_counter(self, run_id: UUID, blocks: int) -> None:
        key = f"{self._namespace}:{run_id}"
        await self._redis.hincrby(key, "counter", blocks)


RNGOutputFormat = Literal["hex", "ints"]
