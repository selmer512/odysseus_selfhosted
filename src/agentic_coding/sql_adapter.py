"""SQL storage adapter for Agentic Coding."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import and_, insert, select, update

from core.database import engine
from src.agentic_coding.storage import new_row, now_iso, visible
from src.agentic_coding.sql_storage import metadata as core_metadata, workspaces_table, scaffolds_table
from src.agentic_coding.sql_runs import metadata as run_metadata, runs_table
from src.agentic_coding.sql_outputs import metadata as output_metadata, outputs_table
from src.agentic_coding.sql_metrics import metadata as metric_metadata, metrics_table
from src.agentic_coding.sql_events import metadata as event_metadata, events_table


TABLES = {
    "workspaces": workspaces_table,
    "scaffolds": scaffolds_table,
    "runs": runs_table,
    "steps": events_table,
    "artifacts": outputs_table,
    "benchmarks": metrics_table,
}

JSON_FIELDS = {"repo_map", "likely_files", "inspection_commands", "implementation_plan", "test_plan", "rollback_plan", "metadata", "metrics"}


def _table(collection: str):
    return TABLES[collection]


def _db_key(key: str) -> str:
    if key == "metadata":
        return "metadata_json"
    return key


def _encode(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        out[_db_key(key)] = json.dumps(value, ensure_ascii=False) if key in JSON_FIELDS else value
    return out


class AgenticCodingSqlStore:
    def __init__(self) -> None:
        self.ensure_schema()

    def ensure_schema(self) -> None:
        for meta in (core_metadata, run_metadata, output_metadata, metric_metadata, event_metadata):
            meta.create_all(engine, checkfirst=True)
