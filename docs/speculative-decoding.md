# Speculative Decoding in Odysseus

Speculative decoding is a model-serving optimization. A smaller draft model proposes tokens and a larger target model verifies them.

## Where it fits

- Cookbook model serving presets can expose whether a backend supports it.
- Model endpoint metadata can advertise performance capabilities separately from coding-task capabilities.
- Agentic Coding can record the selected endpoint and model in run metadata, but should not assume this feature is available.

## Suggested metadata

- `supports_speculative_decoding`: boolean or null when unknown.
- `draft_model`: optional draft model id.
- `target_model`: optional target model id.
- `decode_backend`: vLLM, llama.cpp, Ollama, OpenAI-compatible proxy, or unknown.

## Safety notes

Speculative decoding changes speed and cost characteristics, not authorization. Agentic Coding approval gates, workspace confinement, untrusted-context wrapping, and artifact logging should behave the same whether speculative decoding is enabled or disabled.
