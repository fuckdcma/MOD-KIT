# MOD-KIT — Mod Studio AI Project Library

**Repository tài liệu và dữ liệu kỹ thuật dài hạn của dự án Mod Studio AI.** Mốc lưu: 2026-11-02.

## Đọc theo thứ tự

1. [CHAT_HANDOFF.md](docs/CHAT_HANDOFF.md) — hồ sơ bàn giao khi chuyển sang cuộc trò chuyện khác.
2. [ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) — nguyên tắc và quyết định đã chốt.
3. [PROGRESS.md](docs/PROGRESS.md) — tiến độ Milestone 01–03.
4. [M03_LATEST_FINDINGS.md](docs/M03_LATEST_FINDINGS.md) — các kết quả build-only mới nhất.
5. [ARTIFACT_INDEX.md](docs/ARTIFACT_INDEX.md) — vị trí file được lưu và phần chưa đồng bộ.
6. [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — sự cố Windows/Python/UnityPy.
7. [SYNC_AND_PRIVACY.md](docs/SYNC_AND_PRIVACY.md) — quy trình đồng bộ, bảo mật, giới hạn archive.

## Tầm nhìn

Mod Studio AI nghiên cứu nguồn text và font, trích xuất nguồn gốc văn bản, nghiên cứu điểm can thiệp bằng REA, tạo adapter mapping text/font 1:1 và kiểm thử mod độc lập. **Ứng dụng Việt hóa là sản phẩm riêng.** Unity Mono được ưu tiên; IL2CPP và Unreal để giai đoạn sau.

## Trạng thái hiện tại

| Giai đoạn | Trạng thái |
|---|---|
| M01 UnityTextLab & REA | Đạt trong laboratory |
| M02 Editor Provenance | 8 bản ghi, 5/5 case đối chiếu với dữ liệu nguồn |
| M03 UnityPy TypeTree v0.2 | 6/6 file, 32/32 MonoBehaviour, 0 lỗi |
| M03 bộ chấm hiện tại | 2 exact / 1 template / 2 unproven |
| Qwen local / LoRA / hook standalone | Chưa kiểm thử hoàn chỉnh |

**Không đồng nhất số liệu công cụ với năng lực AI.**

> **Cảnh báo:** Repository hiện là **public**. Các tệp trong `benchmarks/reference_DO_NOT_FEED_MODEL` chỉ được tách theo quy ước — không hề riêng tư. Việc đưa ground truth công khai có thể làm nhiễm benchmark; muốn một blind test thực sự cần tập đáp án ngoài public repo.

Không thể tự động chép nguyên văn toàn bộ transcript ChatGPT sang đây qua các công cụ hiện có. Kho này lưu bản ghi bàn giao và những file có thể truy xuất; xem [giới hạn](docs/SYNC_AND_PRIVACY.md).

## Snapshot hiện vật 2026-11-02

- [Tải toàn bộ hiện vật đã có trong sandbox (ZIP)](archives/MODKIT_Chat_Artifacts_20261102.zip): 88 file, gồm các ZIP/RAR mã nguồn, ảnh, logs, báo cáo và JSON, có manifest SHA-256. **Không phải bản export nguyên văn toàn bộ chat.**
- [Hồ sơ bàn giao](docs/CHAT_HANDOFF.md) để tiếp tục phiên ChatGPT sau.
- [Mã nguồn được duyệt trên GitHub](source/) sẽ được đồng bộ thành các tệp riêng; xem [chỉ mục](docs/ARTIFACT_INDEX.md).

### Final synchronization status

[Snapshot status / SHA-256 manifest](docs/SNAPSHOT_STATUS.md): archived 88 available original files, published 47 browsable source/evidence text files. Source copies were checked against original SHA-256/Git object IDs. Raw chat messages are **not** exported.


## Milestone 03 v0.3 — Provenance Linker (2026-11-02)

- [Mã nguồn & installer v0.3](source/m03_provenance_v03/) · [Tải gói ZIP](archives/ModStudioAI_M03_Provenance_Fix_v03.zip)
- [Báo cáo v0.3](reports/m03/BAO_CAO_M03_V03.md); 22/22 unit tests; **chưa chạy scanner v0.3 trên PC Windows**.
- Bản v0.3 giải quyết việc bảo toàn `LabStringTable.entries[N].key` cùng `entries[N].value`; T001 prefab origin vẫn chưa có proof. **Điểm chấm thực tế hiện vẫn 2 exact +1 template +2 not proven cho dữ liệu v0.2**.


## Milestone 03 v0.4 — Cross-file PPtr Resolver (2026-11-02)

- [Source, tests and installer v0.4](source/m03_pointer_v04/) · [Download ZIP](archives/ModStudioAI_M03_PointerResolver_Fix_v04.zip) · [Engineering report](reports/m03/BAO_CAO_M03_V04.md)
- **34/34 local synthetic unit tests passed.** Unity 6.3 v0.4 build scan has **not** been run on the user's PC; do not claim pointer resolved until new scan.
- v0.3 real run: **3 exact + 1 template + 1 unproven (T001)**. New resolver checks actual serialized file external table before linking T002 reader to table.


## Verified v0.4 Windows run (2026-11-02)

- [Build evidence v0.4](evidence/m03/runs/20261102_v04/) · [QA report](reports/m03/BAO_CAO_XAC_MINH_M03_V04_20261102.md) · [original RAR](raw_uploads/Outputs_M03_v04_20261102.rar).
- **1/1 serialized reader pointer resolved** (T002). Baseline remains **3 exact, 1 template, 1 not proven (T001)**; Qwen baseline not yet measured.


## M03 Ollama Qwen3.5 first run + agent fix v0.5 (2026-11-02)

- GPU confirmed **100% GPU**, `qwen3.5:4b`, ~3.1 GB, context 4096 from user `ollama ps`.
- [First-run Agent trace](evidence/m03/runs/20261102_ollama_first/qwen_agent.json): incomplete, first tool call OK, second step invalid JSON. **0/5 evaluation is NOT a valid AI performance measurement**, because `completed=false`.
- [Fix v0.5 sources](source/m03_ollama_fix_v05/) · [ZIP](archives/ModStudioAI_M03_OllamaAgent_Fix_v05.zip) · [QA report](reports/m03/BAO_CAO_QWEN_FIRST_RUN_VI.md). **51/51 local tests passed**. Windows/Ollama live retest pending.


## M03 Qwen v0.5 completed; evidence-guided v0.6 (2026-11-02)

- [User's completed Qwen autonomous trace](evidence/m03/runs/20261102_ollama_v05_completed/qwen_agent.json) — `completed=true`, 3 steps, 2 observations; [evaluator](benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v05_completed/evaluation_private_agent.json): **1 exact, 0 template, 4 unproven**. Extra observation is a diagnostic/error literal, not proven UI text. Tool baseline: **3 exact + 1 template**.
- [v0.6 guided source](source/m03_evidence_guided_v06/) · [install ZIP](archives/ModStudioAI_M03_EvidenceGuided_Fix_v06.zip) · [QA report](reports/m03/BAO_CAO_QWEN_V05_REVIEW_V06.md).
- v0.6 uses compact REA+build-only evidence brief and conservative `candidate_only` diagnostic status. **66/66 local Python tests passed; no Windows/Ollama v0.6 model run yet.** Guided and autonomous results must be measured separately.


## M03 Guided v0.6 timeout — repair v0.7 (2026-11-02)

- User's guided v0.6 output returned `completed:false`, `observations:[]` due to HTTP `TimeoutError('timed out')` on request 1, after controller prepared a 4,706-char brief. **No guided accuracy score exists.** [Raw trace](evidence/m03/runs/20261102_ollama_v06_guided_timeout/qwen_agent_guided.json) · [original RAR](raw_uploads/Outputs_M03_Ollama_v06_GuidedTimeout_20261102.rar).
- [Timeout/Probe v0.7 code](source/m03_timeout_v07/) · [complete ZIP including data contract](archives/ModStudioAI_M03_OllamaTimeout_Fix_v07.zip) · [QA report](reports/m03/BAO_CAO_M03_V07.md).
- v0.7 provides local JSON probe, configurable HTTP timeout default 600s, `num_predict=1280`, bounded brief 3900 chars retaining 6 REA methods and 2 source-qualified assets. **80/80 local tests pass (66 old +14 new)**; not yet tested live with user Ollama. Baseline replay scores 3 exact + 1 template + 1 unknown.


## Verified v0.7 Guided Qwen + v0.8 semantic consistency fix (2026-11-02)

- [Qwen v0.7 guided run](evidence/m03/runs/20261102_ollama_v07_guided_completed/qwen_agent_guided.json), [evaluator](benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v07_guided_completed/evaluation_private_guided.json): **completed=true**, 8 observations, **3 exact + 0 format template + 2 unproven**. Tool static baseline: **3 exact + 1 template + 1 unproven**. Ollama probe passed in 5.56 seconds. Trace includes one invalid/truncated JSON reply that was retried successfully.
- Key gap: Qwen found `Health: {0}/100` but labeled it `hardcoded_managed`, not `runtime_generated`. [v0.8 semantic validation patch](source/m03_semantic_v08/) marks that incorrect assertion `candidate_only` without auto-correcting the model answer. [ZIP](archives/ModStudioAI_M03_SemanticValidation_Fix_v08.zip), [report](reports/m03/BAO_CAO_XAC_MINH_QWEN_GUIDED_V07_20261102.md).
- **96/96 offline Python tests passed**; v0.8 live Windows/Ollama inference pending. Keep public lab as functional regression only, not a secret holdout.


## Verified Qwen Guided v0.8 — M03 regression target achieved (2026-11-02)

- [New guided result](evidence/m03/runs/20261102_ollama_v08_guided/qwen_agent_guided.json) · [evaluation](benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v08_guided/evaluation_private_guided.json) · [QA report](reports/m03/BAO_CAO_XAC_MINH_M03_GUIDED_V08_20261102.md).
- User Windows **96/96 tests passed**, Qwen3.5 4B Guided `completed=true`, **4 observations**; evaluator **3 exact + 1 runtime template + 1 not proven**, matching the static-rule baseline. T004 `Health: {0}/100` is correctly tagged `runtime_generated` by the model, not auto-fixed. T001 serialized-prefab origin remains unproven.
- [Original RAR](raw_uploads/Outputs_M03_Ollama_Guided_v08_20261102.rar), [PowerShell log](history/M03_Ollama_v08_Run_Log_20261102.txt), [SHA256 manifest](evidence/m03/runs/20261102_ollama_v08_guided/SHA256_MANIFEST.json). The evaluator was reproduced independently with semantic JSON match.
- **Next:** [M04 unseen holdout protocol](docs/M04_UNSEEN_HOLDOUT_PROTOCOL.md). Public lab is functional regression, not a secret benchmark; Qwen autonomous and runtime-hook provenance are not solved by this result.


## Milestone 04 — Unseen UnityTextLab-B generator v0.1 (2026-11-02)

[Browse M04 source](source/m04_unseen_v01/) · [Release ZIP](archives/ModStudioAI_M04_UnseenLab_v01.zip) · [Windows setup in Vietnamese](source/m04_unseen_v01/README_VI.md).

**26/26 Python tests passed and ephemeral private-seed smoke test passed.** M04 is a **public generator/evaluator**, not a fixed publicly labelled dataset. It creates 20 cases locally (15 UI, 5 negative), a fresh 256-bit seed and private ground truth OUTSIDE public MOD-KIT. M03 v0.8 stays frozen for evaluation. **Unity 6000.3 Editor compile/build and Qwen testing on B have not yet been run.** Never commit generated Unity project, ProjectSettings/M04HoldoutLocal.json, seed, ground truth, or raw model outputs until safe to publish.


## M04 UnityTextLab-B build warning diagnosed — Script Binding Fix v0.2 (2026-11-02)

- User demonstrated Unity Editor Play and successful Windows Mono build, but Console shows **5 missing/invalid script warnings** from M04 readers and ScriptableObject, with several UI placeholders still `...`. **Do not evaluate this build yet.**
- Root cause: the public generator template `M04LabRuntime.cs` defines multiple MonoBehaviour/ScriptableObject classes in one file; their Unity MonoScript asset mapping is ambiguous. [Source/repair instructions](source/m04_script_binding_fix_v02/) · [ZIP](archives/ModStudioAI_M04_ScriptBindingFix_v02.zip).
- Patch backs up files, splits classes into matching `.cs` names, repairs six readers and rebuilds one ScriptableObject from the EXISTING private local spec (no seed regeneration), and adds a pre-build guard. **9/9 offline static tests pass; Unity Windows compile/rebuild not tested yet.** Only publish public patch code, never screenshot/private spec/seed/cases.


## M04 Autonomous Bounded Context v0.9 — experimental recovery (2026-11-02)

The original M03 v0.8 Autonomous r01 failed at step 8 with invalid JSON `finish=length` x3. A separate 2560-token retry against identical SHA-matched REA/UnityPy input **also failed** at the same step with identical three JSON error details. Guided M03 v0.8 completed 3/3 runs (11 observations each, **not scored**). This does not establish an accuracy score or uniquely prove context overflow.

A [new **experimental** v0.9 bounded-history runner](source/m04_autonomous_bounded_v09/) and [Windows ZIP](archives/ModStudioAI_M04_Autonomous_BoundedContext_v09.zip) change Autonomous chat-context management and set native Ollama `num_ctx=8192` (also `num_predict=2560`, 16 steps), without modifying the **frozen M03 v0.8 source**. Includes SHA-fingerprint checks and isolated output directory. **7/7 offline Python tests passed; no live Ollama/Windows run yet.** Private B game labels, ground truth, source, agent outputs and raw traces were not committed.


## M04 Evidence-Grounded v1.0 (experimental, 2026-11-02)

Public source: [v1.0](source/m04_evidence_grounded_v10/) | [Windows ZIP](archives/ModStudioAI_M04_EvidenceGrounded_v10.zip). The B mixed-version score was baseline v0.8 3/15 validator-supported, Guided v0.8 0/15 supported, Autonomous v0.9 1/15 supported. New v1.0 lets local Qwen select only exact evidence IDs from frozen M03 v0.8 REA/UnityPy verified records, instead of composing free-form source claims. 24/24 synthetic tests PASS; no live Windows Ollama results yet. The old B is regression only, not a pristine new holdout.


## M04 Evidence-Grounded v1.0 live Windows result and private regression score v0.3 (2026-11-02)

User's Windows run SHA-confirmed original frozen M03 and both sealed B REA/UnityPy inputs. v1.0 preflight enumerated **10** qualified static candidates (3 hardcoded managed, 3 runtime templates, 4 external JSON), excluding 19 unproven serialized sources. All three local Qwen evidence-ID selection trials **completed with 6/10 selected, 6/6 validator-observed, 0 protocol errors**. This establishes evidence consistency, **not 6 correct UI cases**. [Separate v0.3 private regression scorer](source/m04_evidence_grounded_score_v03/) and [Windows ZIP](archives/ModStudioAI_M04_EvidenceGrounded_PrivateRegressionScore_v03.zip) preserve exact earlier v0.2 scoring semantics, SHA-lock predictions, output aggregate-only results, and label B as exposed integration regression. **14/14 synthetic scorer tests PASS; no v1.0 accuracy score yet**. Create blind B2 only after code freeze.
