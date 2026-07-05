"""Scaffold generation for Agentic Coding."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from src.tool_execution import vet_workspace

from .repository_map import is_important_file, ordered_walk_roots, root_files
from .security import wrap_untrusted_context
from .source_context import context_bullets, summarize_likely_files
from .storage import AgenticCodingStore, now_iso

_IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".cache"}
_AGENTIC_PATHS = (
    "src/agentic_coding/",
    "companion/agentic_coding_ui.py",
    "static/agentic-coding",
    "tests/test_agentic_coding",
    ".github/workflows/agentic-coding.yml",
    "docs/agentic-coding",
)
_AUTH_PATH_HINTS = (
    "core/auth.py",
    "routes/auth_routes.py",
    "src/auth_helpers.py",
    "src/secret_storage.py",
    "src/runtime_paths.py",
    "scripts/",
    "tests/test_auth",
    "tests/test_admin",
    "tests/test_reset",
    "docs/",
    "README.md",
)


def _repo_relative(base: Path, path: Path) -> str:
    rel = path.relative_to(base)
    return str(rel).replace(os.sep, "/")


def _goal_terms(goal: str) -> set[str]:
    return {term for term in re.split(r"[^a-z0-9]+", (goal or "").lower()) if len(term) >= 4}


def _has_any(terms: set[str], values: tuple[str, ...]) -> bool:
    return any(value in terms for value in values)


def _path_matches(path: str, hints: tuple[str, ...]) -> bool:
    lower = path.lower()
    for hint in hints:
        h = hint.lower()
        if lower == h or lower.startswith(h) or h in lower:
            return True
    return False


def _score_file(path: str, goal: str) -> tuple[int, str]:
    lower = path.lower()
    terms = _goal_terms(goal)
    score = 0

    is_agentic_goal = _has_any(terms, ("agentic", "coding", "scaffold", "artifact", "workspace"))
    is_auth_goal = _has_any(terms, ("auth", "admin", "password", "reset", "login", "user", "username", "credential"))
    is_script_goal = _has_any(terms, ("script", "utility", "docker", "container", "cli", "command"))
    is_docs_goal = _has_any(terms, ("docs", "documentation", "readme", "usage"))
    is_test_goal = _has_any(terms, ("test", "tests", "pytest"))

    if is_agentic_goal and _path_matches(lower, _AGENTIC_PATHS):
        score += 120
    if is_auth_goal and _path_matches(lower, _AUTH_PATH_HINTS):
        score += 140
    if is_auth_goal and ("auth" in lower or "login" in lower or "secret" in lower):
        score += 90
    if is_auth_goal and ("admin" in lower or "user" in lower):
        score += 45
    if is_script_goal and (lower.startswith("scripts/") or "script" in lower or lower.endswith(".sh") or lower.endswith(".py")):
        score += 55
    if "password" in terms and ("password" in lower or "auth" in lower or "secret" in lower):
        score += 75
    if "reset" in terms and ("reset" in lower or "auth" in lower or "admin" in lower):
        score += 65
    if "docker" in terms or "container" in terms:
        if lower in ("dockerfile", "docker-compose.yml") or lower.startswith("docker"):
            score += 50
    if is_test_goal and lower.startswith("tests/"):
        score += 45
    if is_docs_goal and (lower.startswith("docs/") or lower == "readme.md"):
        score += 40
    if "workspace" in terms and "workspace" in lower:
        score += 40
    if "artifact" in terms and ("artifact" in lower or "run_service" in lower):
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
                if len(files) >= 420:
                    break
            if len(files) >= 420:
                dirnames[:] = []
                break
        if len(files) >= 420:
            break
    return {"root_files": root_files(path), "files": files[:420], "important_files": important[:180], "generated_at": now_iso()}


def _plan_from_context(goal: str, source_context: dict | None) -> list[str]:
    terms = _goal_terms(goal)
    bullets = context_bullets(source_context or {})
    plan = ["Inspect the source-aware file summaries before drafting changes"]
    if bullets:
        plan.append("Confirm integration points: " + "; ".join(bullets[:3]))
    if _has_any(terms, ("auth", "admin", "password", "reset", "login", "credential")):
        plan.extend([
            "Trace the existing auth storage and password hashing helpers before adding reset logic",
            "Add the reset utility under scripts/ without creating a parallel authentication path",
            "Preserve existing auth configuration and only update the targeted admin credential",
        ])
    elif _has_any(terms, ("agentic", "coding", "scaffold", "artifact", "workspace")):
        plan.extend([
            "Update the Agentic Coding service/UI surface using the existing Odysseus API and modal patterns",
            "Keep the review-first approval gate before any execution or patch artifact",
        ])
    else:
        plan.append("Prepare a minimal patch against the highest-ranked integration files")
    plan.append("Generate review artifacts before execution")
    return plan


def _test_plan_from_goal(goal: str) -> list[str]:
    terms = _goal_terms(goal)
    plan = ["Run focused tests for the changed feature area"]
    if _has_any(terms, ("auth", "admin", "password", "reset", "login", "credential")):
        plan.extend([
            "Add tests for blank password rejection and successful admin credential update",
            "Run the reset command inside the Docker container against a temporary auth store",
            "Confirm login succeeds with the new password and existing auth configuration remains intact",
        ])
    elif _has_any(terms, ("agentic", "coding", "scaffold", "artifact", "workspace")):
        plan.extend([
            "Run Agentic Coding focused pytest coverage",
            "Verify the native Odysseus UX flow in the browser",
        ])
    return plan


def build_scaffold(goal: str, repo_map: dict, source_context: dict | None = None) -> dict:
    likely = rank_likely_files(goal, repo_map)
    return {
        "title": goal.strip()[:96] or "Agentic Coding scaffold",
        "likely_files": likely,
        "inspection_commands": ["Review likely files", "Review source context", "Confirm workspace scope", "Run focused tests"],
        "implementation_plan": _plan_from_context(goal, source_context),
        "test_plan": _test_plan_from_goal(goal),
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
        likely = rank_likely_files(user_goal, scan["repo_map"])
        source_context = summarize_likely_files(scan["workspace"]["canonical_path"], likely)
        scaffold = build_scaffold(user_goal, scan["repo_map"], source_context)
        metadata = {"source_context": source_context, "source_context_generated_at": now_iso()}
        return self.store.add_row("scaffolds", owner, session_id=session_id, workspace_id=workspace_id, endpoint_id=endpoint_id, model=model, status="draft", approved_at=None, user_goal=user_goal, repo_map=scan["repo_map"], metadata=metadata, **scaffold)

    def list_scaffolds(self, owner: str | None, workspace_id: str | None = None) -> list[dict]:
        return self.store.list_rows("scaffolds", owner, workspace_id=workspace_id)

    def approve_scaffold(self, owner: str | None, scaffold_id: str) -> dict:
        return self.store.update_row("scaffolds", scaffold_id, owner, status="approved", approved_at=now_iso())

    def reject_scaffold(self, owner: str | None, scaffold_id: str) -> dict:
        return self.store.update_row("scaffolds", scaffold_id, owner, status="rejected")
