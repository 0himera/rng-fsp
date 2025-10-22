from fastapi import APIRouter

from . import analysis, audit, entropy, rng

router = APIRouter()
router.include_router(entropy.router, prefix="/entropy", tags=["entropy"])
router.include_router(rng.router, prefix="/rng", tags=["rng"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])

__all__ = ["router"]
