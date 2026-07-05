import pytest

from src.agentic_coding.patch_service import apply_operations, build_patch_proposal
from src.agentic_coding.run_service import AgenticCodingRunService
from src.agentic_coding.storage import now_iso


class MemoryStore:
    def __init__(self, workspace):
        self.rows = {
            "workspaces": [{"id": "workspace-1", "owner": "admin", "canonical_path": str(workspace), "path": str(workspace)}],
            "scaffolds": [{
                "id": "scaffold-1",
                "owner": "admin",
                "workspace_id": "workspace-1",
                "status": "approved",
                "session_id": None,
                "endpoint_id": None,
                "model": None,
                "user_goal": "Add admin reset utility script",
                "repo_map": {},
                "metadata": {},
                "implementation_plan": [],
                "test_plan": [],
                "rollback_plan": [],
            }],
            "runs": [{"id": "run-1", "owner": "admin", "workspace_id": "workspace-1", "scaffold_id": "scaffold-1"}],
            "artifacts": [],
        }

    def list_rows(self, collection, owner=None, **filters):
        rows = list(self.rows.get(collection, []))
        for key, value in filters.items():
            rows = [row for row in rows if row.get(key) == value]
        return rows

    def get_row(self, collection, row_id, owner=None):
        for row in self.rows[collection]:
            if row["id"] == row_id:
                return row
        raise KeyError(row_id)

    def add_row(self, collection, owner=None, **fields):
        row = {"id": f"{collection}-{len(self.rows[collection])}", "owner": owner, "created_at": now_iso(), "updated_at": now_iso(), **fields}
        self.rows[collection].append(row)
        return row

    def update_row(self, collection, row_id, owner=None, **fields):
        row = self.get_row(collection, row_id, owner)
        row.update(fields)
        row["updated_at"] = now_iso()
        return row


def test_patch_proposal_for_admin_reset_is_applicable():
    proposal = build_patch_proposal({"user_goal": "Add admin reset utility script"})

    assert proposal["metadata"]["can_apply"] is True
    assert proposal["metadata"]["operation_count"] == 3
    assert "scripts/reset-admin-password.py" in proposal["content"]
    assert "tests/test_reset_admin_password_script.py" in proposal["content"]


def test_patch_apply_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        apply_operations(str(tmp_path), [{"action": "create_or_replace", "path": "../outside.py", "content": "x"}])


def test_patch_workflow_requires_approval_before_apply(tmp_path):
    store = MemoryStore(tmp_path)
    service = AgenticCodingRunService(store)

    proposal = service.generate_patch_proposal("admin", "run-1")
    assert proposal["artifact_type"] == "patch_proposal"
    assert proposal["metadata"]["approved"] is False

    with pytest.raises(ValueError):
        service.apply_patch("admin", "run-1")

    approved = service.approve_patch("admin", "run-1")
    assert approved["metadata"]["approved"] is True

    result = service.apply_patch("admin", "run-1")
    changed = {row["path"] for row in result["result"]["changed"]}

    assert "scripts/reset-admin-password.py" in changed
    assert "tests/test_reset_admin_password_script.py" in changed
    assert "docs/admin-password-reset.md" in changed
    assert result["artifact"]["artifact_type"] == "patch_apply"
