# Release notes — M04 Evidence-Grounded v1.0 EXPERIMENTAL

- Deterministic catalog of exact REA ldstr + method setter evidence and qualified serialized TextAssets using frozen M03 v0.8 validator.
- All source claims are reconstructed from catalog IDs. Qwen can choose among IDs; it cannot fabricate source strings, method names or evidence fields in `observations`.
- Strict local Ollama-only requests; `num_ctx=8192`, `num_predict=512`, bounded batch of 10; fail closed on invalid or cut JSON.
- Separate Windows runner preflights SHA-256 hashes and refuses to overwrite old runs.
- Offline synthetic tests: 24 PASS. Live UnityTextLab-B/Ollama run: NOT PERFORMED by the authoring environment.
- Explicitly **not** a generalized prefab or M04 ScriptableObject pointer resolver, **not** a proof of runtime UI dataflow, **not** a replacement for M03 v0.8 benchmarks.
