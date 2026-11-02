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


## M03 Ollama Qwen first integration attempt (2026-11-02)

- `qwen3.5:4b` loaded in Ollama on RX 6700 XT, 100% GPU, 3.1GB; API was reachable for one successful tool-call.
- First Qwen run: step1 search_literals(text) returned 2 results; step2 malformed/empty JSON => aborted. `completed=false`. Do not treat 0/5 eval as an AI accuracy number.
- v0.5 native Ollama JSON mode + thinking off + retries + incomplete-eval guard + 4500-character tool-result bound: **51/51 local tests passed**, no live Windows test yet.
- Next run v0.5 with existing REA + build_assets (do not rescan) and upload fresh qwen_agent/evaluation files.


## Qwen Agent v0.5 completed; v0.6 guided built (2026-11-02)

- v0.5 Ollama native: Windows 51/51 tests, `completed:true`, 3 steps, two IL observations; evaluator 1 exact (T003), 0 template, 4 not proven. Model prematurely ended tool exploration; diagnostic log literal wrongly considered observed by previous validator.
- v0.6 guided evidence brief (REA + build assets), separated autonomous strategy, diagnostic `candidate_only`: 66/66 Python tests local (51 old +15 new). Replay old Agent 1/5 and static baseline 3 exact + 1 template unchanged. **No new live Qwen run yet**.
- Need new `qwen_agent_guided.json` and `evaluation_private_guided.json`, followed by separate holdout to assess generalization.


## M03 Guided v0.6 real run failed at HTTP client timeout; v0.7 fix (2026-11-02)

- v0.6 66/66 Windows unit tests passed, but Ollama guided 1st request exceeded 180s; trace has `completed:false` and no observations. Avoid treating this as zero correct.
- v0.7 code patch introduces `-Mode probe`, `-TimeoutSeconds`, `-NumPredict`, `-BriefChars`; default 600s/1280/3900, `num_ctx=4096`. 14 new + 66 old tests = **80/80 offline passed**; baseline counts unchanged 3/1/1.
- Next: run v0.7 probe and guided on user's Windows Ollama; no claim of GPU inference performance or success yet.


## M03 Guided v0.7 verified, Semantic Validation v0.8 built (2026-11-02)

- User installed v0.7, Windows 80/80 unit tests, native Ollama probe 5.56s. Qwen Guided `completed=true`, 8 observations, one invalid_json retry then finish.
- Guided Qwen score = **3 exact + 0 format template + 2 unproven** (T004 source-type wrong, T001 unknown). v0.4 tool baseline = 3 exact + 1 format template + 1 unknown. Autonomous v0.5 = 1 exact.
- Validator v0.7 classed Health template as `observed` with `hardcoded_managed` despite `String.Format` call; v0.8 marks that assertion `candidate_only`, no auto-correction.
- v0.8 source/tests/installer packaged and **96/96 local tests passed**; CLI score feedback improved; live Qwen retest pending. Need private game holdout later.


## M03 v0.8 — measured Guided Qwen baseline reached (2026-11-02)

- User Windows 96/96 tests; Qwen Guided v0.8 completed true with four observations, `Health: {0}/100` corrected to `runtime_generated`, no diagnostics exposed as UI observations.
- Qwen Guided now matches static tool baseline: **3 exact +1 template +1 unproven (T001 prefab origin)**. Independent evaluator reproduction matches submitted JSON report. This establishes a successful *functional regression on UnityTextLab A* only, not generalization or runtime hooking.
- Prior guided v0.7 =3 exact +0 template +2 unknown; autonomous v0.5 =1 exact. Never mix strategy scores.
- Next prioritize private holdout UnityTextLab-B; avoid leaking game/seed/ground truth via public repo. Review [protocol](M04_UNSEEN_HOLDOUT_PROTOCOL.md).


## Milestone 04 v0.1 — generator implemented, Windows validation pending

- 20-case cryptographically fresh local holdout generator (15 positives, 5 negatives), with Unity C# lab/Editor scene builder, separate M04 run scripts using frozen M03 v0.8, conservative post-freeze scorer, SHA build manifest and privacy rules.
- Public release: [source](../source/m04_unseen_v01/), [ZIP](../archives/ModStudioAI_M04_UnseenLab_v01.zip). 26/26 Python unit tests + temporary generation smoke passed. **No Unity 6.3 compilation or build from M04 exists yet; no model score yet.**
- Next on user Windows: create empty UnityTextLabB project in Unity Hub, import TMP essentials, generate with `Scripts/Create_M04_Local.ps1`, Editor menu scene creation, Mono build; report only build success/Unity errors without source/truth. Do not leak private answers to public repo.


