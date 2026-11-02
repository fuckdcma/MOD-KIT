# M04 — Private Regression Scorer v0.3 cho Evidence-Grounded v1.0

**Mục tiêu:** chấm đúng ba lượt `evidence_r01..r03` của Agent v1.0 trên **UnityTextLab-B đã lộ trước đây**, dùng đúng **quy tắc chấm M04 v0.2** đã sử dụng cho Static v0.8 / Guided v0.8 / Autonomous v0.9. Đây là **kiểm thử hồi quy tích hợp**, **KHÔNG phải holdout mới**, và **KHÔNG thay thế benchmark v0.8**.

Bằng chứng người dùng báo cáo trước khi chấm: catalog 10 ứng viên (3 hardcoded, 3 runtime, 4 external JSON), mỗi lượt chọn 6, 6 `validation_status=observed`, 0 lỗi giao thức, 3/3 lượt hoàn tất. Đây là số liệu kỹ thuật, **không phải độ chính xác 6/15**. Catalog chưa nhận diện được prefab và ScriptableObject của B; 19 serialized nguồn không xác minh bị loại.

## Chạy một lần trên Windows 11

1. Giữ nguyên các thư mục đã niêm phong: 
   - `D:\ModStudioAI\Milestone03\src\modstudio_m03.py`
   - `D:\ModStudioAI\Milestone04\Runs_LOCAL` (REA + UnityPy nguyên gốc)
   - `D:\ModStudioAI\Milestone04\Runs_EVIDENCE_GROUNDED_V10_LOCAL` (3 kết quả mới)
   - `D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD` (**đáp án riêng tư**) 
2. Giải nén ZIP vào thư mục riêng. Mở PowerShell tại thư mục chứa `Scripts`, `src`, `vendor`, `tests` và chạy:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Score_M04_EvidenceGrounded_v10_Regression.ps1
   ```

3. Bộ chấm từ chối chạy nếu mã M03, bản sao REA/UnityPy, chiến lược v1.0, hash assembly, hoàn thành hoặc trạng thái validator không hợp lệ. Không chạy Qwen thêm, không sửa bất kỳ kết quả M03/M04 nào.

4. File **chỉ có số liệu tổng hợp an toàn để chia sẻ**:

   `D:\ModStudioAI\Milestone04\Runs_V10_REGRESSION_SCORE_V03_LOCAL\metrics_V10_REGRESSION_AGGREGATE_ONLY.json`

   In bảng:

   ```powershell
   $p = 'D:\ModStudioAI\Milestone04\Runs_V10_REGRESSION_SCORE_V03_LOCAL\metrics_V10_REGRESSION_AGGREGATE_ONLY.json'
   $m = Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
   $m.runs | Select-Object run, version, observations_total, positive_total, source_and_text_matches, observed_supported_matches, false_positive_claims, ambiguous_duplicate_observations | Format-Table -AutoSize
   ```

5. Hai loại dữ liệu **KHÔNG ĐƯỢC tải lên GitHub hoặc gửi chat**:
   - `PRIVATE_DO_NOT_UPLOAD\metrics_PRIVATE_V10_REGRESSION_V03_*.json` (đánh giá từng ca và các chuỗi âm tính)
   - `PRIVATE_DO_NOT_UPLOAD\locked_predictions_V10_REGRESSION_V03_*` (bản sao dự đoán raw)

## Giới hạn phương pháp

- Chấm **15 UI dương tính** và kiểm tra **5 ca âm tính**, nguồn đúng và chuỗi đúng phải khớp chính xác; `observed_supported_matches` còn đòi `validation_status='observed'` từ validator và `confidence='observed'`. Đây vẫn chỉ là bằng chứng tĩnh. Không khẳng định luồng IL stack→TMP setter hoặc runtime UI.
- Nguyên quy tắc v0.2 nằm tại `vendor/m04_evaluate_v02.py` **không chỉnh sửa** (SHA-256 `77de1425502c5912e972c873c0d96ba177140e77036d113d8e617522af9f69df`); wrapper v0.3 chỉ thêm ràng buộc phiên bản, cách khóa và nhãn study.
- Ba lượt v1.0 bị đánh giá bằng chính bộ B đã dùng khi phát triển, do vậy kết quả tốt hơn (nếu có) chỉ mang tính **hồi quy**, không chứng minh tổng quát hóa. Để test blind phải tạo B2 mới sau khi khóa code/prompt và trước khi thấy đáp án.
- Tệp tổng hợp chỉ chứa số lượng và SHA, không chứa text/ground truth. Tên source method/asset của từng nhận định chỉ nằm trong bản raw giữ riêng tư.
- Bộ chấm **không ghi đè** thư mục kết quả hoặc private lock nào. Khi đã chạy một lần, không chạy lại cùng `ScoreDir`; nếu cần so sánh tiếp, tạo nghiên cứu khác có tên phiên bản khác.

## Tự kiểm thử (không cần Qwen, không đọc B)

```powershell
& 'D:\ModStudioAI\Milestone03\.venv\Scripts\python.exe' -m unittest discover -s .\tests -v
```

Kiểm thử tự sinh dữ liệu giả lập, **không chứa seed/đáp án/chuỗi B thật**.
