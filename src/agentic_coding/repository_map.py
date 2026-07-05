"""Repository map helpers."""

from __future__ import annotations

from pathlib import Path


IMPORTANT_DIRS = ("core", "src", "routes", "scripts", "tests", "docs", "companion", ".github", "static")
IMPORTANT_FILES = ("README.md", "ROADMAP.md", "app.py", "requirements.txt", "pyproject.toml", "Dockerfile", "docker-compose.yml")


def root_files(workspace: str) -> list[str]:
    base = Path(workspace)
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_file())[:40]


def ordered_walk_roots(workspace: str) -> list[Path]:
    base = Path(workspace)
    roots: list[Path] = []
    for rel in IMPORTANT_DIRS:
        path = base / rel
        if path.exists() and path.is_dir():
            roots.append(path)
    roots.append(base)
    return roots


def is_important_file(rel: str) -> bool:
    return rel in IMPORTANT_FILES or rel.startswith(tuple(prefix + "/" for prefix in IMPORTANT_DIRS))
