from types import SimpleNamespace

from src.agentic_coding.model_profiles import coding_capabilities_from_endpoint, list_model_profiles


def test_builtin_agentic_coding_profiles_are_advertised():
    profiles = list_model_profiles()
    assert any(profile["capabilities"].get("agentic_coding") for profile in profiles)


def test_coding_capabilities_detect_code_named_endpoint():
    endpoint = SimpleNamespace(name="Local Coder", cached_models='["qwen-coder"]', supports_tools=True)
    caps = coding_capabilities_from_endpoint(endpoint)
    assert caps["coding"] is True
    assert caps["repo_reasoning"] is True
    assert caps["tool_calling"] is True
