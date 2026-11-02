# Báo cáo M03 — Ollama timeout v0.7 (2026-11-02)

## Đầu vào thực tế

- Người dùng: đã cài v0.6; Windows 66/66 unit tests đạt.
- `Outputs.rar` mới: 7 JSON, riêng `qwen_agent_guided.json` ghi `completed:false`, `observations:[]`, trace bước 1 `TimeoutError('timed out')`.
- Step 0: evidence_chars=4706, methods_included=6, qualified_sources_included=2, unverified_ui_snapshots_included=5. Controller không chèn private answers.
- User screenshot: GPU 100% hoạt động; GPU utilization không xác nhận tốc độ suy luận hoặc thành công HTTP request.

## Nguyên nhân trực tiếp và suy luận

Trực tiếp: request HTTP blocking đến Ollama không nhận response hợp lệ trong timeout 180s của v0.6. Khả năng prompt nặng hay tốc độ output thấp là giả thuyết cần đo; không kết luận Qwen thiếu khả năng, cũng không cho rằng lỗi JSON tái xuất hiện.

## Sửa v0.7

1. Probe API localhost bằng JSON ngắn, không gửi REA hay data đánh giá.
2. Cho chỉnh timeout mặc định 600s; `num_predict` mặc định 1280, `num_ctx` 4096 để phù hợp với môi trường hiện tại.
3. Brief 3900 char; fixture hiện vẫn giữ 6 methods & 2 qualified assets.
4. Timeout được ghi với `timeout_seconds` và `recommended_action`; `completed:false` không được chấm.
5. Giữ 2 chế độ guided/autonomous; không tự gán điểm từ tool baseline.

## Kết quả kiểm thử

80/80 offline unit tests đạt (66 cũ + 14 mới). Không có inference Windows v0.7 mới; không có số liệu tốc độ thực tế. Bước kế tiếp: chạy probe, guided, upload trace mới.
