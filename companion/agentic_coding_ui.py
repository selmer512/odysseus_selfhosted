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
      <h2>Workspace</h2>
      <label>Path</label>
      <input id="workspace-path" placeholder="/workspace/odysseus">
      <label>Title</label>
      <input id="workspace-title" placeholder="Odysseus repository">
      <button id="register-workspace-button" type="button">Register workspace</button>
      <button id="refresh-workspaces-button" type="button" class="secondary">Refresh</button>
      <div id="workspace-list"></div>
    </section>
    <section class="card">
      <h2>Scaffold</h2>
      <label>Workspace</label>
      <select id="workspace-select"></select>
      <label>Model profile</label>
      <select id="profile-select"></select>
      <label>Goal</label>
      <textarea id="scaffold-goal" placeholder="Describe the code change to plan..."></textarea>
      <button id="generate-scaffold-button" type="button">Generate scaffold</button>
      <button id="approve-scaffold-button" type="button" class="secondary">Approve latest scaffold</button>
      <button id="create-run-button" type="button" class="secondary">Create run</button>
      <button id="prepare-artifacts-button" type="button" class="secondary">Prepare artifacts</button>
    </section>
  </main>
  <section class="card output-card">
    <h2>Output</h2>
    <pre id="agentic-log">Loading...</pre>
  </section>
  <script src="/static/agentic-coding.js"></script>
</body>
</html>"""