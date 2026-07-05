from companion.agentic_coding_ui import _PAGE, make_agentic_coding_ui_router
from src.app_helpers import inject_native_odysseus_modules


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


def test_agentic_coding_native_module_injected_into_main_shell():
    html = "<html><body><main>Odysseus</main></body></html>"
    injected = inject_native_odysseus_modules(html, "/app/static/index.html")

    assert "/static/js/agenticCoding.js" in injected
    assert injected.count("agenticCoding.js") == 1


def test_agentic_coding_native_module_not_injected_into_login_shell():
    html = "<html><body>Login</body></html>"
    assert inject_native_odysseus_modules(html, "/app/static/login.html") == html


def test_agentic_coding_native_module_targets_visible_sidebar():
    script = open("static/js/agenticCoding.js", "r", encoding="utf-8").read()

    assert "tool-agentic-coding-btn" in script
    assert "ensureSidebarButton" in script
    assert "#sidebar .list-item" in script


def test_agentic_coding_native_module_uses_managed_tool_window():
    script = open("static/js/agenticCoding.js", "r", encoding="utf-8").read()
    css = open("static/agentic-coding-native.css", "r", encoding="utf-8").read()

    assert "from './modalManager.js'" in script
    assert "from './windowDrag.js'" in script
    assert "Modals.register" in script
    assert "Modals.injectMinimizeButton" in script
    assert "makeWindowDraggable" in script
    assert "agentic-coding-window" in css
    assert "resizeStorageKey" in script


def test_agentic_coding_native_module_exposes_patch_controls():
    script = open("static/js/agenticCoding.js", "r", encoding="utf-8").read()

    assert "agentic-native-patch" in script
    assert "agentic-native-approve-patch" in script
    assert "agentic-native-apply-patch" in script
    assert "/patch-proposal" in script
    assert "/approve-patch" in script
    assert "/apply-patch" in script
