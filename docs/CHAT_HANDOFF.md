# Chat handoff — Mod Studio AI (2026-11-02)

## Hướng dẫn cho AI ở phiên trò chuyện mới

Đây là hồ sơ chuyển giao kỹ thuật. Trước khi đưa quyết định mới, hãy đọc `ARCHITECTURE_DECISIONS.md`, `PROGRESS.md`, `M03_LATEST_FINDINGS.md`, và các JSON trong `evidence/m03/latest/`. Không khẳng định đã chạy Qwen, hook hay fine-tuning khi chưa có log kiểm chứng. Không dùng `benchmarks/reference_DO_NOT_FEED_MODEL` làm đầu vào của agent lúc đánh giá.

## Sản phẩm và nguyên tắc

- Mod Studio AI và Translator/Localization Studio **là hai ứng dụng riêng**.
- Mod Studio phải tự tìm nguồn text: scene/prefab, ScriptableObject/string table, hardcoded CIL, runtime-generated, JSON/custom manager; lưu provenance gồm asset/object/field/method và mức bằng chứng.
- Mod đầu ra phải hoạt động **độc lập**, không bắt người dùng cài BepInEx/Harmony/MelonLoader/Mod Studio AI. REA là công cụ nghiên cứu, không là loader.
- Định hướng Hook Text & Font Mapping **1:1**, ID/ngữ cảnh ưu tiên hơn exact string; bảo toàn placeholder, rich-text, lifecycle.
- Font SDF: kiểm tra font asset, glyph coverage, atlas, material, shader, padding, gradient/sampling, fallback, clipping và overwrites. Không khẳng định một kỹ thuật chữa được mọi game.
- Unity Mono trước; Unity IL2CPP rồi Unreal. Offline và các tình huống có quyền mod; không bypass anti-cheat.
- REA (npm `rea-agents`) lấy bằng chứng managed metadata/callgraph; UnityPy + TypeTreeGeneratorAPI đọc asset serialized.
- AI lõi dự kiến Qwen3.5-4B, inference local qua llama.cpp Vulkan trên RX 6700 XT 12 GB. LoRA trên cloud khi đủ dữ liệu verified; không fine-tune sớm. RAG phục vụ tài liệu.

## Máy thử nghiệm và đường dẫn Windows

- Windows 11; Unity Editor 6000.3.27f2, Mono Windows x64.
- `D:\ModStudioAI\UnityLab\UnityTextLab` — project Unity nguồn.
- `D:\ModStudioAI\Builds\UnityTextLab\UnityTextLab_Data` — bản build Unity Mono.
- `D:\ModStudioAI\Research\REA` — các báo cáo REA.
- `D:\ModStudioAI\Milestone03` — tool Python; `.venv\Scripts\python.exe` là Python 3.12.10 x64; UnityPy 1.25.4; tpk_ar 0.2.4; TypeTreeGeneratorAPI 0.0.10 trong lần scanner v0.2.
- Model Qwen chưa có bằng chứng chạy thực tế.

## UnityTextLab 5 case chuẩn

| Case | Giá trị | Nguồn thiết kế |
|---|---|---|
| T001 | New Game | Serialized prefab TMP |
| T002 | Load Game | LabStringTable ScriptableObject: menu.load |
| T003 | Quest Completed | ModStudioLab.HardcodedTextExample.Awake |
| T004 | Health: {0}/100, snapshot 75/100 | RuntimeTextExample.Refresh |
| T005 | Hello, Commander | Resources/dialogue.json, key message |

Game đã chạy, Player.log có `sameAtlas=True` cho LiberationSans SDF / LiberationSans SDF Material; vẫn chưa kiểm tra Việt glyph. REA: Assembly-CSharp.dll SHA256 ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e, 16 methods, 9 type defs, 14 fields.

## Kết quả gần nhất

