# Progress ledger — 2026-11-02

## Milestone 01 — UnityTextLab / Mono / REA — VERIFIED LAB BASELINE

- Unity 6000.3.27f2 Windows Mono; build UnityTextLab.exe.
- 5 text displayed: New Game, Load Game, Quest Completed, Health dynamic, Hello Commander.
- REA static inspection exports `assembly_identity.json` + `members.json`. 9 type defs (including Module), 16 methods, 14 fields; Assembly SHA256: `ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e`.
- Player.log: `sameAtlas=True` on `Prefab_NewGame`, LiberationSans SDF; warnings GPU resource cleanup. Glyph Vietnamese not tested.

## Milestone 02 — Editor provenance — VERIFIED OUTPUT

- Collector scanned Unity source Editor: 5 scene TMP + 1 prefab TMP + 1 ScriptableObject + 1 Resources JSON = 8 records.
- Cross-check 5 cases; reference data must never be provided to blind agent.
- No collector warnings; data exported to `text_provenance.jsonl`, `manifest.json`.

## Milestone 03 — Build-only scanner — IN PROGRESS

- v0.1 rule baseline 1 exact + 1 template + 3 unknown.
- UnityPy 1.25.4 installation blocked initially by Python 3.15 C++ compile, fixed with Python 3.12.10 venv. `tpk_ar` needs sdist install before the `--only-binary` dependency restriction. Windows ExecutionPolicy requires per-process Bypass or `powershell -ExecutionPolicy Bypass -File`.
- UnityPy v0.1: first read TextAsset, failed 32 MonoBehaviour decode.
- v0.2 + TypeTreeGeneratorAPI: **32/32 MB decoded, 0 errors, 7 asset observations**, 6/6 build files; latest files in `evidence/m03/latest/`.
- Current evaluator: **2/5 exact, 1/5 template, 2/5 unproven**. No Qwen inference score yet.

## Not yet done

- T001 serialized prefab origin from build (only scene TMP snapshot).
- T002 ScriptableObject key + reader method verified end-to-end (class + value observed but proof chain incomplete).
- Qwen GGUF download/load test; agent tool use eval.
- SDF broken-cases lab, font 1:1 runtime mapping validation.
- Standalone mod bootstrap, hook adapter compiler/test, IL2CPP/Unreal.


## M03 v0.3 — provenance linker (code completed, runtime pending)

- Source/installer packaged; **22/22 Python unit tests passed**.
- New table key/value pairing, reader metadata and build-only provenance output. Validity guard rejects unknown TMP snapshot and ScriptableObject missing entry key.
- **No Windows v0.3 build scan yet**; v0.2 user upload still 2 exact + 1 template + 2 unknown.
- Next: install patch on Windows, run scanner and evaluate; then develop one-to-one binding validation and start Qwen baseline if stable.


## M03 v0.3 — verified Windows results (2026-11-02)

- Real UnityTextLab build scan: 6/6 files; all 32 MonoBehaviour and 5 TextAsset decoded; 0 warnings/errors.
- Proof of paired `menu.load → Load Game` in ScriptableObject; T002 exact source+text now accepted by evaluator, but reader PPtr still unresolved.
- Evaluation: **3 exact + 1 dynamic template + 1 unproven (T001)**, not a Qwen result.
- Independent offline reproduction matches user's `baseline_static.json`, `provenance_links.json`, `evaluation_private.json`.
- Next engineering task: external-reference table resolver to bind `level0 (FileID=3, PathID=16)` to correct sharedassets0 target; don't infer prefab source from TMP `m_text`.


## M03 v0.4 — cross-file pointer resolver code & tests (2026-11-02)

- 12 unit tests mới, tổng 34/34 đạt; có false-positive guards và mock external UnityPy.
- v0.4 scanner mới sẽ cố xác nhận reader `level0#path_id=40` PPtr fileID3/pathID16 tới `sharedassets0.assets#path_id=16` qua external file table, không suy luận từ tên string hay PathID.
- Chưa chạy v0.4 scanner thực tế trên máy Windows. Replay dữ liệu v0.3 không tự nâng pointer; evaluator vẫn 3 exact + 1 template + 1 unknown.
- T001 còn thiếu prefab-origin proof; Qwen local chưa kiểm thử.


## M03 v0.4 — Verified real Windows output (2026-11-02)

- Real Unity 6000.3.27f2 Mono test build: 6/6 files, 32/32 MB decoded, 5/5 TextAsset decoded, 7 assets, 0 scan errors.
- One reader binding `level0#path_id=40` mapped via `level0.externals[2]` to `sharedassets0.assets#path_id=16` and LabStringTable `menu.load` entry; `serialized_pointer_resolved` verified from scanner JSON.
- v0.4 Python 34/34 tests, 3/3 report semantic reproduction. Counts: 3 exact + 1 template + 1 unproven; T001 prefab origin remains unknown. Qwen baseline not run.
- Archived exact RAR + four JSON + SHA-256 manifest and QA report in repository.
- Next: local Qwen baseline; no claims of runtime behavior or fully recovered prefab path.
