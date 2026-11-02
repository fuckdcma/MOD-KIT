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
