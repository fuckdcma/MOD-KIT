# Mod Studio AI — M03 Ollama Agent Fix v0.5

**Ngày:** 2026-11-02. Sửa đúng lỗi bước 2 từ đầu ra Qwen local `qwen_agent.json` của người dùng, không thay đổi các thuật toán REA, UnityPy, provenance hoặc ground truth.

## Dữ liệu gốc xác nhận

- `ollama ps`: `qwen3.5:4b`, 100% GPU, 3.1 GB, context 4096, runner llamacpp.
- `qwen_agent.json`: `completed=false`, step 1 search_literals(`text`) có 2 kết quả, step 2 lỗi `Expecting value: line 1 column 1 (char 0)`; không có observation.
- `evaluation_private_agent.json`: 0 exact, 0 template, 5 unproven **do Agent chưa hoàn tất, không phải điểm chất lượng Qwen**.
- `evaluation_private.json`: baseline công cụ 3 exact + 1 template + 1 chưa chứng minh. `build_assets.json`: 6/6 files, 32/32 MonoBehaviour, 5/5 TextAsset, 1/1 pointer resolved, 0 scanner errors.

## Nguyên nhân và cách sửa

Trước v0.5, ứng dụng chỉ dùng OpenAI-compatible `/v1/chat/completions` trên Ollama, không tắt `thinking`; `json.loads(message.content)` báo lỗi nếu content rỗng/không hợp lệ. Lỗi này **phù hợp** với trường hợp output bị dành cho thinking hoặc sinh không xong; chỉ có thể xác minh nguyên nhân cụ thể trên PC bằng raw API metadata. Không lưu reasoning riêng tư vào log.

- Mặc định `-Server http://127.0.0.1:11434` → **native Ollama `/api/chat`** với `think:false`, `format:'json'`, `stream:false`.
- Mặc định `-Server http://127.0.0.1:9931` → **OpenAI-compatible `/v1/chat/completions`** để giữ tương thích llama.cpp.
- Tham số `-Transport auto|ollama|openai` có thể ghi đè nếu dùng cổng khác. Chỉ kết nối localhost, không gửi dữ liệu cloud.
- Kiểm tra JSON object và action hợp lệ; tối đa 2 lần retry có chỉ dẫn sửa; trace chỉ lưu mã lỗi, không lưu reasoning/model output thô.
- Giới hạn mỗi tool result 4500 ký tự cho context 4096. Tham số `-Steps 12` có thể điều chỉnh.
- Nếu `completed:false`, bộ chấm từ nay **từ chối chấm** thay vì đưa ra tỷ lệ 0/5 sai ý nghĩa. File cũ không bị thay đổi.

## Cài đặt trên Windows

Giải nén ZIP và mở PowerShell tại thư mục có `Install_Fix_v05.ps1`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v05.ps1
```

Bản vá tự kiểm tra SHA-256 của ba file nguồn trước khi chép, sao lưu file cũ vào `D:\ModStudioAI\Milestone03\Backups`; không xóa `.venv`, REA, Unity build, outputs hoặc dữ liệu đánh giá.

## Chạy Qwen local

Giữ Ollama đang chạy. Không cần cài thêm Python, UnityPy, llama-server hay tải model lại.

```powershell
cd D:\ModStudioAI\Milestone03

powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests

powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent -Server 'http://127.0.0.1:11434' -Model 'qwen3.5:4b'
```

Kiểm tra `Outputs\qwen_agent.json`. **Chỉ khi** `completed:true` mới chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate -EvaluateTarget agent
```

Tạo `Outputs\evaluation_private_agent.json`. Kết quả này chỉ đo **chương trình Agent + model trên bài test công khai**, không đo năng lực khái quát trên game khác.

## Nếu Agent vẫn chưa hoàn tất

Gửi `Outputs\qwen_agent.json` và log PowerShell. Trace giờ sẽ có `model_response_error` với `empty_content`, `invalid_json`, `invalid_action` hoặc `transport_error`. Model local có thể cần tăng context hoặc giảm nội dung mỗi lượt, nhưng **đừng thay thông số ngẫu nhiên trước khi xem trace**.

Để thử riêng API native Ollama (không chạy Agent):

```powershell
$body = @{ model='qwen3.5:4b'; messages=@(@{role='user';content='Trả về JSON có action là finish và observations rỗng.'}); think=$false; format='json'; stream=$false } | ConvertTo-Json -Depth 8
$r = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11434/api/chat' -ContentType 'application/json' -Body $body
$r.message.content
```

Nếu kết quả in một JSON object hợp lệ, kênh Ollama native chạy đúng.

## Kết quả đã kiểm thử trong môi trường phát triển

- **51/51 Python unit tests đạt**, gồm 34 tests v0.4 và 17 tests giao tiếp Ollama v0.5; tất cả dùng mock, chưa có truy cập Ollama trên máy của người dùng.
- Khi chạy lại `baseline` với chính `build_assets.json` mới tải lên, output **khớp chính xác về JSON** với baseline v0.4. Không thay đổi kết luận provenance của T001/T002.
- Chưa khẳng định `qwen_agent.json` sẽ `completed:true` cho tới khi thử trên PC Windows.

## Nguyên tắc dữ liệu

REА/Build only cho Agent; `PrivateEvaluation`, `ground_truth` và `Unity Editor` chỉ cho evaluator. Repo GitHub MOD-KIT là **public** nên case UnityTextLab không phải blind benchmark bảo mật.
