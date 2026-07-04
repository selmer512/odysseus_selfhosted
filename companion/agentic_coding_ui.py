"""Agentic Coding UI helper."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


def make_agentic_coding_ui_router() -> APIRouter:
    router = APIRouter(tags=["agentic-coding-ui"])

    @router.get("/agentic-coding", response_class=HTMLResponse)
    def page():
        return HTMLResponse("<h1>Agentic Coding</h1><p>Use /api/agentic-coding/health to verify the backend.</p><p><a href='/'>Back to Odysseus</a></p>")

    return router
