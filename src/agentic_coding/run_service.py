"""Run record helpers for Agentic Coding."""

from __future__ import annotations

import json

from .storage import AgenticCodingStore, now_iso
from .test_service import normalize_test_command


def _md_list(title: str, values: list | None) -> str:
    items = values or []
    body = "\n".join(f"- {item}" for item in items) if items else "- No items recorded."
    return f"# {title}\n\n{body}\n"


def _json_content(value: dict | list | None) -> str:
    return json.dumps(value or {}, indent=2, ensure_ascii=False)


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
        goal = (scaffold.get("user_goal") or "").strip()
        metadata = scaffold.get("metadata") or {}
        source_context = metadata.get("source_context") or {}
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="repo_map", title="Repository map", content=_json_content(scaffold.get("repo_map") or {}), metadata={})
        if source_context:
            self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="source_context", title="Source context", content=_json_content(source_context), metadata={"file_count": source_context.get("count", 0)})
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="implementation_plan", title="Implementation plan", content=_md_list("Implementation plan", scaffold.get("implementation_plan")), metadata={})
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="test_plan", title="Test plan", content=_md_list("Test plan", scaffold.get("test_plan")), metadata={})
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="rollback_plan", title="Rollback plan", content=_md_list("Rollback plan", scaffold.get("rollback_plan")), metadata={})
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="commit_message", title="Commit message draft", content=f"Implement agentic coding workflow\n\nGoal: {goal}", metadata={})
        self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="pr_summary", title="Pull request summary draft", content=f"# Summary\n\n- Prepared an approved Agentic Coding run for: {goal}\n- Review likely files and source context before applying changes.\n- Run focused tests before merge.\n", metadata={})
        return self.store.update_row("runs", run_id, owner, status="completed", started_at=now_iso(), completed_at=now_iso(), summary="Prepared source-aware review artifacts from the approved scaffold.")

    def record_test_command(self, owner: str | None, run_id: str, command: str | None) -> dict:
        payload = normalize_test_command(command)
        artifact = self.store.add_row("artifacts", owner, run_id=run_id, artifact_type="test_plan", title="Test command review", content=str(payload), metadata=payload)
        return {"artifact": artifact, "test": payload}

    def list_artifacts(self, owner: str | None, run_id: str) -> list[dict]:
        return self.store.list_rows("artifacts", owner, run_id=run_id)
