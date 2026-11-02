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
