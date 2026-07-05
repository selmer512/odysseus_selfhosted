"""Odysseus companion bridge — additive LAN endpoints."""

import logging

from fastapi import APIRouter

from companion.routes import setup_companion_routes as _setup_companion_routes
from companion.agentic_coding_ui import make_agentic_coding_ui_router

logger = logging.getLogger(__name__)


def setup_companion_routes() -> APIRouter:
    router = APIRouter()
    router.include_router(_setup_companion_routes())
    try:
        from src.agentic_coding.health_router import make_router as _agentic_coding_router
        router.include_router(_agentic_coding_router())
        logger.info("Agentic Coding API routes initialized at /api/agentic-coding")
    except Exception:
        logger.exception("Agentic Coding API routes failed to initialize")
    router.include_router(make_agentic_coding_ui_router())
    logger.info("Agentic Coding UI route initialized at /agentic-coding")
    return router


__all__ = ["setup_companion_routes"]
