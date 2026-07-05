from src.agentic_coding.health_router import make_router


def test_agentic_coding_router_exposes_planned_route_groups():
    router = make_router()
    paths = {route.path for route in router.routes}

    assert "/api/agentic-coding/health" in paths
    assert "/api/agentic-coding/workspaces" in paths
    assert "/api/agentic-coding/model-profiles" in paths
    assert "/api/agentic-coding/models" in paths
    assert "/api/agentic-coding/scaffolds" in paths
    assert "/api/agentic-coding/runs" in paths
    assert "/api/agentic-coding/benchmarks" in paths


def test_agentic_coding_router_has_execute_and_artifact_routes():
    router = make_router()
    paths = {route.path for route in router.routes}

    assert "/api/agentic-coding/runs/{run_id}/execute" in paths
    assert "/api/agentic-coding/runs/{run_id}/artifacts" in paths
    assert "/api/agentic-coding/artifacts/{artifact_id}" in paths


def test_agentic_coding_router_has_patch_workflow_routes():
    router = make_router()
    paths = {route.path for route in router.routes}

    assert "/api/agentic-coding/runs/{run_id}/patch-proposal" in paths
    assert "/api/agentic-coding/runs/{run_id}/approve-patch" in paths
    assert "/api/agentic-coding/runs/{run_id}/apply-patch" in paths