## M04 Unity editor validation: build succeeded but invalid for benchmark (2026-11-02)

- Windows Unity 6000.3 scene/Play renders UI; BuildPipeline created UnityTextLabB.exe; Console reports five missing/no-valid-script warnings on M04 readers and table asset and several UI `...` placeholders.
- Determined public generator v0.1 has ambiguous MonoBehaviour/ScriptableObject types in one source file. [Repair v0.2](../source/m04_script_binding_fix_v02/) separates types and rebuilds six reader refs/table asset from existing local spec, preserving seed/truth. Adds build guard; 9/9 Python structural tests passed; NO Windows Unity compile/test yet.
- Block M04 score until a clean rebuild, 15/15 populated UI labels, no missing-script warnings, new sealed build hash. Treat exposed screenshot cases as integration smoke test rather than perfect holdout.


## M04 Script Binding Fix v0.2 — Unity Editor Play visual smoke check (2026-11-02)

- User applied repair and validation menus, then posted Game View. All **15 UI labels display populated strings**, no `...` placeholders; Console shows **0 errors, 2 warning messages** consistent with intentional diagnostic cases, **no visible missing-script warnings**.
- This screenshot does **NOT** show the separate `[M04] Validation OK...` message because Console was cleared/Play logs only; formal validation status and a new Windows Mono rebuild still require explicit confirmation. **Do not run M04 AI scoring on prior invalid build.**
- Required next: exit Play mode, clear Console, run `Tools > Mod Studio AI > M04 > Validate Scene Bindings`, confirm `Validation OK`; then rebuild Windows Mono, inspect current build warnings; only if clean, proceed `seal -> rea -> evidence` against new build.
- Private screenshot exposes generated case text within chat; **do not upload screenshot or strings to public repo**. The current seed should be treated as integration smoke-test, not pristine secret holdout.


## M04 UnityTextLab-B repaired build + REA recorded; asset scan health unresolved

- User's Unity 6000.3 Windows Mono rebuild after M04 script binding fix has **0 console errors and 0 warnings** (only information messages). Prior Play smoke test shows 15 populated UI labels.
- M04 `seal` succeeded with **8 build files**; REA exported `assembly_identity.json` and `members.json` without error; `prepare` found **21 methods**.
- Frozen M03 v0.8 `scan-assets` returned **0 asset text observations**; `baseline` reported 4 observations and `provenance` 23 records, both unscored and **not coverage/accuracy**.
- Critical next check: collect ONLY the scanner's counts (`files_considered/files_scanned`, MonoBehaviour/TextAsset seen/decoded, error stages, raw_candidate_count, TypeTree loaded/errors) from `Milestone04/Runs_LOCAL/AgentInput/build_assets.json`. Do not upload raw `assets`, strings, private project, seed, ground truth or hash-linked confidential case data to public repo.
- Until diagnostics distinguish unreadable serialized assets vs simply unsupported source classes, **do not interpret 0 observations as a negative model result**. Preserve M03 v0.8 frozen baseline and existing hash-sealed run; do not tune/fix mid-experiment without a new explicitly labeled protocol.


## M04 frozen scanner health check — decoded correctly (2026-11-02)

User executed safe aggregate PowerShell health-check on `Runs_LOCAL/AgentInput/build_assets.json`: `files_considered=6`, `files_scanned=6`, `truncated=false`, `monobehaviours_seen/decoded=33/33`, `textassets_seen/decoded=8/8`, `assets=23`, `raw_candidates=0`, `reader_bindings=0`, `errors=0`, TypeTree imported, one loaded version, zero TypeTree errors. The earlier `scan-assets observations=0` is **CLI summary display only**: M03 v0.8 prints `len(output.get('observations',[]))` for scans, while scan JSON actually uses `assets` (23 records). The frozen M03 v0.8 hard-codes UnityTextLab-A reader class, so 0 reader bindings in B is an expected coverage limitation, not a parsing error.

**Build evidence is technically usable for M04 functional integration trials.** Preserve `seal`, REA, source hash and build-only input without modifying scanner mid-benchmark. Run local Ollama probe, then 3 autonomous and 3 guided repeated trials; only after complete/locked predictions run separate M04 private scorer. Never interpret baseline 4 observations or provenance 23 as correctness scores. No generated case strings, private files or raw traces were committed.
