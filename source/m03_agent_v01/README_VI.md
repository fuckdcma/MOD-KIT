# Mod Studio AI — Milestone 03: Local Research Agent v0.1

## Mục đích

Chạy thử năng lực tìm **nguồn text** chỉ từ bằng chứng bản build, không cho AI đọc mã nguồn Unity hoặc `ground_truth`. Giai đoạn này **không tạo hook, không dịch thuật, không train Qwen và không chỉnh sửa game**. Các bản mod về sau vẫn phải tự chứa, không dùng BepInEx.

**Đã thử nghiệm tại môi trường tạo gói:** bộ dữ liệu REA đã có của UnityTextLab, 6/6 bài test Python. **Chưa thử nghiệm:** Qwen thật trên PC của bạn, UnityPy với Unity 6.3 trên build đầy đủ và GPU Vulkan.

## Thao tác ngay (không cần tải model)

1. Giải nén ZIP vào `D:\ModStudioAI\Milestone03`.
2. Mở PowerShell trong thư mục vừa giải nén.
3. Chạy lệnh:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode baseline
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate
   ```

4. Kiểm tra `Outputs\baseline_static.json` và `Outputs\evaluation_private.json`.

Baseline mẫu đi kèm dùng kết quả REA **thực tế** từ project bạn đã gửi, không có đáp án chuẩn trong đầu vào. Nó chứng minh chính xác 1/5 giá trị nguồn (`Quest Completed`) và một mẫu động 1/5 (`Health: {0}/100`); ba trường hợp còn lại **chưa xác minh**. Đây là **baseline không dùng AI**, không phải kết quả đánh giá Qwen.

## Phân tích lại REA sau khi build game mới

Nếu bạn đã tạo bản build UnityTextLab mới, xuất hai JSON bằng REA như trước rồi chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode prepare
```

Kết quả: `Outputs\rea_evidence_new.jsonl`. Nó giữ method, SHA-256 assembly, lệnh `ldstr` và các cạnh call từ `members.json`. **Không được** trộn dữ liệu chuẩn từ Unity Editor vào file này.

Muốn dùng evidence mới: chạy trực tiếp:

```powershell
py -3 .\src\modstudio_m03.py baseline --rea .\Outputs\rea_evidence_new.jsonl --out .\Outputs\baseline_new.json
```

## Đọc asset đã đóng gói (thử nghiệm, tùy chọn)

Việc chỉ đọc CIL không thể chứng minh text nằm trong prefab/ScriptableObject/JSON. Thử đọc Unity asset trong bản build:

```powershell
py -3 -m pip install UnityPy
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
```

Kết quả: `Outputs\build_assets.json`. **Cảnh báo:** UnityPy có thể không parse được một số bản Unity 6, stripped type tree hay custom serialization. Không có kết quả **không đồng nghĩa** game không chứa text. Bản quét này chỉ đọc file, giới hạn mặc định 40 file × 128MB mỗi file; không xác định chắc tên prefab/scene gốc từ bản build. Hãy gửi `build_assets.json` nếu nó có errors để nâng cấp parser.

## Chạy Qwen local — sau khi có GGUF và llama.cpp

Bạn cần **tự tải** một bản model Qwen GGUF đáng tin cậy và `llama-server.exe` có backend Vulkan hỗ trợ card AMD. Gói này **không chứa model**. Theo tài liệu llama.cpp, server có API OpenAI-compatible `/v1/chat/completions` và JSON-constrained output.

Ví dụ trong PowerShell (thay đường dẫn thật):

```powershell
& "D:\AI\llama.cpp\llama-server.exe" -m "D:\ModStudioAI\Models\qwen-4b.gguf" -c 4096 -ngl 99 --host 127.0.0.1 --port 9931
```

Mở cửa sổ PowerShell **thứ hai**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate
```

Kết quả: `Outputs\qwen_agent.json` có hành động AI, quan sát, trạng thái `observed`/`hypothesis`/`rejected`, còn `evaluation_private.json` chứa điểm chấm riêng. Mặc định agent kết nối **127.0.0.1**, không gọi API cloud. Nếu localhost chưa chạy hoặc model phản hồi sai định dạng, file trace ghi lỗi; không có chế độ tự nhận vơ kết quả thành công.

**Quan trọng:** Qwen có thể không trả JSON đúng schema hoặc không hoàn tất trong 10 lượt; đây chính là điều phải đo trong baseline. Không coi đó là lỗi của REA.

## Không để lộ ground truth

- `AgentInput/` chứa duy nhất dữ liệu REA được phép đọc khi đánh giá.
- `PrivateEvaluation/` chứa đáp án và phải giữ **ngoài** RAG, prompt, training, thư mục mà AI agent truy cập.
- Khi công bố dataset sau này, tách theo game/build: tránh lẫn phương thức gần như giống nhau giữa train và test.
- Dữ liệu do Unity Editor xuất ra là bản tham chiếu; tuyệt đối **không** đưa vào prompt đầu vào của bài kiểm thử mù.

## Cần gửi lại

Sau khi làm ba lệnh đầu, gửi `Outputs\baseline_static.json` và `Outputs\evaluation_private.json`. Khi đã sẵn sàng chạy Qwen, gửi thêm `Outputs\qwen_agent.json` và `Outputs\build_assets.json` (nếu quét thành công). Không cần upload toàn bộ game lên Drive.

## Mốc nghiệm thu M03

1. REA được dùng như nguồn evidence từ build chứ không dùng source Unity.
2. Không chấp nhận chuỗi do model bịa: các `il_literal` không tìm thấy sẽ thành `rejected`.
3. Các câu không có chứng cứ giữ `not_proven`.
4. Chạy được local model qua endpoint loopback sau khi người dùng cài runtime/model.
5. Báo cáo đánh giá độc lập không đi vào prompt.

Đây là nguyên mẫu nghiên cứu M03, **chưa phải Studio Windows GUI hay hệ thống hook game 1:1**.