"""Health router factory for Agentic Coding."""

from fastapi import APIRouter


def make_router() -> APIRouter:
    router = APIRouter(prefix="/api/agentic-coding", tags=["agentic-coding"])

    @router.get("/health")
    def health():
        return {"ok": True, "feature": "agentic-coding"}

    return router
