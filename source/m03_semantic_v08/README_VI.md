# Mod Studio AI M03 — Semantic Validation Fix v0.8

Ngày: 2026-11-02. Bản vá **sau** kết quả Guided Agent v0.7, không phải một điểm AI mới.

## Kết quả đã quan sát từ Windows v0.7

- 80/80 unit tests tại PC, Ollama probe `status=ok` (5,56 giây).
- Qwen3.5:4b Guided `completed=true`, 8 nhận định. Evaluator: **3 exact + 0 template + 2 unproven**.
- T002 `Load Game` ScriptableObject, T003 `Quest Completed` hardcoded CIL, T005 `Hello, Commander` external JSON đều đúng.
- T004 `Health: {0}/100` có trong CIL và `String.Format` nhưng Qwen gắn **hardcoded_managed**: sai phân loại. T001 prefab origin chưa có chứng cứ.
- 4 nhận định khác là 3 chuỗi chẩn đoán và `menu.load`; không thể coi là văn bản UI.
- Lượt 2 có `invalid_json` `finish=length` rồi thử lại; cuối cùng `completed=true`.

## Bản vá làm gì

1. **Chốt tính nhất quán kiểu nguồn từ IL:** literal format (vd `HP: {0}`), khi trong method cũng có `System.String.Format` + `TMP_Text.set_text`, **không chấp nhận `hardcoded_managed` là observed**. Đánh dấu `candidate_only` và đưa lý do. Ngược lại, `runtime_generated` chỉ được nhận ở mức method-level khi có định dạng và formatter; KHÔNG tự gắn nhãn thay model.
2. **Bổ sung quy tắc phân tích cho Guided Qwen:** tách template runtime khỏi hardcoded, phân biệt key dùng tra bảng với text, bỏ chuỗi log/diagnostic khỏi danh sách UI đã chứng minh; trả lời ngắn hơn để giảm JSON bị cắt.
3. **Đổi thông báo CLI `evaluate`:** in ra `total_cases`, `exact_text_and_source_proven`, `format_template_and_source_proven`, `unproven` thay vì dòng `observations: 0` gây hiểu nhầm.
4. Giữ nguyên `Run_M03.ps1`, API Ollama, timeout 600s, num_predict 1280, context4096, build scanner, REA và evaluator. Không chạm `Outputs` hoặc ground truth.

### Cảnh báo phương pháp

- `String.Format` và setter cùng method chưa chứng minh dataflow IL tới TMP. `observed` nghĩa là có bằng chứng tĩnh cấp method, **không phải UI runtime verified**.
- Không sửa lại điểm v0.7. Phân tích offline lại chính 8 nhận định cũ bằng v0.8 vẫn **3+0+2**, nhưng T004 sai kiểu được hạ về `candidate_only` thay vì `observed`.
- Các bài test là Python (không phải Qwen inference thực tế). Thư mục GitHub public chứa ground truth của lab; điểm hiện là chức năng lab, không phải secret blind benchmark.

## Cài trên máy Windows 11

Giải nén ZIP vào thư mục bất kỳ, mở PowerShell tại thư mục chứa `Install_Fix_v08.ps1`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v08.ps1
```

Installer xác minh SHA-256, sao lưu file gốc và chỉ thay `src/modstudio_m03.py`, thêm `tests/test_semantics_v08.py`. Không cài lại Python, Qwen hay Unity.

Vào project và chạy tests:

```powershell
cd D:\ModStudioAI\Milestone03
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
```

**Trước khi chạy Agent mới, sao lưu kết quả v0.7:**

```powershell
New-Item -ItemType Directory -Force .\Outputs\History | Out-Null
Copy-Item .\Outputs\qwen_agent_guided.json .\Outputs\History\qwen_agent_guided_v07.json -Force
Copy-Item .\Outputs\evaluation_private_guided.json .\Outputs\History\evaluation_private_guided_v07.json -Force
```

Chạy lại model (sẽ dùng bằng chứng `Outputs\build_assets.json` hiện có, không cần scan lại):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent -Strategy guided -Transport ollama -Server 'http://127.0.0.1:11434' -Model 'qwen3.5:4b' -TimeoutSeconds 600 -NumPredict 1280 -BriefChars 3900
(Get-Content .\Outputs\qwen_agent_guided.json -Raw | ConvertFrom-Json).completed
```

Chỉ nếu thấy `True`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate -EvaluateTarget guided
Get-Content .\Outputs\evaluation_private_guided.json -Raw | ConvertFrom-Json | Select-Object exact_text_and_source_proven, format_template_and_source_proven, unproven
```

Gửi `qwen_agent_guided.json`, `evaluation_private_guided.json`, log PowerShell. So sánh T004 quan trọng hơn là chỉ nhìn tổng điểm. Nếu không `completed=true`, gửi trace, không đánh giá.

## Giới hạn

Bản v0.8 **chưa chạy với Ollama trên Windows**. Đã kiểm thử offline bằng suite tích hợp 96/96. Báo cáo replay trong `Reports/REPLAY_V07_WITH_V08_REVALIDATION.json` không phải kết quả suy luận mới.
