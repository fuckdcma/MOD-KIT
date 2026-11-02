# MOD Studio AI — M04 Mixed-Version Private Score v0.2

**Mục đích:** sau khi Qwen Guided v0.8 hoàn tất 3/3 (11 nhận định/lượt, **11/11 rejected**), và Autonomous Bounded v0.9 hoàn tất 3/3 (1 nhận định/lượt, **1/1 observed**), chấm riêng tư đối chiếu 15 ca dương tính + 5 ca negative *mà không sửa/ghi đè bất kỳ thí nghiệm nào*.

**Quan trọng:** Đây là so sánh **khác phiên bản** (Guided v0.8 và Autonomous v0.9 experimental), KHÔNG được gọi là benchmark công bằng cùng-phiên-bản. Hai lần thất bại Autonomous v0.8 (1280 và 2560 token) tiếp tục được ghi nhận là **lỗi vận hành**, không bị biến mất hoặc tính là 0/20 đúng.

## Lý do scorer cần v0.2

Scorer M04 v0.1 tính `observed_supported_matches` dựa trên `confidence='observed'` và sự hiện diện của trường `evidence_type`, method/source_ref. Nó không yêu cầu `validation_status='observed'` do bộ lọc bằng chứng đóng băng cấp. Trong tình huống Guided trả 11 nhận định bị `rejected`, scorer có thể đánh giá quá cao `observed_supported_matches` nếu model tự gán confidence. **Bản v0.2 chỉ tính hỗ trợ bằng chứng nếu cả `validation_status='observed'` VÀ `confidence='observed'` và có bằng chứng/method/source_ref; không chứng minh runtime dataflow.** Giữ nguyên phép so khớp nguồn + text (`source_and_text_matches`) như một thước đo khác, tách biệt.

## Cách chạy Windows

Giải nén ZIP vào thư mục riêng và mở PowerShell tại nơi có `Scripts`, `src`, `tests`. Không chạy script chấm v0.1 trước đó. Chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Score_M04_MixedVersion_v02.ps1
```

Script kiểm tra SHA frozen M03 v0.8 và hai file REA/UnityPy đầu vào, đối chiếu SHA lắp ghép với config v0.9, và yêu cầu 7 file hoàn tất trước khi đọc private truth: `baseline_r01`, `guided_r01/02/03` từ `Runs_LOCAL`; `autonomous_r01/02/03` từ `Runs_AUTONOMOUS_BOUNDED_V09_LOCAL`. Không thu nhận hai file Autonomous `completed=false`.

Kết quả:

- **SAFE-TO-SHARE sau chấm:** `D:\ModStudioAI\Milestone04\Runs_MIXED_SCORE_V02_LOCAL\metrics_MIXED_V08_GUIDED_V09_AUTO_AGGREGATE_ONLY.json`. Có score tổng, hash, nhãn phiên bản; không có private case text.
- **PRIVATE, KHÔNG ĐƯA LÊN MẠNG:** `D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD\metrics_PRIVATE_MIXED_V02_*.json` và `locked_predictions_MIXED_V02_*`.

Script **từ chối ghi đè** `Runs_MIXED_SCORE_V02_LOCAL` đã có. Nếu cần chấm lại, chọn một `-ScoreDir` khác và ghi rõ protocol; không xóa output cũ.

Sau khi hoàn tất, chỉ gửi *bảng số liệu tổng hợp từ file AGGREGATE_ONLY* (hoặc file AGGREGATE_ONLY) vào cuộc trò chuyện. Không gửi: `ground_truth_PRIVATE.json`, `ProjectSettings/M04HoldoutLocal.json`, seed, source Unity sinh ra, raw AgentInput, bất cứ file `locked_predictions` và `metrics_PRIVATE*` nào.

**Giới hạn:** scanner M03 v0.8 vẫn thiếu nhận diện binding lớp M04; nguồn SerializedPrefab trong Unity build không tự có đường dẫn `.prefab` như Unity Editor. Chỉ số `observed_supported_matches` là bằng chứng tĩnh đã được validator chấp nhận, không phải chứng minh runtime dataflow hay UI. Bản seed B đã từng xuất hiện chuỗi trong ảnh chụp; nên coi đây là integration holdout, không phải đánh giá mù bí mật tuyệt đối.