- **M01:** game lab, ảnh UI, 2 báo cáo REA, Player.log đều có; text hiển thị; runtime Health đổi theo thời gian.
- **M02:** Editor Collector xuất 8 record: 5 scene TMP, 1 prefab TMP, 1 ScriptableObject, 1 Resources JSON; 0 cảnh báo; đủ 5 case khi đối chiếu với ground truth.
- **M03 v0.1:** REA CIL chứng minh hardcoded + template; UnityPy scan bản đầu tìm JSON, nhưng 32 lỗi MonoBehaviour.
- **M03 v0.2, JSON mới nhất 2026-11-02:** quét 6 file; **32/32 MonoBehaviour decoded**, 5/5 TextAsset decoded; 7 asset observations, 0 errors, 0 raw candidates; TypeTreeGenerator loaded Unity 6000.3.27f2.
- Giá trị `New Game` ở `level0#path_id=35` trong `TMP_Text.m_text`, **không chứng minh asset prefab nguồn**.
- `Load Game` ở `level0#path_id=31` (TMP UI) và `sharedassets0.assets#path_id=16` (`ModStudioLab.LabStringTable.entries[0].value`), hiện source_type='unknown' trong scan. Có bằng chứng lớp ScriptableObject, nhưng evaluator chưa xác nhận toàn bộ provenance.
- `Quest Completed` và `Health: 75/100` cũng trong scene TMP; đây là snapshot UI, không phải nguồn gốc; REA mới chứng minh hardcoded và dynamic template.
- `Hello, Commander` trong `resources.assets#path_id=9`, `TextAsset dialogue.message` chứng minh external JSON.
- Evaluator v0.2 vẫn **2 exact + 1 template + 2 not_proven**. Không sửa điểm bằng cách đoán. M03 là **rule-based tool baseline**, chưa đánh giá AI.

## Công việc kế tiếp ưu tiên

1. Nâng cấp provenance linker: nối `LabStringTable.entries[0].value` với `TableTextExample.Start -> LabStringTable.TryGet`, lấy key thật `menu.load` từ asset và xác minh T002.
2. Với T001, phân biệt `level0` scene TMP, đối tượng thuộc prefab/instance và serialized prefab origin bằng object identity + prefab relationship; chỉ nâng điểm khi chứng minh được.
3. Kết hợp REA + asset scanner để tạo report `observed/likely/unproven` có bằng chứng cụ thể và hạn chế.
4. Sau khi tool có năng lực kiểm chứng đáng tin, chạy Qwen3.5-4B GGUF bằng llama.cpp Vulkan localhost, đo first baseline agent chưa fine-tune.
5. Mở rộng lab bằng các ca SDF known-good/known-bad, glyph Việt, dynamic string, trùng chuỗi đa ngữ cảnh, material overwrite.
6. Chuẩn hóa case provenance/version/hash, giữ holdout riêng theo game; không đưa ground truth của build này vào prompt đánh giá.

## Lưu trữ

Repo này là **public**. Các file từ ChatGPT chưa được commit đầy đủ (đặc biệt các ZIP tool, ảnh screenshot, thư mục code giải nén) được nêu trong `ARTIFACT_INDEX.md`. Có công cụ `tools/Sync_Local_Artifacts.ps1` để người dùng tự đồng bộ nguồn local sau khi kiểm tra. Hồ sơ này không phải bản sao nguyên văn toàn bộ cuộc chat.


## Cập nhật v0.3 — cuối ngày 2026-11-02

Đã phát triển, test Python **22/22 đạt** và commit [Provenance Linker v0.3](../source/m03_provenance_v03/) cùng [ZIP cài đặt](../archives/ModStudioAI_M03_Provenance_Fix_v03.zip). Bản này đọc key/value serialized trên cùng `LabStringTable`, bảo toàn `TableTextExample.key` và PPtr dưới dạng metadata, phân loại `TMP_Text.m_text` là UI snapshot; không tự nhận prefab origin hoặc runtime binding. Cần **cài bản v0.3 trên máy Windows rồi scan-assets mới**. Trên JSON v0.2 đã được người dùng gửi, điểm vẫn **2 exact / 1 template / 2 unproven**; chỉ khi JSON v0.3 có paired key từ build mới có khả năng nâng T002 lên source+text proven. **Chưa có log thực tế v0.3.**

Chạy PowerShell trong `D:\\ModStudioAI\\Milestone03`: `tests` → `scan-assets` → `provenance` → `baseline` → `evaluate`, theo README tại `source/m03_provenance_v03/README_VI.md`. Gửi `build_assets.json`, `provenance_links.json`, `evaluation_private.json` để tiếp tục.


## Xác minh đầu ra Windows v0.3 — 2026-11-02

Đã nhận [bộ JSON v0.3](../evidence/m03/runs/20261102_v03/) từ máy Windows và [báo cáo xác minh](../reports/m03/BAO_CAO_XAC_MINH_M03_V03_20261102.md). UnityPy quét 6/6 file, MonoBehaviour 32/32, TextAsset 5/5, 7 bản ghi, 1 reader binding, **0 errors**. Ground truth evaluator **3 exact (T002, T003, T005) + 1 template (T004) + 1 chưa proven (T001)**. Đã chạy lại offline provenance/baseline/evaluate bằng source v0.3, 3 JSON kết quả trùng nội dung với bản tải lên; 22/22 tests đạt.

