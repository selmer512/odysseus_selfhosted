"""Odysseus companion bridge — additive LAN endpoints.

Read endpoints (/api/companion/ping, /info, owner-scoped /models) so a LAN
client can discover what a server offers, plus admin-only pairing
(/api/companion/pair) that mints a one-time chat-scoped token on POST. No new LLM
logic; auth is enforced by the existing AuthMiddleware. See companion/README.md.
"""

from fastapi import APIRouter

from companion.routes import setup_companion_routes as _setup_companion_routes


def setup_companion_routes() -> APIRouter:
    """Return companion routes plus additive adjacent feature routers.

    app.py already imports this single factory near the end of startup. Wrapping
    here lets the Agentic Coding slice mount without expanding the app
    orchestrator, which keeps the change bounded and reversible.
    """
    router = APIRouter()
    router.include_router(_setup_companion_routes())
    try:
        from src.agentic_coding.health_router import make_router as _agentic_coding_router

        router.include_router(_agentic_coding_router())
    except Exception:
        # Keep the companion bridge resilient even if an experimental feature is
        # unavailable during partial upgrades.
        pass
    return router


__all__ = ["setup_companion_routes"]
