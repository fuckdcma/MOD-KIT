# Semantic Validation Contract — M03 v0.8

- `evidence_type=il_literal` must match an exact literal in a specific REA method. It cannot establish `external_json`, `scriptable_object`, `serialized_prefab` or `serialized_scene` source type by itself.
- To mark `hardcoded_managed` `observed` at method level: exact literal + `TMPro.TMP_Text.set_text` call, literal not flagged diagnostic; if placeholder format and `System.String.Format` coexist, classify assertion as `candidate_only` instead of hardcoded. This is *not* IL stack-to-setter proof.
- To mark `runtime_generated` template `observed` at method level: exact literal carrying `{N}`/`{N:spec}` + `System.String.Format` + TMP setter. Runtime rendered values are NOT inferred.
- If caller proposes wrong category, validator flags `candidate_only` and never silently rewrites `source_type`, so model scoring remains faithful.
- ScriptableObject and TextAsset `asset_text` evidence must come from build reader and pass existing proof checks. TMP scene `m_text` does not prove prefab origin.
- `evaluation` score still requires `validation_status=observed` and matching source category; `candidate_only`/`rejected` never contribute. Public ground truth is only used after agent generation.
- Model prompt contains source-type definitions and evidence, not ground truth, expected text list or Editor export.
