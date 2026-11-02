# Báo cáo Milestone 03 v0.8 — Semantic consistency guard

## Từ người dùng, 2026-11-02

- `Run_M03.ps1 -Mode tests`: **80/80** trên Windows.
- Ollama native probe `status=ok`, elapsed **5,56 s**.
- Guided `qwen3.5:4b`: **completed:true**, 8 observations, có một phản hồi JSON `finish=length` ở bước 2 và được retry thành công.
- Evaluator Guided: **3 exact / 0 dynamic template / 2 unproven**. Các case đúng: T002, T003, T005. Sai: T004 bị phân loại `hardcoded_managed`, chưa có proof T001 prefab.

## Kiểm định chất lượng bằng chứng

Trong v0.7 có 4 observations `observed` (3 đúng + 1 sai kiểu) và 4 `candidate_only` (3 thông báo lỗi và một key tra cứu). Với v0.8, chính 8 nhận định cũ được kiểm tra lại: **3 `observed` + 5 `candidate_only`**, điểm riêng không thay đổi (3/0/2). Điều này sửa sai cấp kiểm tra mà không ghi đè phân loại do AI sinh.

Bằng chứng REA cho T004: literal `Health: {0}/100`, call `System.String.Format` và `TMPro.TMP_Text.set_text` cùng `ModStudioLab.RuntimeTextExample.Refresh`; kết luận nguồn **mẫu runtime-generated** là phù hợp ở mức method-level. Chưa chứng minh chi tiết IL stack-to-setter hay lần chạy runtime.

## Phát triển

- Thêm kiểm tra source-type consistency; `il_literal` không còn hợp lệ để chứng minh loại nguồn asset.
- Prompt Guided yêu cầu phân loại template/diagnostic/key đúng và giới hạn độ dài note nhằm giảm JSON truncation.
- CLI in thẳng số liệu `evaluate` thay vì `observations:0`.
- **96/96 Python tests offline đạt** (80 cũ + 16 mới); `baseline` với JSON người dùng đạt 3 exact + 1 template + 1 unknown. Chưa có lượt Qwen v0.8 mới.

## Giới hạn & bước tiếp

Không thay đổi điểm Qwen v0.7 và không chấm lại một lần chạy v0.8 chưa có. Sau khi cài, chạy Guided trên máy Windows/Ollama local và so sánh riêng T004; vẫn cần game holdout chưa công bố để đo tổng quát.
