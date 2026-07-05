import json
import time
import uuid

import pytest

from src.agentic_coding.run_service import AgenticCodingRunService
from src.agentic_coding.scaffold_service import ScaffoldService
from src.agentic_coding.storage import now_iso


class MemoryStore:
    def __init__(self):
        self.rows = {
            "workspaces": [],
            "scaffolds": [],
            "runs": [],
            "artifacts": [],
        }

    def list_rows(self, collection, owner=None, **filters):
        rows = list(self.rows.get(collection, []))
        if owner is not None:
            rows = [row for row in rows if row.get("owner") in (owner, None, "")]
        for key, value in filters.items():
            rows = [row for row in rows if row.get(key) == value]
        return rows

    def get_row(self, collection, row_id, owner=None):
        for row in self.list_rows(collection, owner):
            if row.get("id") == row_id:
                return row
        raise KeyError(row_id)

    def add_row(self, collection, owner=None, **fields):
        row = {
            "id": str(uuid.uuid4()),
            "owner": owner,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            **fields,
        }
        self.rows[collection].append(row)
        return row

    def update_row(self, collection, row_id, owner=None, **fields):
        row = self.get_row(collection, row_id, owner)
        row.update(fields)
        row["updated_at"] = now_iso()
        return row


@pytest.mark.asyncio
async def test_agentic_coding_measurable_lifecycle(tmp_path):
    (tmp_path / "src" / "agentic_coding").mkdir(parents=True)
    (tmp_path / "companion").mkdir()
    (tmp_path / "static").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "agentic_coding" / "run_service.py").write_text("# run", encoding="utf-8")
    (tmp_path / "src" / "agentic_coding" / "scaffold_service.py").write_text("# scaffold", encoding="utf-8")
    (tmp_path / "companion" / "agentic_coding_ui.py").write_text("# ui", encoding="utf-8")
    (tmp_path / "static" / "agentic-coding.js").write_text("// js", encoding="utf-8")
    (tmp_path / "tests" / "test_agentic_coding_artifacts.py").write_text("# tests", encoding="utf-8")

    store = MemoryStore()
    scaffolds = ScaffoldService(store)
    runs = AgenticCodingRunService(store)
    goal = "Improve Agentic Coding artifact output and workspace registration UX"

    started = time.perf_counter()
    workspace = scaffolds.create_workspace("admin", str(tmp_path), "Fixture repo")
    scaffold = await scaffolds.generate_scaffold("admin", workspace["id"], goal, model="generic-coding-tools")
    approved = scaffolds.approve_scaffold("admin", scaffold["id"])
    run = runs.create_run("admin", approved["id"])
    completed = await runs.prepare_artifacts("admin", run["id"])
    artifacts = runs.list_artifacts("admin", run["id"])
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    metrics = {
        "status": completed["status"],
        "artifact_count": len(artifacts),
        "artifact_types": sorted({artifact["artifact_type"] for artifact in artifacts}),
        "elapsed_ms": elapsed_ms,
        "likely_files": scaffold["likely_files"][:6],
    }
    print("AGENTIC_CODING_METRICS " + json.dumps(metrics, sort_keys=True))

    assert metrics["status"] == "completed"
    assert metrics["artifact_count"] >= 6
    assert {"repo_map", "implementation_plan", "test_plan", "rollback_plan", "commit_message", "pr_summary"}.issubset(metrics["artifact_types"])
    assert any(path.startswith("src/agentic_coding/") for path in metrics["likely_files"])
    assert "companion/agentic_coding_ui.py" in metrics["likely_files"]
