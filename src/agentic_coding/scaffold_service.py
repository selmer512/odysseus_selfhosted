"""Scaffold generation for Agentic Coding."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from src.tool_execution import vet_workspace

from .repository_map import is_important_file, ordered_walk_roots, root_files
from .security import wrap_untrusted_context
from .storage import AgenticCodingStore, now_iso

_IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".cache"}
_AGENTIC_PATHS = (
    "src/agentic_coding/",
    "companion/agentic_coding_ui.py",
    "static/agentic-coding.js",
    "static/agentic-coding.css",
    "tests/test_agentic_coding",
    ".github/workflows/agentic-coding.yml",
    "docs/agentic-coding",
)


def _repo_relative(base: Path, path: Path) -> str:
    rel = path.relative_to(base)
    return str(rel).replace(os.sep, "/")


def _goal_terms(goal: str) -> set[str]:
    return {term for term in re.split(r"[^a-z0-9]+", (goal or "").lower()) if len(term) >= 4}


def _score_file(path: str, goal: str) -> tuple[int, str]:
    lower = path.lower()
    terms = _goal_terms(goal)
    score = 0
    if any(lower.startswith(prefix) or lower == prefix for prefix in _AGENTIC_PATHS):
        score += 120
    if "agentic" in terms or "coding" in terms:
        if "agentic" in lower or "coding" in lower:
            score += 90
    if "workspace" in terms and "workspace" in lower:
        score += 40
    if "artifact" in terms and ("artifact" in lower or "run_service" in lower):
        score += 40
    if "scaffold" in terms and "scaffold" in lower:
        score += 40
    if lower.startswith("tests/"):
        score += 15
    if lower.startswith("docs/"):
        score += 10
    score += sum(5 for term in terms if term in lower)
    return (-score, path)


def rank_likely_files(goal: str, repo_map: dict, limit: int = 30) -> list[str]:
    candidates = list(dict.fromkeys((repo_map.get("important_files") or []) + (repo_map.get("files") or [])))
    ranked = sorted(candidates, key=lambda path: _score_file(path, goal))
    return ranked[:limit]


def build_repo_map(path: str) -> dict:
    base = Path(path)
    files: list[str] = []
    important: list[str] = []
    seen: set[str] = set()
    for walk_root in ordered_walk_roots(path):
        for root, dirnames, filenames in os.walk(walk_root):
            root_path = Path(root)
            dirnames[:] = [d for d in sorted(dirnames) if d not in _IGNORE_DIRS]
            for name in sorted(filenames):
                rel = _repo_relative(base, root_path / name)
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
    likely = rank_likely_files(goal, repo_map)
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
