# Báo cáo M03 v0.3 — Provenance Linker / Text Source Discovery

Ngày: 02-11-2026. Dữ liệu đầu vào thực tế: `build_assets.json` v0.2 và `model_input_rea_evidence.jsonl` lấy từ REA trên UnityTextLab.

## Đã thực hiện

- Xây bộ đọc cặp `entries[N].key`/`entries[N].value` từ cùng đối tượng `ModStudioLab.LabStringTable`, yêu cầu class và đường dẫn field có cấu trúc chính xác.
- Thu thập reader config `TableTextExample.key` và con trỏ `table` nếu deserialize được; không giả định PPtr cross-file tự resolve.
- Xuất `provenance_links.json` phân biệt `source_key_value_observed`, `source_value_observed`, `ui_snapshot_only`, `unproven`, và `runtime_binding`.
- Bổ sung baseline `scriptable_object` chỉ khi key/value có bằng chứng cùng object. Không nâng `TMP_Text.m_text` lên `serialized_prefab`.
- 22/22 unit tests Python đạt, trong đó 1 test mô phỏng API UnityPy, 9 test mới (bao gồm kiểm thử giả mạo bằng chứng), 12 test từ M03 cũ.

## Đối chiếu với dữ liệu người dùng gửi (scanner v0.2)

- T001 `New Game`: có chuỗi trong `level0`, chưa chứng minh prefab origin → **chưa xác minh**.
- T002 `Load Game`: có value `LabStringTable.entries[0].value`, nhưng **chưa có entry_key trong JSON v0.2** → **chưa xác minh**.
- T003 `Quest Completed`: REA exact ldstr → **đúng nguồn**.
- T004 `Health: {0}/100`: REA template → **mẫu động**.
- T005 `Hello, Commander`: TextAsset `dialogue.message` → **đúng nguồn**.

Bộ chấm chạy lại với v0.2: **2 exact / 1 template / 2 unproven**, không tự nâng điểm.

## Kỳ vọng khi chạy v0.3 trên PC

Nếu TypeTree giải mã `LabStringTable.entries[0].key` (ví dụ `menu.load`) cùng value tương ứng, tool sẽ xác nhận **giá trị tại nguồn bảng** và có thể chấm T002 ở mức `source+text`. `reader_binding` vẫn có thể là `unresolved` vì chứng minh gọi TryGet/SetText chưa đủ chứng minh reader instance trỏ tới asset đó.

**Không khẳng định 3/5 exact khi chưa nhận kết quả quét mới từ Windows.** Không khẳng định T001 prefab origin từ `level0`. Không có bằng chứng Qwen đã được chạy hoặc mod standalone đã được biên dịch.

## Các tệp cần kiểm tra sau lần chạy trên Windows

`Outputs/build_assets.json`, `Outputs/provenance_links.json`, `Outputs/baseline_static.json`, `Outputs/evaluation_private.json`.

Thực thi: `powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests` rồi `scan-assets`, `provenance`, `baseline`, `evaluate`.

- Sửa PowerShell evaluator để không ưu tiên nhầm `qwen_agent.json` cũ; mặc định đánh giá baseline, tùy chọn `-EvaluateTarget agent`.
