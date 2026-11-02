# Milestone 03 v0.4 — Pointer Resolver engineering report

**Status:** code and synthetic unit tests completed; **Unity 6000.3.27f2 Windows scan not yet run with v0.4**.

## Motivation

The user's v0.3 Windows scan verified T002 source table `menu.load → Load Game` in `sharedassets0.assets#path_id=16`, but did not link `level0#path_id=40` reader pointer `m_FileID=3,m_PathID=16` to that object.

## Implementation

The resolver reads UnityPy `obj.assets_file.externals` and applies Unity's 1-based external file index (`m_FileID-1`), with special case `m_FileID=0` for same serialized file. A resolved relationship requires an unambiguous target file in the scanned build; exact target PathID, ScriptableObject MonoScript class and matching key. It does NOT assign paths from Unity Editor and does NOT promote `TMP_Text.m_text` to prefab proof.

The new code records pointer evidence explicitly and differentiates serialized configuration from runtime behavior. If external metadata is absent, pointer resolution remains unproven.

## QA

- New tests: 12, including malicious/wrong key, file, PathID, ambiguously duplicated basename, out-of-range fileID, wrong source, and fake UnityPy API-level integration.
- Existing tests from v0.3: 22.
- Total: 34/34 pass.
- Local replay of v0.3 JSON must keep `3 exact + 1 template + 1 not-proven` as v0.3 source data has no external table metadata; new scan required for a stronger pointer claim.

## Next

Deploy patch to Windows and export new `build_assets.json`, `provenance_links.json`, `evaluation_private.json`. Only then mark the pointer resolved if build evidence supports it. T001 prefab origin remains an open research problem, then move toward Qwen base agent evaluation.