**T002** có key/value serialized (`menu.load → Load Game`) đúng class `ModStudioLab.LabStringTable` ở `sharedassets0.assets#path_id=16`. Reader `level0#path_id=40` giữ key `menu.load` và pointer `m_FileID=3,m_PathID=16` nhưng `binding_status=unresolved_build_pointer`. Chưa xác minh target external mapping; **không gọi là runtime binding proven**. **T001** chỉ được thấy như UI snapshot `level0#path_id=35`, chưa chứng minh prefab origin.

Bước tiếp theo: đọc external references table `level0` để chứng minh pointer tới asset; giữ T001 not_proven; sau đó chạy Qwen nền local. **Không dùng evaluation_private.json hoặc Editor provenance trong agent prompt.**


## Bản vá v0.4 — cần xác minh bằng Unity build (2026-11-02)

[Source v0.4](../source/m03_pointer_v04/) và [ZIP installer](../archives/ModStudioAI_M03_PointerResolver_Fix_v04.zip) đã được tạo, **34/34 unit tests Python đạt**. v0.4 dùng `UnityPy obj.assets_file.externals[m_FileID-1]` để kiểm tra quan hệ PPtr tới bảng ScriptableObject theo file name duy nhất, PathID, class và key. `m_FileID=0` tham chiếu cùng file. Nếu bảng externals không có/khác, vẫn giữ `unresolved_build_pointer` — không suy đoán theo PathID/key. **Đây là proof cấu hình serialized**, không phải chứng cứ runtime đã gọi hàm.

Đã chạy logic v0.4 trên JSON v0.3 cũ: score vẫn `3 exact + 1 template + 1 unproven` và pointer vẫn unresolved vì dữ liệu cũ thiếu external mapping. **Chưa có `build_assets.json` v0.4 từ Windows.** Để tiếp tục, cài bản vá, chạy `tests -> scan-assets -> provenance -> baseline -> evaluate`; gửi mới `build_assets.json`, `provenance_links.json`, `evaluation_private.json`. Giữ T001 chưa chứng minh prefab origin. [README chi tiết](../source/m03_pointer_v04/README_VI.md).


## Milestone 03 v0.4 — Windows scan đã xác minh (2026-11-02)

Người dùng tải lên `Outputs.rar` sau khi chạy Pointer Resolver v0.4. Bản gốc và 4 JSON lưu tại [runs/20261102_v04](../evidence/m03/runs/20261102_v04/), [RAR gốc](../raw_uploads/Outputs_M03_v04_20261102.rar), [evaluation riêng](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_v04/evaluation_private.json), [báo cáo QA](../reports/m03/BAO_CAO_XAC_MINH_M03_V04_20261102.md).

- UnityPy scan 6/6 files; 32/32 MonoBehaviour decoded, 5/5 TextAsset decoded; 7 asset observations, 0 errors, 1/1 reader pointer resolved.
- **T002:** `TableTextExample level0#path_id=40` key `menu.load`, PPtr m_FileID=3/m_PathID=16, `level0.externals[2]=sharedassets0.assets`, target `sharedassets0.assets#path_id=16` class `ModStudioLab.LabStringTable` entry `menu.load → Load Game`; `binding_status=serialized_pointer_resolved`. Proof covers serialized configuration and REA method-call flow **not runtime execution**.
- T001 `New Game` only TMP `m_text` scene observation, `not_proven` source prefab.
- Evaluator: **3 exact + 1 dynamic template + 1 not_proven**. Same counts as v0.3; v0.4 strengthened pointer proof.
- Replayed v0.4 `provenance`, `baseline`, `evaluate` with uploaded build JSON: all 3 outputs semantically identical to Windows files; CRLF vs LF only. **34/34 unit tests passed** locally. Unity build itself is not available for independent rescanning here.
- **Next:** Qwen untrained local baseline (localhost llama-server), keep reference ground truth/Editor evidence away from agent; build a separate private holdout because this public repository contains lab answers. T001 prefab origin should not be invented.


## Qwen Agent local lần 1: GPU OK, giao thức Agent lỗi (2026-11-02)

Người dùng cho xem `ollama ps`: `qwen3.5:4b` **100% GPU** (~3.1GB, context4096, runner llamacpp). User upload [RAR](../raw_uploads/Outputs_M03_Ollama_First_20261102.rar) và [qwen_agent.json](../evidence/m03/runs/20261102_ollama_first/qwen_agent.json): `completed=false`, tool step1 `search_literals(text)` trả 2 dòng, step2 lỗi `Expecting value: line 1 column 1`, 0 observations. [Agent evaluator](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_first/evaluation_private_agent.json) 0/5 **chỉ do aborted**, không phải kết quả AI thực. Tool baseline remains 3 exact / 1 template / 1 unproven (T001).

