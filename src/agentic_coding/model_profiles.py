"""Built-in Agentic Coding model profile registry."""

from __future__ import annotations

AGENTIC_CODING_MODEL_PROFILES = [
    {
        "id": "generic-coding-tools",
        "label": "Generic coding + tools",
        "provider_family": "openai-compatible",
        "capabilities": {
            "coding": True,
            "agentic_coding": True,
            "tool_calling": True,
            "repo_reasoning": True,
            "patch_generation": True,
            "supports_speculative_decoding": False,
        },
        "notes": "Use for local or API endpoints that can follow repo-aware coding instructions and call tools.",
    },
    {
        "id": "ornith-coding",
        "label": "Ornith coding profile",
        "provider_family": "ornith",
        "capabilities": {
            "coding": True,
            "agentic_coding": True,
            "tool_calling": True,
            "repo_reasoning": True,
            "patch_generation": True,
            "supports_speculative_decoding": False,
        },
        "notes": "Profile placeholder for Ornith-family coding models and Cookbook presets.",
    },
]


def list_model_profiles() -> list[dict]:
    return [dict(profile) for profile in AGENTIC_CODING_MODEL_PROFILES]


def coding_capabilities_from_endpoint(endpoint) -> dict:
    """Infer coding capability metadata from an existing ModelEndpoint row."""
    import json

    raw = getattr(endpoint, "capabilities_json", None)
    capabilities = {
        "coding": False,
        "agentic_coding": False,
        "tool_calling": bool(getattr(endpoint, "supports_tools", False)),
        "repo_reasoning": False,
        "patch_generation": False,
        "supports_speculative_decoding": False,
    }
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                capabilities.update(parsed)
        except Exception:
            pass
    profile_id = getattr(endpoint, "coding_profile_id", None) or getattr(endpoint, "profile_id", None)
    if profile_id:
        capabilities["coding"] = True
        capabilities["agentic_coding"] = True
    name = f"{getattr(endpoint, 'name', '')} {getattr(endpoint, 'cached_models', '')}".lower()
    if any(token in name for token in ("coder", "coding", "code", "ornith", "deepseek")):
        capabilities["coding"] = True
        capabilities["repo_reasoning"] = True
        capabilities["patch_generation"] = True
    return capabilities
