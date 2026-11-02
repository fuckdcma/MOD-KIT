# Báo cáo M03 — Baseline phân tích tĩnh (không dùng AI)

Ngày tạo: 2026-11-02. Dữ liệu: REA `Assembly-CSharp.dll`, SHA-256 `ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e`.

## Đã chạy
- 7/7 unit tests: đạt, trong đó có phép chuyển đổi từ REA `members.json` thật (16 phương thức).
- REA evidence mẫu đã duyệt: 6 phương thức hướng text/SDF từ bản build người dùng đã cung cấp.
- Bộ luật tĩnh tạo 4 quan sát: 2 `observed`, 2 `hypothesis`. Không gán trạng thái `observed` cho giá trị chưa thấy trong bản build.
- Đối chiếu private 5 case: `Quest Completed` exact (T003), `Health: {0}/100` format template (T004), T001/T002/T005 chưa chứng minh được nội dung.

## Kết quả
| Case | Kết quả chứng cứ từ assembly |
|---|---|
| T001 New Game | not_proven (prefab/scene serialization, chưa đọc từ build) |
| T002 Load Game | not_proven (có đường gọi bảng, chưa thấy value) |
| T003 Quest Completed | exact_text |
| T004 Health: 75/100 | template_text (`Health: {0}/100`) |
| T005 Hello, Commander | not_proven (có Resources.Load và tên dialogue, chưa thấy JSON value) |

**Không phải kết quả kiểm thử model Qwen.** Không có model local hay bản build UnityData đầy đủ trong môi trường tạo gói, nên chưa chạy kiểm thử Qwen/Vulkan hoặc asset scanner thật.

## Giai đoạn tiếp
1. Chạy `Run_M03.ps1 -Mode baseline` để xác minh trên Windows.
2. Chạy `-Mode scan-assets` sau khi cài UnityPy để xem có đọc thêm Serialized Text hay không.
3. Khi đã có GGUF và llama-server Vulkan, chạy `-Mode agent`; gửi `Outputs/qwen_agent.json` để kiểm tra hành vi AI.
4. Chỉ khi có benchmark thật mới quyết định tạo SFT/LoRA dataset cho từng kỹ năng yếu.