Đã viết và kiểm thử [Ollama Fix v0.5](../source/m03_ollama_fix_v05/), [ZIP installer](../archives/ModStudioAI_M03_OllamaAgent_Fix_v05.zip). Python **51/51 tests passed** (34 old + 17 new), run baseline vs uploaded build_assets.json semantically identical. Native Ollama `/api/chat`, `think=false`, `format=json`; controlled retries, safe error trace, bounded context, incomplete evaluation is rejected. **Not yet run with user's live Ollama**.

Next: apply v0.5 on Windows, execute `tests` then `agent -Server http://127.0.0.1:11434 -Model qwen3.5:4b`; inspect `qwen_agent.json.completed`; only if true run `evaluate -EvaluateTarget agent`. Do not put ground truth/Editor provenance into AI inputs. If fails, send trace and PowerShell log; evaluate cause based on error codes, not assume Qwen poor.


## Qwen Agent v0.5 success and v0.6 guided pending (2026-11-02)

User's `Run_M03.ps1 -Mode tests` passed **51/51**, then `-Mode agent -Transport ollama -Model qwen3.5:4b` returned `completed:true` and 2 observations. [Trace](../evidence/m03/runs/20261102_ollama_v05_completed/qwen_agent.json): 3 steps `search_literals(Quest)` → `inspect_method(HardcodedTextExample.Awake)` → `finish`. [Evaluation](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v05_completed/evaluation_private_agent.json): **1 exact (T003), 0 template, 4 not_proven**; rule baseline still **3 exact + 1 template + 1 unknown**. Second agent observation is a diagnostic `ldstr` string not proven to reach TMP UI. Qwen/Ollama/GPU transport works, but agent exploration stopped prematurely.

Developed [v0.6 evidence-guided patch](../source/m03_evidence_guided_v06/), [ZIP](../archives/ModStudioAI_M03_EvidenceGuided_Fix_v06.zip), [report](../reports/m03/BAO_CAO_QWEN_V05_REVIEW_V06.md): **66/66 local Python tests passed** (51 prior + 15 new). Guided brief uses only REA method evidence and build-only asset reader; no Unity Editor data or evaluator ground truth supplied. Diagnostic-looking `ldstr` is `candidate_only`. Distinct result files: `qwen_agent_guided.json` vs `qwen_agent_autonomous.json`; this is a strategy experiment, not an unbiased model generalization test. **Windows Ollama v0.6 run not yet done.**

Next run: install v0.6, run `tests`, `agent -Strategy guided -Transport ollama -Server http://127.0.0.1:11434 -Model qwen3.5:4b`; only evaluate with `-EvaluateTarget guided` if `qwen_agent_guided.json.completed = true`. User should send `qwen_agent_guided.json` and `evaluation_private_guided.json`. Keep T001 prefab provenance unproven. Public GitHub lab isn't a secret holdout.


## M03 Guided v0.6 real timeout; v0.7 pending Ollama retest (2026-11-02)

