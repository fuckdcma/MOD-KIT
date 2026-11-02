# Artifact index — snapshot 2026-11-02

## Snapshot nguyên gốc

[archives/MODKIT_Chat_Artifacts_20261102.zip](../archives/MODKIT_Chat_Artifacts_20261102.zip) đã được đưa vào nhánh main. Bao gồm 88 file sẵn có trong phiên này: ZIP/RAR, PNG, JSON/CSV, log, báo cáo, code và source extracts. Bên trong ZIP có MANIFEST_SHA256.json với SHA-256/size của từng file.

## Tệp đọc trực tiếp trên GitHub

- [Hồ sơ bàn giao](CHAT_HANDOFF.md)
- [REA](../evidence/m01/rea/) và [Player.log](../evidence/m01/runtime/Player.log)
- [M03 build-only JSON](../evidence/m03/latest/)
- [M02 & M03 reports](../reports/)
- [Dữ liệu tham chiếu](../benchmarks/reference_DO_NOT_FEED_MODEL/) — PUBLIC, không phải secret
- [Source code](../source/) — được bổ sung theo các commit riêng; nếu liên kết chưa tồn tại, giải nén snapshot ZIP để lấy source.

## Các giới hạn

Không có API tự động xuất nguyên văn lịch sử chat ChatGPT. Phần đã lưu chỉ là *tài liệu bàn giao + toàn bộ file hiện vật khả dụng*. Bản UnityTextLab đang nằm trên máy tác giả có thể có scene/prefab/build khác những file đã tải lên; không coi các tệp cục bộ chưa đồng bộ là đã có trên GitHub.

Mỗi lần có milestone mới, cập nhật cả source, evidence và CHANGELOG. Không commit token/secret, thư mục .venv/Library, game thương mại hoặc trọng số model không được phép chia sẻ.


## Bản vá gần nhất — M03 v0.3

- [Mã nguồn, tests, installer, README](../source/m03_provenance_v03/)
- [Source hash manifest](../source/m03_provenance_v03/SOURCE_SHA256.json)
- [ZIP nguyên bản](../archives/ModStudioAI_M03_Provenance_Fix_v03.zip)
- [Báo cáo](../reports/m03/BAO_CAO_M03_V03.md)

Không coi `provenance_links.json` v0.3 là đã có trong kho vì người dùng cần chạy lại bản build trên Windows.


## M03 v0.4 — Pointer Resolver

- [Mã nguồn, installer, fixture, tests](../source/m03_pointer_v04/)
- [Manifest SHA256](../source/m03_pointer_v04/SHA256_MANIFEST.json)
- [ZIP nguyên bản](../archives/ModStudioAI_M03_PointerResolver_Fix_v04.zip)
- [Báo cáo kỹ thuật v0.4](../reports/m03/BAO_CAO_M03_V04.md)
- Chưa có Windows scan v0.4; không nhầm với kết quả mới nhất v0.3 trong `evidence/m03/runs/20261102_v03/`.


## M03 Ollama Agent v0.5 (latest code)

