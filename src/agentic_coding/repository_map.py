"""Repository map helpers."""

from pathlib import Path


def root_files(workspace: str) -> list[str]:
    base = Path(workspace)
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_file())[:40]
