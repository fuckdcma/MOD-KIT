# Mod Studio AI — M03 v0.7: Ollama Guided Timeout / Probe

Ngày: 2026-11-02. Phát triển từ bản **Evidence-Guided v0.6** đang chạy tại `D:\ModStudioAI\Milestone03`.

## Kết quả thực tế làm cơ sở

Người dùng đã chạy thành công 66/66 tests v0.6. Nhưng lần gọi `agent -Strategy guided` với Qwen3.5:4b trên Ollama local trả `completed:false`. Trong **`Outputs/qwen_agent_guided.json` của người dùng**:

```json
{"step":0,"action":"controller_evidence_brief","evidence_chars":4706,"methods_included":6,"qualified_sources_included":2}
{"step":1,"status":"transport_error","error_type":"TimeoutError","detail":"timed out"}
```

Như vậy đây là **HTTP request timeout** tại bước Qwen đầu tiên, *không phải chấm điểm 0/5* và không chứng minh model kém về reverse engineering. Bản v0.6 chờ tối đa 180 giây cho một request, yêu cầu model sinh tối đa 2048 tokens.

## Bản v0.7 thay đổi gì

- `-Mode probe`: gửi duy nhất một **yêu cầu JSON rất ngắn** qua API Ollama localhost và tạo `Outputs/ollama_probe.json` với thời gian hoàn thành. Probe **không đọc REA, ground truth hoặc game**.
- `-TimeoutSeconds`: điều chỉnh HTTP timeout (20–1800 giây), mặc định 600 giây khi dùng Agent. Chỉ thay thời gian client chờ, không khẳng định model sẽ chạy nhanh hơn.
- `-NumPredict`: số token tối đa của phản hồi, mặc định 1280 thay cho 2048, giúp giảm khối lượng sinh output.
- `-BriefChars`: giới hạn dung lượng brief, mặc định 3900; với fixture hiện có vẫn chứa **2 source-qualified asset và 6 method**, lược bớt một số `TMP_Text.m_text` UI snapshots chưa được xác minh. Bản brief không chứa đáp án Editor/ground truth.
- Native Ollama tiếp tục sử dụng `think:false`, `format:"json"`, `stream:false`, đặt `num_ctx:4096` vì context người dùng đang báo là 4096.
- Mọi timeout vẫn được lưu trace `completed:false`; evaluator không được phép chấm. Không tạo observation bằng suy đoán hoặc chép thẳng baseline vào model output.

## Cài đặt

1. Giải nén ZIP v0.7 ra thư mục bất kỳ, mở PowerShell trong thư mục chứa `Install_Fix_v07.ps1`.
2. Chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v07.ps1
```

Installer kiểm tra SHA-256 từng file, sao lưu file cũ vào `D:\ModStudioAI\Milestone03\Backups`, và chỉ cập nhật Python source, `Run_M03.ps1`, thêm tests và fixture. Không sửa `.venv`, Unity game, REA, ground truth, đầu vào Agent hay các file trong `Outputs`.

## Cách chạy — theo thứ tự

```powershell
cd D:\ModStudioAI\Milestone03

# A: Kiểm tra 80 bài test offline
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests

# B: Thử một request JSON rất ngắn với Qwen/Ollama
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode probe -Transport ollama -Server "http://127.0.0.1:11434" -Model "qwen3.5:4b" -TimeoutSeconds 120

# C: Chỉ chạy nếu ollama_probe.json có status = ok
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent -Strategy guided -Transport ollama -Server "http://127.0.0.1:11434" -Model "qwen3.5:4b" -TimeoutSeconds 600 -NumPredict 1280 -BriefChars 3900

# D: Đọc trạng thái
(Get-Content .\Outputs\qwen_agent_guided.json -Raw | ConvertFrom-Json).completed
```

**Chỉ nếu trạng thái là `True`** mới chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate -EvaluateTarget guided
```

Nếu `False`, **không chạy evaluate**. Gửi `Outputs/ollama_probe.json`, `Outputs/qwen_agent_guided.json` và log PowerShell để biết timeout/invalid_json/tool_failure.

Nếu probe hoàn thành nhưng Guided vẫn timeout, có thể thử một lần **để chẩn đoán**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent -Strategy guided -Transport ollama -Server "http://127.0.0.1:11434" -Model "qwen3.5:4b" -TimeoutSeconds 900 -NumPredict 768 -BriefChars 3900
```

Không tăng thời gian liên tục nếu request vẫn không hoàn thành; khi đó xem Ollama logs, tốc độ token và context, hoặc chia nhiệm vụ thành nhiều yêu cầu nhỏ trong milestone tiếp theo.

## Kiểm thử v0.7

- **80/80 tests**: 66 bài cũ + 14 bài mới. Tất cả chạy offline; tests mock HTTP, không chứng minh inference thực tế trên GPU Windows.
- Fixture `Fixtures/guided_v06_timeout.json` giữ lại trace lỗi v0.6 đã tải lên để tái hiện bằng chứng.
- Bản vá **không thay baseline 3 exact + 1 dynamic template + 1 unknown** và không có điểm Guided mới khi chưa chạy model trên Windows.
- Benchmark UnityTextLab trên GitHub public là functional lab, không phải tập holdout bí mật.
