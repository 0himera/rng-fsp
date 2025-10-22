from fastapi import APIRouter

from . import audit, entropy, rng

router = APIRouter()
router.include_router(entropy.router, prefix="/entropy", tags=["entropy"])
router.include_router(rng.router, prefix="/rng", tags=["rng"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])

__all__ = ["router"]
