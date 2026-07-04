"""Database-backed persistence hooks for Agentic Coding."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from core.database import engine
from src.agentic_coding.storage import new_row, now_iso


COLLECTION_TABLES = {
    "workspaces": "agentic_coding_workspaces",
    "scaffolds": "agentic_coding_scaffolds",
    "runs": "agentic_coding_runs",
    "steps": "agentic_coding_steps",
    "artifacts": "agentic_coding_artifacts",
    "benchmarks": "agentic_coding_benchmarks",
}

JSON_FIELDS = {
    "repo_map",
    "likely_files",
    "inspection_commands",
    "implementation_plan",
    "test_plan",
    "rollback_plan",
    "metadata",
    "metrics",
}


def table_for(collection: str) -> str:
    try:
        return COLLECTION_TABLES[collection]
    except KeyError as exc:
        raise KeyError(f"Unknown Agentic Coding collection: {collection}") from exc


def encode_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key in JSON_FIELDS:
            fallback = {} if key in {"metadata", "metrics", "repo_map"} else []
            out[key] = json.dumps(value if value is not None else fallback, ensure_ascii=False)
        elif isinstance(value, bool):
            out[key] = 1 if value else 0
        else:
            out[key] = value
    return out


def decode_row(row: dict[str, Any]) -> dict[str, Any]:
    for key, value in list(row.items()):
        if key in JSON_FIELDS and isinstance(value, str):
            try:
                row[key] = json.loads(value)
            except Exception:
                row[key] = {} if key in {"metadata", "metrics", "repo_map"} else []
    if "is_active" in row:
        row["is_active"] = bool(row["is_active"])
    return row
