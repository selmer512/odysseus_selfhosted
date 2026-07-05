import pytest

from src.agentic_coding.run_service import AgenticCodingRunService


@pytest.mark.asyncio
async def test_prepare_artifacts_creates_review_package():
    class Store:
        def __init__(self):
            self.rows = {
                "runs": [{"id": "run-1", "owner": "admin", "scaffold_id": "scaffold-1"}],
                "scaffolds": [{
                    "id": "scaffold-1",
                    "owner": "admin",
                    "user_goal": "Improve artifact output",
                    "repo_map": {"important_files": ["src/agentic_coding/run_service.py"]},
                    "implementation_plan": ["Inspect likely files"],
                    "test_plan": ["Run focused tests"],
                    "rollback_plan": ["Revert patch"],
                }],
                "artifacts": [],
            }

        def get_row(self, collection, row_id, owner=None):
            return next(row for row in self.rows[collection] if row["id"] == row_id)

        def add_row(self, collection, owner=None, **fields):
            row = {"id": f"{collection}-{len(self.rows[collection])}", "owner": owner, **fields}
            self.rows[collection].append(row)
            return row

        def update_row(self, collection, row_id, owner=None, **fields):
            row = self.get_row(collection, row_id, owner)
            row.update(fields)
            return row

    store = Store()
    service = AgenticCodingRunService(store)

    run = await service.prepare_artifacts("admin", "run-1")
    artifact_types = {row["artifact_type"] for row in store.rows["artifacts"]}

    assert run["status"] == "completed"
    assert {"repo_map", "implementation_plan", "test_plan", "rollback_plan", "commit_message", "pr_summary"}.issubset(artifact_types)
