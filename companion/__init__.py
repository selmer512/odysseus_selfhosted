"""Odysseus companion bridge — additive LAN endpoints."""

from fastapi import APIRouter

from companion.routes import setup_companion_routes as _setup_companion_routes
from companion.agentic_coding_ui import make_agentic_coding_ui_router


def setup_companion_routes() -> APIRouter:
    router = APIRouter()
    router.include_router(_setup_companion_routes())
    try:
        from src.agentic_coding.health_router import make_router as _agentic_coding_router
        router.include_router(_agentic_coding_router())
    except Exception:
        pass
    router.include_router(make_agentic_coding_ui_router())
    return router


__all__ = ["setup_companion_routes"]
