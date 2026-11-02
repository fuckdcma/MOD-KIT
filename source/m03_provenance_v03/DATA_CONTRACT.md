# Mod Studio AI M03 v0.3 — Data contract

Schema: `modstudio.m03.v0.3`.

## build_assets.json

`assets[]` unchanged basic shape: `{text, source_type, source_ref, asset_type, evidence_type, metadata}`.

- For `ModStudioLab.LabStringTable` entry where `entries[N].key` and `.value` are available from same decoded MonoBehaviour, `source_type="scriptable_object"`, `metadata.entry_key`, `metadata.key_field_path` and `metadata.field_path="entries[N].value"`.
- No paired key / wrong class: keep `source_type="unknown"`, even if `text=Load Game`.
- TMP `m_text` remains `source_type="unknown"`, not `serialized_prefab`.
- `reader_bindings[]`: `{source_ref, reader_class, reader_key, table_pointer, binding_status}`. PPtr linkage **not** established by matching numeric path ID alone across files.

## provenance_links.json

`observations[].source_status` is one of `source_value_observed`, `source_key_value_observed`, `ui_snapshot_only`, `unproven`. `runtime_binding` separately indicates evidence/limits of reader relation. References are build asset refs and method tokens; **never** source-project paths extracted from private ground truth.

## Evaluation

`baseline_static.json` uses `asset_text` validation only when source metadata matches actual scanned asset. A `scriptable_object` claim without class + paired key + field is rejected. `evaluation_private.json` still uses separate test-only CSV and is NOT passed to the model. Source+text score is **not** full runtime dataflow or hook success.
