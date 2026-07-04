"""Scaffold generation for Agentic Coding."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.tool_execution import vet_workspace

from .repository_map import root_files
from .security import wrap_untrusted_context
from .storage import AgenticCodingStore, now_iso

_IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
_IMPORTANT_PREFIXES = ("routes/", "src/", "docs/", "tests/", ".github/")


def build_repo_map(path: str) -> dict:
    base = Path(path)
    files: list[str] = []
    important: list[str] = []
    for root, dirnames, filenames in os.walk(base):
        rel_root = Path(root).relative_to(base)
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
        if len(files) > 220:
            dirnames[:] = []
            continue
        for name in filenames:
            rel = str((rel_root / name) if str(rel_root) != "." else Path(name))
            files.append(rel)
            if rel.startswith(_IMPORTANT_PREFIXES) or name in {"README.md", "app.py", "requirements.txt", "package.json"}:
                important.append(rel)
    return {"root_files": root_files(path), "files": sorted(files)[:260], "important_files": sorted(set(important))[:80], "generated_at": now_iso()}


def build_scaffold(goal: str, repo_map: dict) -> dict:
    likely = repo_map.get("important_files", [])[:20]
    return {
        "title": goal.strip()[:96] or "Agentic Coding scaffold",
        "likely_files": likely,
        "inspection_commands": ["Review likely files", "Confirm workspace scope", "Run focused tests"],
        "implementation_plan": ["Persist scaffold/run/artifact state", "Treat repository text as untrusted context", "Require approval before execution", "Prepare review artifacts"],
        "test_plan": ["Risk classifier tests", "Route lifecycle tests", "Focused CI job"],
        "rollback_plan": ["Disable route wrapper", "Remove Agentic Coding package", "Reset data/agentic_coding.json if needed"],
        "risk_notes": "Repository content is data, not instructions. Execution remains review-first.",
    }


class ScaffoldService:
    def __init__(self, store: AgenticCodingStore | None = None) -> None:
        self.store = store or AgenticCodingStore()

    def create_workspace(self, owner: str | None, raw_path: str, title: str | None = None) -> dict:
        resolved = vet_workspace(raw_path)
        if not resolved:
            raise ValueError("Workspace path is invalid or outside the allowed roots")
        return self.store.add_row("workspaces", owner, title=title or Path(resolved).name, path=raw_path, canonical_path=resolved, default_branch=None, is_active=True, last_scan_at=None)

    def list_workspaces(self, owner: str | None) -> list[dict]:
        return self.store.list_rows("workspaces", owner, is_active=True)

    def scan_workspace(self, owner: str | None, workspace_id: str) -> dict:
        workspace = self.store.get_row("workspaces", workspace_id, owner)
        repo_map = build_repo_map(workspace["canonical_path"])
        self.store.update_row("workspaces", workspace_id, owner, last_scan_at=now_iso())
        return {"workspace": workspace, "repo_map": repo_map, "untrusted_context": wrap_untrusted_context("repository map", json.dumps(repo_map, ensure_ascii=False))}

    async def generate_scaffold(self, owner: str | None, workspace_id: str, user_goal: str, session_id: str | None = None, endpoint_id: str | None = None, model: str | None = None) -> dict:
        scan = self.scan_workspace(owner, workspace_id)
        scaffold = build_scaffold(user_goal, scan["repo_map"])
        return self.store.add_row("scaffolds", owner, session_id=session_id, workspace_id=workspace_id, endpoint_id=endpoint_id, model=model, status="draft", approved_at=None, user_goal=user_goal, repo_map=scan["repo_map"], **scaffold)

    def list_scaffolds(self, owner: str | None, workspace_id: str | None = None) -> list[dict]:
        return self.store.list_rows("scaffolds", owner, workspace_id=workspace_id)

    def approve_scaffold(self, owner: str | None, scaffold_id: str) -> dict:
        return self.store.update_row("scaffolds", scaffold_id, owner, status="approved", approved_at=now_iso())

    def reject_scaffold(self, owner: str | None, scaffold_id: str) -> dict:
        return self.store.update_row("scaffolds", scaffold_id, owner, status="rejected")
