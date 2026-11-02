# Inventory — Những gì đã đồng bộ và chưa đồng bộ

## Đã đưa lên GitHub qua kết nối

- `evidence/m01/rea/`: `assembly_identity.json`, `members.json`.
- `evidence/m01/runtime/Player.log`, `benchmarks/reference_DO_NOT_FEED_MODEL/m01/ground_truth_v01.csv`.
- `reports/m01/`, `reports/m02/`, `reports/m03/`: báo cáo nguyên bản và bảng kết quả có thể đọc.
- `docs/legacy/`: các README / DATA_CONTRACT tại thời điểm từng bản công cụ.
- `evidence/m03/latest/`: `build_assets.json`, `baseline_static.json` mới nhất.
- `benchmarks/reference_DO_NOT_FEED_MODEL/m03/`: evaluation output (PUBLIC — chỉ tách logic, không bảo mật).
- `evidence/m03/history/`: baseline v0.1.
- `history/`: log chạy PowerShell đã tải lên.
- `research/notes/`: một ghi chú AirLLM được cung cấp trong project.

## Chưa đồng bộ nguyên gốc qua GitHub connector

Các **ZIP binary / RAR / PNG screenshot**, cùng những **file code chỉ nằm bên trong ZIP**, không thể chuyển nguyên byte qua GitHub connector dạng text trong phiên này. Các gói có mặt ở phiên ChatGPT tạo ra, nhưng sandbox link không phải đường dẫn GitHub lâu dài:

- `ModStudioAI_Starter_v01.zip`.
- `ModStudioAI_Milestone02_Collector_v01.zip`.
- `ModStudioAI_Milestone02_AGENT_INPUT.zip`, `ModStudioAI_Milestone02_REVIEW_PRIVATE.zip`.
- `ModStudioAI_Milestone03_LocalAgent_v01.zip`.
- `ModStudioAI_M03_Python312_Fix.zip`, `_v2.zip`, `_v3.zip`.
- `ModStudioAI_M03_AssetScanner_Fix_v02.zip`.
- `provenance_20261102_005843_135.rar`, `Outputs.rar`, ảnh chụp Unity Editor & runtime.
- Toàn bộ mã nguồn hiện có tại `D:\ModStudioAI\Milestone03` hoặc thư mục UnityTextLab trên máy tác giả.

Để thêm các nguồn này vào repo bằng Git credential trên máy chủ sở hữu, xem `tools/Sync_Local_Artifacts.ps1`. **Không giả định các file đã có mặt trên GitHub chỉ vì được liệt kê ở đây.**

## File sinh khi chạy công cụ

- Editor: `UnityTextLab/ModStudioExports/provenance_*/text_provenance.jsonl`, `manifest.json`, `warnings.txt`.
- Build scanner: `Milestone03/Outputs/build_assets.json`, `baseline_static.json`, `evaluation_private.json`.
- REA: `D:\ModStudioAI\Research\REA\assembly_identity.json`, `members.json`.

## Đề nghị đặt version

Dùng `milestones/m01`, `milestones/m02`, `milestones/m03`; quản lý source vs reference vs agent input, giữ manifest SHA-256 và commit ID. Không overwrite test outputs mà không giữ history. Với dữ liệu nhiều GB, dùng Drive/Git LFS nếu có quyền lưu; không commit virtualenv và Unity Library.
