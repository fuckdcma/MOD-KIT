# Mod Studio AI v0.1 — Evidence data contract

This file describes the actual exported schema, not a trained model.

## `text_provenance.jsonl`

One JSON object per editor-observed field. Key fields:

- `record_id`: 24 hex chars, SHA256 of source kind + asset location + object path + component type + source key. Stable while a text value changes, but may change when object hierarchy changes.
- `source_kind`: `scene_tmp_serialized`, `prefab_tmp_serialized`, `scriptable_object_kv`, `resources_json_message`.
- `asset_path`, `asset_guid`, `asset_local_id` (may be empty), `object_path`, `component_type`, `source_key`.
- `text`, `text_sha256`.
- `prefab_source_path`, `prefab_text_difference`: helps distinguish source asset and instance overrides.
- `font_asset`, `material`, `shader`, `font_atlas`, `material_atlas`, `atlas_status` (`match`, `mismatch`, `unknown`).
- `evidence_kind`: always `unity_editor_static` in v0.1.
- `verification`: always `observed_not_validated` in v0.1. Do not change to `verified` merely because a string is visible.

No `training_label` or verified hook location is emitted by the collector.

## `model_input_rea_evidence.jsonl`

One record per REA method containing a literal and/or calling `TMPro.TMP_Text.set_text`. Includes method token, method CIL SHA256, referenced literals and call targets, and assembly SHA256. No Unity project source, ground-truth labels, or asset values are injected.

CIL method tokens are **build-local**, not stable addresses. Only interpret them with matching SHA256/MVID.

## Evaluation split

- `PRIVATE_ground_truth_review.csv` is an evaluator artifact only. It checks matching candidates, not a standalone AI performance measure.
- A genuine blind evaluation should hide editor reference data, Unity source project and ground truth from the model, and provide only compiled game binary and permitted research tools.
- Do not split variants from one Unity project across train/test if the task is to generalize across unseen games.