- [Patch source, Windows installer, tests](../source/m03_ollama_fix_v05/)
- [ZIP](../archives/ModStudioAI_M03_OllamaAgent_Fix_v05.zip)
- [QA report](../reports/m03/BAO_CAO_QWEN_FIRST_RUN_VI.md), [input hash manifest](../reports/m03/QA_INPUT_HASHES_OLLAMA_FIRST_20261102.json)
- [User's aborted Agent trace](../evidence/m03/runs/20261102_ollama_first/qwen_agent.json), [0/5 incomplete evaluation (invalid as AI score)](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_first/evaluation_private_agent.json)
- [Uploaded RAR original](../raw_uploads/Outputs_M03_Ollama_First_20261102.rar). Contains same baseline/build/provenance as M03 v0.4; no duplicated uploads needed.


## M03 Qwen v0.5 successful run & v0.6 patch

- [Qwen v0.5 run](../evidence/m03/runs/20261102_ollama_v05_completed/) including [qwen_agent.json](../evidence/m03/runs/20261102_ollama_v05_completed/qwen_agent.json); [evaluator output](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v05_completed/evaluation_private_agent.json) and [RAR original](../raw_uploads/Outputs_M03_Ollama_v05_completed_20261102.rar).
- [v0.6 source, installer, unit tests](../source/m03_evidence_guided_v06/), [patch ZIP](../archives/ModStudioAI_M03_EvidenceGuided_Fix_v06.zip), [QA review](../reports/m03/BAO_CAO_QWEN_V05_REVIEW_V06.md).
- v0.6 outputs are not available until running on user's Windows Ollama. Public GitHub evaluation files are NOT a secret blind benchmark.


## M03 Guided v0.6 timeout and v0.7 patch

- [Original Guided timeout trace](../evidence/m03/runs/20261102_ollama_v06_guided_timeout/qwen_agent_guided.json), [RAR upload](../raw_uploads/Outputs_M03_Ollama_v06_GuidedTimeout_20261102.rar).
- [v0.7 browsable Python/PowerShell/test source](../source/m03_timeout_v07/), [release ZIP](../archives/ModStudioAI_M03_OllamaTimeout_Fix_v07.zip) containing full data contract, [QA analysis](../reports/m03/BAO_CAO_M03_V07.md).
- No completed v0.6 guided report or v0.7 Windows test output exists yet.


## M03 Guided v0.7 uploaded run, v0.8 follow-up

- [All user-uploaded JSON + upload hash manifest](../evidence/m03/runs/20261102_ollama_v07_guided_completed/) from original [Outputs.rar](../raw_uploads/Outputs_M03_Ollama_Guided_v07_20261102.rar), plus [Windows log](../history/M03_Ollama_v07_Run_Log_20261102.txt).
- [Guided evaluation](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v07_guided_completed/evaluation_private_guided.json) is PUBLIC (separated by convention only).
- [v0.8 source and tests](../source/m03_semantic_v08/), [ZIP installer](../archives/ModStudioAI_M03_SemanticValidation_Fix_v08.zip), [QA report](../reports/m03/BAO_CAO_XAC_MINH_QWEN_GUIDED_V07_20261102.md).
- No v0.8 live Ollama report yet; replay file in patch demonstrates only revalidation of prior model output.


## M03 v0.8 — latest live result + transition to M04

- [Guided output](../evidence/m03/runs/20261102_ollama_v08_guided/qwen_agent_guided.json)
- [Guided reference evaluator](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_ollama_v08_guided/evaluation_private_guided.json) — PUBLIC despite filename, never feed to agent.
- [Original user RAR (all 11 JSON including v0.7 History)](../raw_uploads/Outputs_M03_Ollama_Guided_v08_20261102.rar); [original PowerShell run log](../history/M03_Ollama_v08_Run_Log_20261102.txt); [SHA-256 file manifest](../evidence/m03/runs/20261102_ollama_v08_guided/SHA256_MANIFEST.json).
- [Independent QA report](../reports/m03/BAO_CAO_XAC_MINH_M03_GUIDED_V08_20261102.md)
- [M04 unseen holdout testing protocol](M04_UNSEEN_HOLDOUT_PROTOCOL.md). Private seed and answer key must NOT enter this public repo.


## M04 v0.1 public generator artifacts (NO private holdout data)

- [Browsable 17 source/test/docs/manifest files](../source/m04_unseen_v01/)
- [Download release ZIP](../archives/ModStudioAI_M04_UnseenLab_v01.zip)
- [Source byte SHA-256 manifest](../source/m04_unseen_v01/PUBLIC_SOURCE_SHA256.json)
- [Privacy/evaluation rules](../source/m04_unseen_v01/Docs/PRIVACY_AND_EVALUATION.md)
- No generated UnityTextLabB project, seed, case values, private ground truth, Editor build, REA/UnityPy B outputs, or model scores have been uploaded to GitHub. These must remain private until predictions locked.


## M04 Script Binding Fix v0.2 — public-only code

- [Source and PowerShell installer](../source/m04_script_binding_fix_v02/) · [ZIP](../archives/ModStudioAI_M04_ScriptBindingFix_v02.zip) · [README](../source/m04_script_binding_fix_v02/README_VI.md).
- Includes C# editor repair script, Unity runtime classes separated into matching files, backup/build guard script, 9 offline tests and SHA-256 manifest.
- No user screenshot, private UnityTextLabB scene/spec/ground-truth/seed, regenerated source, or invalid build binary uploaded to public GitHub.


## M04 Autonomous Bounded Context v0.9 — isolated public engineering package

- [Source, PowerShell runner, tests and protocol](../source/m04_autonomous_bounded_v09/)
- [Download ZIP](../archives/ModStudioAI_M04_Autonomous_BoundedContext_v09.zip)
- [Public SHA256 manifest](../source/m04_autonomous_bounded_v09/PUBLIC_SHA256_MANIFEST.json)
- Test report: **7/7 offline Python tests**; no live Windows/Ollama benchmark completed; existing first-attempt Autonomous failure preserved.
- Contains public engine/testing code only: **no user-generated UnityTextLab-B text, answers, seed, AgentInput, model outputs, screenshots or game project files**.
