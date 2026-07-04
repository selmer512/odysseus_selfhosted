from companion.agentic_coding_ui import _PAGE, make_agentic_coding_ui_router


def test_agentic_coding_ui_route_exists():
    router = make_agentic_coding_ui_router()
    assert "/agentic-coding" in {route.path for route in router.routes}


def test_agentic_coding_ui_loads_static_assets_and_controls():
    assert "/static/agentic-coding.css" in _PAGE
    assert "/static/agentic-coding.js" in _PAGE
    assert "agenticCreateWorkspace" in _PAGE
    assert "agenticCreateScaffold" in _PAGE
    assert "agenticCreateRun" in _PAGE
    assert "agenticExecuteRun" in _PAGE
