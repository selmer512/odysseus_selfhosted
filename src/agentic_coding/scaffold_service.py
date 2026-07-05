"""Scaffold generation for Agentic Coding."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.tool_execution import vet_workspace

from .repository_map import is_important_file, ordered_walk_roots, root_files
from .security import wrap_untrusted_context
from .storage import AgenticCodingStore, now_iso

_IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".cache"}


def _repo_relative(base: Path, path: Path) -> str:
    rel = path.relative_to(base)
    return str(rel).replace(os.sep, "/")


def build_repo_map(path: str) -> dict:
    base = Path(path)
    files: list[str] = []
    important: list[str] = []
    seen: set[str] = set()
    for walk_root in ordered_walk_roots(path):
        for root, dirnames, filenames in os.walk(walk_root):
            rel_root = Path(root).relative_to(base)
            dirnames[:] = [d for d in sorted(dirnames) if d not in _IGNORE_DIRS]
            for name in sorted(filenames):
                rel = _repo_relative(base, rel_root / name)
                if rel in seen:
                    continue
                seen.add(rel)
                if is_important_file(rel):
                    important.append(rel)
                files.append(rel)
                if len(files) >= 360:
                    break
            if len(files) >= 360:
                dirnames[:] = []
                break
        if len(files) >= 360:
            break
    return {"root_files": root_files(path), "files": files[:360], "important_files": important[:120], "generated_at": now_iso()}


def build_scaffold(goal: str, repo_map: dict) -> dict:
    likely = repo_map.get("important_files", [])[:30]
    return {
        "title": goal.strip()[:96] or "Agentic Coding scaffold",
        "likely_files": likely,
        "inspection_commands": ["Review likely files", "Confirm workspace scope", "Run focused tests"],
        "implementation_plan": ["Inspect likely files", "Prepare a minimal patch", "Keep destructive steps behind approval", "Generate review artifacts before execution"],
        "test_plan": ["Run focused Agentic Coding tests", "Verify workspace registration in browser", "Confirm generated artifacts are persisted"],
        "rollback_plan": ["Revert the focused patch", "Restart Odysseus", "Rerun focused tests"],
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
