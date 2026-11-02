# M03 v0.4 — Cross-file Pointer Resolution Contract

- `schema`: `modstudio.m03.v0.4`.
- `build_assets.json.reader_bindings[*]` includes `pointer_file_lookup` derived only from per-object `obj.assets_file.externals` (plus local m_FileID=0) and `m_FileID / m_PathID`.
- `pointer_file_lookup.status`: `file_mapped` or `not_resolved`.
- `binding_status`: `serialized_pointer_resolved` only if unique scanned file basename, matching file PathID, `ModStudioLab.LabStringTable` type identity and paired entry key. Otherwise `unresolved_build_pointer`.
- `resolved_target_ref`: only when `binding_status=serialized_pointer_resolved`.
- `resolution_evidence`: reader ref, source serialized file, m_FileID/m_PathID, external table index and path, exact build target ref, class/key check. No Editor GUID or original prefab path is fabricated.
- `provenance_links.json`: `source_key_value_observed` still means source key/value proven, not runtime execution. When a direct pointer is proven, `runtime_binding` is `serialized_pointer_and_lookup_flow_proven_runtime_unverified` when REA method flow also confirmed.
- `evaluation_private.json`: unchanged evaluation semantics (exact source+text, template, unknown), and should not change score for T001 or T002 merely because PPtr now resolves.
- **Do not feed** `PrivateEvaluation/` or Editor source/project data into Qwen build-only agent.
