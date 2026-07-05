from companion.agentic_coding_ui import _PAGE, make_agentic_coding_ui_router


def test_agentic_coding_ui_route_exists():
    router = make_agentic_coding_ui_router()
    assert "/agentic-coding" in {route.path for route in router.routes}


def test_agentic_coding_ui_loads_static_assets_and_controls():
    assert "/static/agentic-coding.css" in _PAGE
    assert "/static/agentic-coding.js" in _PAGE
    assert "register-workspace-button" in _PAGE
    assert "generate-scaffold-button" in _PAGE
    assert "create-run-button" in _PAGE
    assert "prepare-artifacts-button" in _PAGE


def test_agentic_coding_ui_avoids_inline_event_handlers():
    assert "onclick=" not in _PAGE