User installed v0.6, passed **66/66 Windows tests**, ran `-Mode agent -Strategy guided -Transport ollama -Model qwen3.5:4b`. [User's output](../evidence/m03/runs/20261102_ollama_v06_guided_timeout/qwen_agent_guided.json) shows `completed:false` and no observations; step0 evidence brief 4706 chars, six REA methods, two qualified assets and five UI snapshots; step1 `transport_error: TimeoutError: timed out`. v0.6 local_chat timeout=180 seconds, Ollama `num_predict=2048`; cause is client timeout, **not model accuracy**. Screenshot GPU 100% but cannot infer throughput.

Developed v0.7 [source](../source/m03_timeout_v07/) / [ZIP](../archives/ModStudioAI_M03_OllamaTimeout_Fix_v07.zip), test **80/80** offline. New `-Mode probe` sends tiny JSON to Ollama localhost; `-TimeoutSeconds 600`, `-NumPredict 1280`, `-BriefChars 3900` for Guided; `num_ctx=4096`. On fixture, two source-qualified assets + six REA methods remain; unverified UI snapshots can be trimmed. Incomplete runs remain unscored; baseline replay remains 3+1+1. **No Windows v0.7 run yet.**

Next: apply v0.7, run tests, run probe with `-TimeoutSeconds 120`, then guided with 600/1280/3900 if probe succeeds, inspect completed before evaluate. Upload `ollama_probe.json` and `qwen_agent_guided.json` and PowerShell log if still timed out. Never feed public ground truth/Editor data into Agent. Prefab T001 remains unproven.


## New confirmed state — 2026-11-02, M03 Qwen Guided v0.7 completed; v0.8 code ready

Received user's `Pasted text.txt` + `Outputs.rar`: Windows [80/80 tests](../history/M03_Ollama_v07_Run_Log_20261102.txt), [probe status=ok 5.56 sec](../evidence/m03/runs/20261102_ollama_v07_guided_completed/ollama_probe.json). [Guided Qwen trace](../evidence/m03/runs/20261102_ollama_v07_guided_completed/qwen_agent_guided.json) has `completed=true`, 8 observations, 3 research steps, step 2 invalid/truncated JSON `finish=length` recovered by retry. [Evaluator](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v07_guided_completed/evaluation_private_guided.json) scores **3 exact (T002,T003,T005), 0 template, 2 unproven (T001,T004)**. Static baseline = 3 exact + 1 template + 1 unproven. This is a Guided strategy score; autonomous v0.5 was 1 exact/5.

Qwen mislabeled `Health: {0}/100` from `ModStudioLab.RuntimeTextExample.Refresh` as `hardcoded_managed` even though REA shows `System.String.Format` + `TMP_Text.set_text`. v0.7's validator incorrectly marked the same observation `observed` at method-level. Four other extra observations were three diagnostic/log strings and a lookup key `menu.load`, all `candidate_only`.

Developed [M03 Semantic Validation v0.8](../source/m03_semantic_v08/) and [installer ZIP](../archives/ModStudioAI_M03_SemanticValidation_Fix_v08.zip), [QA report](../reports/m03/BAO_CAO_XAC_MINH_QWEN_GUIDED_V07_20261102.md): **96/96 offline tests passed** (80 old+16 new). Validator now downgrades misclassified format string `hardcoded_managed` to `candidate_only` without rewriting model tags. Replay same 8 v0.7 observations yields **3 observed + 5 candidate_only, score remains 3/0/2**. Baseline replay on user JSON remains 3 exact + 1 template + 1 unproven. CLI evaluate prints actual counts instead of misleading `observations:0`. **No new v0.8 Windows inference yet.**

Next: user installs v0.8, runs 96 tests, backs up old `qwen_agent_guided.json`, reruns Guided Ollama `qwen3.5:4b` (600s, num_predict 1280, brief_chars 3900), checks completed, only then evaluates and uploads new report. Focus first on whether **T004 correctly becomes runtime_generated**; T001 prefab origin still unproven. Do not put public benchmark ground truth or Editor references in model input. Need unseen holdout for generalization.


## Latest confirmed — M03 v0.8 Qwen Guided reaches rule baseline (2026-11-02)

User uploaded [Windows log](../history/M03_Ollama_v08_Run_Log_20261102.txt) and [original RAR](../raw_uploads/Outputs_M03_Ollama_Guided_v08_20261102.rar) after installing v0.8. Windows **96/96 tests passed**. [Guided Qwen3.5:4b output](../evidence/m03/runs/20261102_ollama_v08_guided/qwen_agent_guided.json): `completed=true`, strategy guided, exactly **4 observations**, one `finish` after controller's evidence summary (six REA methods, two qualified assets), no request errors in trace. [Private-labelled evaluator (but PUBLIC repo)](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v08_guided/evaluation_private_guided.json): **3 exact + 1 dynamic template + 1 unproven**. T002 ScriptableObject, T003 hardcoded, T005 external JSON; T004 `Health: {0}/100` **correctly classified by Qwen as `runtime_generated`**. T001 prefab origin remains not proven. [QA report](../reports/m03/BAO_CAO_XAC_MINH_M03_GUIDED_V08_20261102.md), [raw artifacts manifest](../evidence/m03/runs/20261102_ollama_v08_guided/SHA256_MANIFEST.json).

Independently reran Python v0.8 evaluator with user `qwen_agent_guided.json` and ground truth held locally for scoring; semantic report **exactly matches** Windows `evaluation_private_guided.json`. Backup of v0.7 inside RAR: 8 observations and score 3+0+2. New v0.8: 4 observations and 3+1+1; no extra log diagnostics/technical lookup key. Dynamic evidence is **method-level static IL**, not validated end-to-end runtime stack dataflow. Do not claim 100% complete or all five sources found. This is one known public Unity lab and guided orchestration, not independent model generalization.

**Milestone pivot:** mark M03 Guided 5-case regression target **met (4 evidenced, T001 unresolved)**. Stop prompt-tuning to overfit this public case; implement [M04 Unseen Holdout Protocol](M04_UNSEEN_HOLDOUT_PROTOCOL.md) with new UnityTextLab-B and private (nonpublic) ground truth, separate autonomous/guided/rule baseline, log repeatability and false positives. Keep public repo as technical library, but do NOT publish private holdout answers before evaluation.


## Milestone 04 started — generator v0.1 shipped, Windows build pending (2026-11-02)

Last verified M03 remains Qwen Guided v0.8: 3 exact + 1 dynamic template + 1 unproven (prefab T001), 96/96 Windows tests. Do NOT overfit that public lab.

[M04 source](../source/m04_unseen_v01/), [release ZIP](../archives/ModStudioAI_M04_UnseenLab_v01.zip), [Vietnamese README](../source/m04_unseen_v01/README_VI.md), and [holdout protocol](M04_UNSEEN_HOLDOUT_PROTOCOL.md). M04 v0.1 **Python 26/26 tests passed**, temporary local-generation smoke passed with automatically deleted test data. **Not yet Unity Editor compiled or run on user's Windows machine.**

M04 CLI `Scripts/Create_M04_Local.ps1` requires a NEW empty Unity 6000.3.27f2 project `D:\\ModStudioAI\\UnityLab\\UnityTextLabB`; generates a fresh local 256-bit seed, 20 hidden text cases (3 prefab, 3 ScriptableObject, 3 CIL hardcoded, 3 runtime format, 3 Resources JSON, 5 negative), all strings and private truth are created on the USER PC only. Generator refuses to overwrite seed and rejects private folders under Git. Open Unity and import TextMeshPro essentials. Then Tools > Mod Studio AI > M04 > Generate Unseen Lab B Scene, Play, and Build Unseen Lab B Windows Mono. Build path defaults `D:\\ModStudioAI\\Builds\\UnityTextLabB\\UnityTextLabB.exe`.

After build, M04 `Scripts/Run_M04.ps1 -Mode seal/rea/evidence` obtains hashes and REA/UnityPy from B; `-Mode autonomous -Repeats 3` and `-Mode guided -Repeats 3` use *frozen* M03 v0.8 source + Ollama Qwen3.5:4b; outputs in Milestone04/Runs_LOCAL, NOT M03 Outputs. Only after these outputs are locked run `Scripts/Evaluate_M04_Private.ps1`, which produces private per-case and public aggregated counts separately. The M03 scanner has hard-coded `ModStudioLab.LabStringTable` recognition: **expect B ScriptableObject may be unknown, deliberately do not tune before first benchmark**.

Security: do not upload generated `UnityTextLabB` sources, `ProjectSettings/M04HoldoutLocal.json`, `PRIVATE_DO_NOT_UPLOAD`, or any answer strings into PUBLIC repository or same AI prompt before freezing scores. Do not claim results for M04 until Windows logs and real Build SHA exist. On Unity compilation error, request only error message without the private source/seed/spec.


## M04 v0.1 scene built; missing Unity script bindings — fix v0.2 pending Windows validation (2026-11-02)

User shared Unity Editor screenshots (not to be uploaded to this public repo): Play renders text but some TMP labels remain `...`; BuildPipeline reports successful Windows Mono executable **with 5 warnings about missing/invalid scripts** attached to `M04_Reader_*` and `M04HoldoutTable.asset`. Therefore **original M04-B build is NOT valid for blind AI evaluation** despite a successful binary build. Public generator source has multiple Unity MonoBehaviour and ScriptableObject types declared in one `M04LabRuntime.cs`, an ambiguous MonoScript mapping. Unity documentation advises one Unity component class per matching .cs file.

Prepared [M04 Script Binding Fix v0.2](../source/m04_script_binding_fix_v02/) / [installer ZIP](../archives/ModStudioAI_M04_ScriptBindingFix_v02.zip). Offline **9/9 structural tests pass; not Unity-compiled on user's PC**. To apply: CLOSE Unity; run `Scripts/Install_M04_ScriptBindingFix.ps1`; reopen existing UnityTextLabB scene, choose `Tools > Mod Studio AI > M04 > Repair Missing Script Bindings`, then `Validate Scene Bindings`, Play, and rebuild only after no missing script warnings. Installer preserves local seed/spec/private truth, backs up scripts, and refuses overwrites. Editor repair rebuilds ScriptableObject and 6 reader components from EXISTING private spec; builder gains guard to prevent invalid build. **Re-seal build SHA and repeat REA/scanner only after clean rebuild.**

IMPORTANT: The screenshot already revealed some rendered private test text to this conversation; do NOT commit screenshot, regenerated C# source, seed, private truth, spec or raw build to PUBLIC MOD-KIT. This B instance is best treated as integration validation; for a strict secret holdout later, create a new unexposed seed/game after patch is validated. Never give ground truth to Qwen prompt.


## M04 v0.2 repair UI observation — 2026-11-02

After applying the [M04 Script Binding Fix v0.2](../source/m04_script_binding_fix_v02/), user shared a Play screenshot showing **15/15 non-placeholder TMP UI labels** and Console **2 diagnostic warnings, 0 errors**, with no missing-script messages visible. They report invoking Repair and Validate menus, but screenshot does not show the formal `[M04] Validation OK` log. **A fresh Windows Mono rebuild after repair has not yet been confirmed.** Next ask the user to exit Play, clear Console, rerun Validate Scene Bindings and confirm success, then rebuild Windows Mono and inspect new warning count. Only afterward run M04's seal, REA and evidence workflow. The old build with 5 missing-script warnings remains excluded from evaluation. Do not commit images or exposed private strings to public GitHub. Current UnityTextLab-B should be considered integration validation; use a new private seed for strict blind generalization tests.


## M04 next checkpoint — build clean, seal/REA works, asset reader zero records

User provided Unity console screenshot of rebuilt Windows Mono executable **0 warnings, 0 errors**, `seal` success with 8 files, `rea` exported both evidence files, `prepare` 21 methods, `scan-assets` output 0 observations, `baseline` 4, `provenance` 23. Do NOT assume 4 and 23 are case-score coverage and do NOT assume Unity build contains no text. Frozen M03 scanner has UnityTextLab-A-specific ScriptableObject class recognition; however that limitation alone doesn't explain zero overall asset observations. Ask for a **privacy-safe aggregate diagnostic summary** from `build_assets.json`: files scanned, MonoBehaviour and TextAsset seen/decoded, error count grouped by stage, TypeTree loaded/version error counts, raw candidate count. Avoid `assets` text or `errors[].error` raw strings in GitHub. The source/private case strings have appeared in screenshots, so this B run is integration validation rather than pristine blind holdout. Keep B output frozen before interpreting score; if tool reader malfunction, record separate fix experiment and keep frozen v0.8 results untouched.


## M04 scanner ambiguity resolved by safe aggregate metrics (2026-11-02)

User reported asset scanner stats: 6/6 files read, 33/33 MonoBehaviour decoded, 8/8 TextAsset decoded, 23 asset records, 0 errors, 0 raw fallback; TypeTree import and one version loaded without errors; reader_bindings=0. Misleading scan CLI `observations:0` comes from `modstudio_m03.py` summary `len(output.get('observations',[]))` while `scan_assets()` returns an `assets` list. Therefore scanner itself works; NO need to rebuild/reseal/REA/prepare. Known frozen code cannot recognize M04 class `ModStudioM04.M04TableReader` because reader matcher checks `ModStudioLab.TableTextExample`; keep limitation as benchmark measurement, do not change frozen source before first score. M04 baseline 4 observations and provenance 23 records are NOT evaluation scores.

Next: `Run_M04.ps1 -Mode probe`; then `-Mode autonomous -Repeats 3` and `-Mode guided -Repeats 3`, same existing sealed run, no overwrite. Only after all 6 completed should `Evaluate_M04_Private.ps1` run. Share aggregate public metrics after lock, not seed, generated source, answers or unfiltered traces. Current test set's values appeared in prior screenshots, so use as integration regression, not immaculate secret holdout.


## M04 Qwen trial status — next investigation (2026-11-02)

User ran frozen M03 v0.8 on sealed M04 B build. Ollama probe succeeded in **6.06s**. Three Guided trials (`guided_r01`, `r02`, `r03`) completed, each with **11 observations**. Autonomous `r01` returned `completed:false`, zero observations; M04 runner stopped without producing r02/r03. **No evaluator executed, so no score.** Agent trace can contain private test strings and method metadata; ask only safe columns `step, attempt, action, status, code, error_type, result_count, candidate_count, tool_result_truncated` from `autonomous_r01.json.trace` to diagnose. `run_agent` source writes `model_response_error`, `transport_error`, and `finish` trace records. M04 run script forbids overwriting existing `autonomous_r01.json`, so do not rerun same `-Mode autonomous -Repeats 3` against existing RunsDir or delete failed original. Any retry must be clearly versioned with frozen input hashes, saved failure kept, and benchmark reported with first-attempt failure rate. Avoid score until protocol requirements met. Keep all private files and model traces off public MOD-KIT.


## M04 Autonomous trace reveals invalid JSON after seven successful tools (2026-11-02)

User posted safe columns of `autonomous_r01.json.trace`: 7 successful actions (`list_methods`, five `inspect_method`, one `list_asset_candidates` with 0 results), then three `model_response_error/invalid_json` attempts at step 8. `completed=false`, 0 observations. This is **not a transport timeout**. Guided r01-r03 remain completed with 11 observations each; no accuracy score exists yet. M03 v0.8 `run_agent` appends all tool results (max 4500 chars each) to chat at Ollama `num_ctx=4096`; context pressure is plausible but not confirmed. To disambiguate, request safe `trace` fields `step,attempt,detail` for `code=invalid_json` (generated `detail` contains only length, JSON error line/column and model finish reason, not raw answer). Do not request raw private agent JSON on public GitHub. Preserve original failed run and sealed input. Engineering rerun requires separate private RunsDir/fingerprint and explicit retry label; never overwrite original, silently tune original benchmark, or treat retry success as first-attempt success. M04 evaluator rejects incomplete reports; not yet run.


## M04 step-8 Autonomous failure — output budget confirmed (2026-11-02)

User sent exact safe diagnostics for failed autonomous r01: at step 8 three successive model responses terminated `finish=length` with chars 1448 / 1314 / 1239, each parse failing near the end (column 1378 / 1291 / 1230). The Ollama-native local client in frozen M03 v0.8 specifies `num_predict=1280`, `num_ctx=4096`. This establishes generation-budget truncation; context pressure remains unproven. 7 tools previously executed successfully. Do not change frozen M03 source and do not overwrite this failed r01 or 3 completed Guided runs. Safe next trial: copy original unchanged `AgentInput` to a separate private `Runs_AUTONOMOUS_2560_LOCAL` directory with matching SHA-256, call original `Run_M04.ps1 -Mode autonomous -Repeats 3 -RunsDir ... -NumPredict 2560 -TimeoutSeconds 900`. Treat as *configured recovery trial*, not original first attempt, keeping each output/manifest and freeze checks. Avoid scoring until appropriately locked reports and protocol met, and avoid committing raw private data to PUBLIC GitHub.


## M04 follow-up: 2560-token Autonomous recovery r01 still incomplete (2026-11-02)

User copied original sealed build evidence to `Runs_AUTONOMOUS_2560_LOCAL` with two SHA-256 matches and executed original `Run_M04.ps1` with `-NumPredict 2560 -TimeoutSeconds 900 -Mode autonomous -Repeats 3`. Retry r01 produced `completed:false,observations:0`; subsequent r02/r03 were NOT started. This is a **separate configured recovery trial**, not a replacement for failed first-attempt 1280 run. The reason for 2560 failure is UNKNOWN until metadata from its trace is checked. Original 1280 r01 was step-8 invalid_json finish=length x3; Guided 3/3 completed 11 candidate observations each; no holdout scoring yet. Next send privacy-safe PowerShell command printing ONLY retry trace error metadata and step/action/result counts (do not paste private requests/text, full trace, seed). Keep M03 frozen and both incomplete reports. After diagnosis, implement bounded tool history only in separately versioned recovery runner, never silently in M03 v0.8.


## M04 v0.9 bounded-history experimental runner ready (2026-11-02)

User confirmed **retry-2560 failure** has EXACT identical diagnostic trace as original 1280 failure: successful steps 1–7; step 8 attempts 1/2/3 `model_response_error invalid_json finish=length` with chars **1448/1314/1239**, columns **1378/1291/1230**; no transport error. Source frozen v0.8 uses Ollama `num_ctx=4096` and accumulates complete tool feedback. This suggests testing bounded context, not assuming changing token count alone fixes it; precise mechanism not yet proven.

Created **M04 Autonomous Bounded Context v0.9** [source](../source/m04_autonomous_bounded_v09/) and [ZIP](../archives/ModStudioAI_M04_Autonomous_BoundedContext_v09.zip). Clone of v0.8 as `src/modstudio_m03_v09.py` leaves original source untouched and fingerprints proof/Guided/scanner sections; replaces only Autonomous tool conversation with bounded ledger, sets native Ollama ctx 8192 (vs 4096), output 2560, max 16 tool/model steps. Runner `Scripts/Run_M04_Autonomous_v09.ps1` copies EXACT REA/UnityPy files from original `Runs_LOCAL` to NEW `Runs_AUTONOMOUS_BOUNDED_V09_LOCAL`, verifies SHA equality to original evidence fingerprint and frozen M03 sha, stores manifest/hashes of earlier failures when present, and refuses overwrite. Offline **7/7 Python tests passing; NOT yet executed in Windows Ollama**. User should extract ZIP, open PowerShell inside folder and run `powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04_Autonomous_v09.ps1`; then report only safe aggregate completion/error counts. Do not request/upload raw outputs, private seed, B game source or answer key. Retain original baseline failure and existing Guided 3/3 unscored; v0.9 is a **separate configured recovery experiment**, not baseline scores.
