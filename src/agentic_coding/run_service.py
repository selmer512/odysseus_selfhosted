"""Run record helpers for Agentic Coding."""

from __future__ import annotations

from .storage import AgenticCodingStore, now_iso
from .test_service import normalize_test_command


class AgenticCodingRunService:
    def __init__(self, store: AgenticCodingStore | None = None) -> None:
        self.store = store or AgenticCodingStore()

    def create_run(self, owner: str | None, scaffold_id: str, endpoint_id: str | None = None, model: str | None = None) -> dict:
        scaffold = self.store.get_row("scaffolds", scaffold_id, owner)
        if scaffold.get("status") != "approved":
            raise ValueError("Scaffold must be approved before creating a run")
        return self.store.add_row("runs", owner, session_id=scaffold.get("session_id"), workspace_id=scaffold["workspace_id"], scaffold_id=scaffold_id, endpoint_id=endpoint_id or scaffold.get("endpoint_id"), model=model or scaffold.get("model"), status="pending", approval_mode="explicit", summary=None, started_at=None, completed_at=None)

    async def prepare_artifacts(self, owner: str | None, run_id: str) -> dict:
        run = self.store.get_row("runs", run_id, owner)
        scaffold = self.store.get_row("scaffolds", run["scaffold_id"], owner)
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="repo_map", title="Repository map", content=str(scaffold.get("repo_map") or {}), metadata={})
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="commit_message", title="Commit message draft", content=f"Implement agentic coding workflow\n\nGoal: {scaffold.get('user_goal', '').strip()}", metadata={})
        return self.store.update_row("runs", run_id, owner, status="completed", started_at=now_iso(), completed_at=now_iso(), summary="Prepared review artifacts from the approved scaffold.")

    def record_test_command(self, owner: str | None, run_id: str, command: str | None) -> dict:
        payload = normalize_test_command(command)
        artifact = self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="test_plan", title="Test command review", content=str(payload), metadata=payload)
        return {"artifact": artifact, "test": payload}

    def list_artifacts(self, owner: str | None, run_id: str) -> list[dict]:
        return self.store.list_rows("artifacts", owner, run_id=run_id)
