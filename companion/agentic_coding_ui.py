"""Agentic Coding UI helper."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


def make_agentic_coding_ui_router() -> APIRouter:
    router = APIRouter(tags=["agentic-coding-ui"])

    @router.get("/agentic-coding", response_class=HTMLResponse)
    def page():
        return HTMLResponse(_PAGE)

    return router


_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Agentic Coding - Odysseus</title>
  <link rel="stylesheet" href="/static/agentic-coding.css">
</head>
<body>
  <header>
    <div>
      <h1>Agentic Coding</h1>
      <p class="muted">Review-first repository work with explicit approval gates.</p>
    </div>
    <a href="/">Back to Odysseus</a>
  </header>
  <main>
    <section class="card">
      <span class="pill" id="agentic-status">Checking backend...</span>
      <h2>Workflow</h2>
      <ol>
        <li>Register a vetted workspace.</li>
        <li>Scan the repository.</li>
        <li>Create and approve a scaffold.</li>
        <li>Create a run and prepare artifacts.</li>
      </ol>
      <button onclick="agenticCodingRefresh()">Refresh status</button>
    </section>
    <section class="card">
      <h2>Backend status</h2>
      <pre id="agentic-log">Loading...</pre>
    </section>
  </main>
  <script src="/static/agentic-coding.js"></script>
</body>
</html>"""
