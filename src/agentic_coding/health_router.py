"""Mounted API router for Agentic Coding."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.auth_helpers import require_user
from src.tool_security import owner_is_admin_or_single_user
from src.agentic_coding.model_profiles import coding_capabilities_from_endpoint, list_model_profiles
from src.agentic_coding.run_service import AgenticCodingRunService
from src.agentic_coding.scaffold_service import ScaffoldService
from src.agentic_coding.storage import AgenticCodingStore, now_iso
from src.agentic_coding.test_service import normalize_test_command


class WorkspaceCreate(BaseModel):
    path: str
    title: str | None = None


class WorkspacePatch(BaseModel):
    title: str | None = None
    is_active: bool | None = None


class ScaffoldCreate(BaseModel):
    workspace_id: str
    user_goal: str = Field(min_length=1)
    session_id: str | None = None
    endpoint_id: str | None = None
    model: str | None = None


class ScaffoldPatch(BaseModel):
    title: str | None = None
    user_goal: str | None = None
    status: str | None = None
    risk_notes: str | None = None


class RunCreate(BaseModel):
    scaffold_id: str
    endpoint_id: str | None = None
    model: str | None = None


class TestCommand(BaseModel):
    command: str | None = None


class BenchmarkCreate(BaseModel):
    workspace_id: str | None = None
    endpoint_id: str | None = None
    model: str | None = None
    task: str
    metrics: dict = Field(default_factory=dict)
    summary: str | None = None


class MemorySuggestion(BaseModel):
    title: str | None = None
    content: str
    tags: list[str] = Field(default_factory=list)


def _owner(request: Request) -> str:
    owner = require_user(request)
    if not owner_is_admin_or_single_user(owner):
        raise HTTPException(403, "Agentic Coding is admin-only")
    return owner


def _missing(exc: KeyError) -> HTTPException:
    return HTTPException(404, str(exc))


def _artifact_content(title: str, content: str) -> str:
    return f"# {title}\n\n{content.strip()}\n"


def make_router() -> APIRouter:
    router = APIRouter(prefix="/api/agentic-coding", tags=["agentic-coding"])
    store = AgenticCodingStore()
    scaffolds = ScaffoldService(store)
    runs = AgenticCodingRunService(store)

    @router.get("/health")
    def health(request: Request):
        _owner(request)
        return {"ok": True, "feature": "agentic-coding"}

    @router.get("/workspaces")
    def list_workspaces(request: Request):
        return {"workspaces": scaffolds.list_workspaces(_owner(request))}

    @router.post("/workspaces")
    def create_workspace(request: Request, body: WorkspaceCreate):
        try:
            return scaffolds.create_workspace(_owner(request), body.path, body.title)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.get("/workspaces/{workspace_id}")
    def get_workspace(request: Request, workspace_id: str):
        try:
            return store.get_row("workspaces", workspace_id, _owner(request))
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.patch("/workspaces/{workspace_id}")
    def patch_workspace(request: Request, workspace_id: str, body: WorkspacePatch):
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        try:
            return store.update_row("workspaces", workspace_id, _owner(request), **updates)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/workspaces/{workspace_id}/scan")
    def scan_workspace(request: Request, workspace_id: str):
        try:
            return scaffolds.scan_workspace(_owner(request), workspace_id)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/model-profiles")
    def model_profiles(request: Request):
        _owner(request)
        return {"profiles": list_model_profiles()}

    @router.get("/models")
    def coding_models(request: Request):
        owner = _owner(request)
        from core.database import ModelEndpoint, SessionLocal

        out = []
        db = SessionLocal()
        try:
            q = db.query(ModelEndpoint).filter(ModelEndpoint.is_enabled == True)  # noqa: E712
            if owner:
                q = q.filter((ModelEndpoint.owner == owner) | (ModelEndpoint.owner == None))  # noqa: E711
            for endpoint in q.all():
                capabilities = coding_capabilities_from_endpoint(endpoint)
                if not capabilities.get("coding"):
                    continue
                out.append({
                    "endpoint_id": endpoint.id,
                    "name": endpoint.name,
                    "base_url": endpoint.base_url,
                    "model_type": endpoint.model_type,
                    "supports_tools": endpoint.supports_tools,
                    "capabilities": capabilities,
                })
        finally:
            db.close()
        return {"models": out}

    @router.get("/models/{endpoint_id}/health")
    def model_health(request: Request, endpoint_id: str):
        owner = _owner(request)
        from core.database import ModelEndpoint, SessionLocal

        db = SessionLocal()
        try:
            q = db.query(ModelEndpoint).filter(ModelEndpoint.id == endpoint_id)
            if owner:
                q = q.filter((ModelEndpoint.owner == owner) | (ModelEndpoint.owner == None))  # noqa: E711
            endpoint = q.first()
            if not endpoint:
                raise HTTPException(404, "Model endpoint not found")
            return {"endpoint_id": endpoint.id, "enabled": bool(endpoint.is_enabled), "capabilities": coding_capabilities_from_endpoint(endpoint)}
        finally:
            db.close()

    @router.get("/scaffolds")
    def list_scaffolds(request: Request, workspace_id: str | None = None):
        return {"scaffolds": scaffolds.list_scaffolds(_owner(request), workspace_id)}

    @router.post("/scaffolds")
    async def create_scaffold(request: Request, body: ScaffoldCreate):
        try:
            return await scaffolds.generate_scaffold(_owner(request), body.workspace_id, body.user_goal, body.session_id, body.endpoint_id, body.model)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/scaffolds/{scaffold_id}")
    def get_scaffold(request: Request, scaffold_id: str):
        try:
            return store.get_row("scaffolds", scaffold_id, _owner(request))
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.patch("/scaffolds/{scaffold_id}")
    def patch_scaffold(request: Request, scaffold_id: str, body: ScaffoldPatch):
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        try:
            return store.update_row("scaffolds", scaffold_id, _owner(request), **updates)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/scaffolds/{scaffold_id}/approve")
    def approve_scaffold(request: Request, scaffold_id: str):
        try:
            return scaffolds.approve_scaffold(_owner(request), scaffold_id)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/scaffolds/{scaffold_id}/reject")
    def reject_scaffold(request: Request, scaffold_id: str):
        try:
            return scaffolds.reject_scaffold(_owner(request), scaffold_id)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/scaffolds/{scaffold_id}/rerun")
    async def rerun_scaffold(request: Request, scaffold_id: str):
        owner = _owner(request)
        try:
            scaffold = store.get_row("scaffolds", scaffold_id, owner)
            return await scaffolds.generate_scaffold(owner, scaffold["workspace_id"], scaffold["user_goal"], scaffold.get("session_id"), scaffold.get("endpoint_id"), scaffold.get("model"))
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/runs")
    def list_runs(request: Request, workspace_id: str | None = None, scaffold_id: str | None = None):
        return {"runs": store.list_rows("runs", _owner(request), workspace_id=workspace_id, scaffold_id=scaffold_id)}

    @router.post("/runs")
    def create_run(request: Request, body: RunCreate):
        try:
            return runs.create_run(_owner(request), body.scaffold_id, body.endpoint_id, body.model)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/runs/{run_id}")
    def get_run(request: Request, run_id: str):
        try:
            return store.get_row("runs", run_id, _owner(request))
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/runs/{run_id}/events")
    def run_events(request: Request, run_id: str):
        owner = _owner(request)
        return {"events": store.list_rows("steps", owner, run_id=run_id)}

    @router.post("/runs/{run_id}/execute")
    async def execute_run(request: Request, run_id: str):
        try:
            return await runs.prepare_artifacts(_owner(request), run_id)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/runs/{run_id}/cancel")
    def cancel_run(request: Request, run_id: str):
        try:
            return store.update_row("runs", run_id, _owner(request), status="cancelled", completed_at=now_iso())
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/runs/{run_id}/artifacts")
    def list_artifacts(request: Request, run_id: str):
        return {"artifacts": runs.list_artifacts(_owner(request), run_id)}

    @router.get("/artifacts/{artifact_id}")
    def get_artifact(request: Request, artifact_id: str):
        try:
            return store.get_row("artifacts", artifact_id, _owner(request))
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/runs/{run_id}/tests")
    def record_tests(request: Request, run_id: str, body: TestCommand):
        owner = _owner(request)
        try:
            store.get_row("runs", run_id, owner)
            payload = normalize_test_command(body.command)
            return store.add_row("artifacts", owner, run_id=run_id, artifact_type="test_log", title="Test command review", content=str(payload), metadata=payload)
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/runs/{run_id}/commit-summary")
    def commit_summary(request: Request, run_id: str):
        owner = _owner(request)
        try:
            run = store.get_row("runs", run_id, owner)
            scaffold = store.get_row("scaffolds", run["scaffold_id"], owner)
            content = f"Implement agentic coding workflow\n\nGoal: {scaffold.get('user_goal', '').strip()}"
            return store.add_row("artifacts", owner, run_id=run_id, artifact_type="commit_message", title="Commit message draft", content=content, metadata={})
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/runs/{run_id}/pr-summary")
    def pr_summary(request: Request, run_id: str):
        owner = _owner(request)
        try:
            run = store.get_row("runs", run_id, owner)
            scaffold = store.get_row("scaffolds", run["scaffold_id"], owner)
            content = _artifact_content("Agentic Coding PR Summary", "\n".join(scaffold.get("implementation_plan", [])))
            return store.add_row("artifacts", owner, run_id=run_id, artifact_type="pr_summary", title="Pull request summary draft", content=content, metadata={})
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.get("/benchmarks")
    def list_benchmarks(request: Request, workspace_id: str | None = None):
        return {"benchmarks": store.list_rows("benchmarks", _owner(request), workspace_id=workspace_id)}

    @router.post("/benchmarks")
    def create_benchmark(request: Request, body: BenchmarkCreate):
        owner = _owner(request)
        return store.add_row("benchmarks", owner, status="recorded", **body.model_dump())

    @router.get("/benchmarks/{benchmark_id}")
    def get_benchmark(request: Request, benchmark_id: str):
        try:
            return store.get_row("benchmarks", benchmark_id, _owner(request))
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/benchmarks/{benchmark_id}/cancel")
    def cancel_benchmark(request: Request, benchmark_id: str):
        try:
            return store.update_row("benchmarks", benchmark_id, _owner(request), status="cancelled")
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/runs/{run_id}/memory-suggestions")
    def memory_suggestions(request: Request, run_id: str):
        owner = _owner(request)
        try:
            run = store.get_row("runs", run_id, owner)
            scaffold = store.get_row("scaffolds", run["scaffold_id"], owner)
            return {"suggestions": [{"title": scaffold.get("title"), "content": scaffold.get("risk_notes") or scaffold.get("user_goal"), "tags": ["agentic-coding", "repo"]}]}
        except KeyError as exc:
            raise _missing(exc) from exc

    @router.post("/runs/{run_id}/save-memory")
    def save_memory_suggestion(request: Request, run_id: str, body: MemorySuggestion):
        owner = _owner(request)
        try:
            store.get_row("runs", run_id, owner)
            return store.add_row("artifacts", owner, run_id=run_id, artifact_type="memory_suggestion", title=body.title or "Repo memory suggestion", content=body.content, metadata={"tags": body.tags})
        except KeyError as exc:
            raise _missing(exc) from exc

    return router
