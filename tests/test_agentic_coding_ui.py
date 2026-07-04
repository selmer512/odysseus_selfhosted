from companion.agentic_coding_ui import make_agentic_coding_ui_router


def test_agentic_coding_ui_route_exists():
    router = make_agentic_coding_ui_router()
    assert "/agentic-coding" in {route.path for route in router.routes}
