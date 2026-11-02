# Mod Studio AI — M03 Evidence-Guided Qwen Agent v0.6

Ngày 2026-11-02. Bản này dựa trên source **v0.5 chạy thành công trên Windows** nhưng cho điểm Agent 1 exact / 0 template / 4 unproven. Không thay Unity build, REA, UnityPy hoặc Qwen model.

## Vì sao cần v0.6?

Qwen 3.5 4B qua Ollama 100% GPU đã trả `completed=true` với 2 observations: `Quest Completed` và một **chuỗi báo lỗi** `[ModStudioLab] HardcodedTextExample: missing label.`. Trace chỉ 3 bước (search Quest → inspect Hardcoded → finish). Agent dừng trước khi đọc bằng chứng `Load Game`, `Health: {0}/100`, và `Hello, Commander`. Evaluator đã chấm chính xác **1/5 exact, 0 template, 4/5 not proven**. Đây là điểm của lần chạy này, không phải năng lực Qwen nói chung.

## Hai chiến lược được giữ riêng

- **guided (mặc định v0.6)**: controller tổng hợp bằng chứng *từ REA và các asset build đã quét* thành brief gọn đủ 4096 context. Nguồn được đánh dấu source-qualified: ScriptableObject có cặp key/value và Resources TextAsset. Chuỗi `TMP_Text.m_text` chỉ đưa dưới danh mục snapshot không đủ provenance; phương thức CIL được tổng hợp kèm lời gọi setter và literal; model vẫn chịu trách nhiệm **phân loại và sinh observations**, controller không tự điền kết quả. Model vẫn có thể gọi tools để điều tra thêm.
- **autonomous**: dùng chế độ tự chọn tool như v0.5 để đo khả năng tìm kiếm tự chủ. Chế độ này có thể kết thúc sớm; **không được trộn điểm của hai chiến lược vào một phép so sánh khả năng reasoning**.

Đầu vào gồm REA + Build Asset Scanner; không có `PrivateEvaluation/ground_truth`, dữ liệu Editor hay file báo cáo nguồn. Đây là bài lab **công khai** trên GitHub nên không phải holdout mù thực sự.

## Kiểm chứng tĩnh và bảo vệ kết luận

- `validate_observations` giữ hardcoded method-level evidence cho literal và setter, **không khẳng định IL stack-to-setter dataflow**.
- Một literal mang hình thức chẩn đoán (ví dụ `[ModStudioLab] ... missing ...`) được gắn `validation_status=candidate_only`, chưa chấp nhận là text UI. Đây là heuristic thận trọng, có thể cần kiểm tra IL sâu hơn.
- Source type `serialized_prefab` không thể được xác minh chỉ từ `TMP_Text.m_text` trong `level0`.
- Kết quả v0.5 qua validator v0.6 vẫn **1 exact / 0 template / 4 unproven**. Baseline công cụ từ bản build thật vẫn **3 exact + 1 template + 1 unknown**.

## Cài đặt trên Windows

Giải nén ZIP, mở PowerShell ở thư mục chứa `Install_Fix_v06.ps1`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v06.ps1
```

Installer xác minh SHA-256, sao lưu `src/modstudio_m03.py` và `Run_M03.ps1` vào thư mục Backups, chỉ thêm `tests/test_guided_v06.py`. Không cài lại Python hoặc model; **không thay hay xóa Outputs cũ**.

```powershell
cd D:\ModStudioAI\Milestone03
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent -Strategy guided -Server 'http://127.0.0.1:11434' -Model 'qwen3.5:4b' -Transport ollama
(Get-Content .\Outputs\qwen_agent_guided.json -Raw | ConvertFrom-Json).completed
```

**Chỉ khi `completed=True`** chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate -EvaluateTarget guided
```

Các file mới không ghi đè Qwen v0.5:

- `Outputs/qwen_agent_guided.json`
- `Outputs/evaluation_private_guided.json`

Để thử tự chọn tools riêng, dùng `-Mode agent -Strategy autonomous ...`, xuất `qwen_agent_autonomous.json`, và chấm `-EvaluateTarget autonomous`.

## Kiểm thử trong môi trường hiện tại

- Chạy **66/66 bài kiểm thử Python đạt** (51 bài trước và 15 bài v0.6). Có mock transport và synthetic evidence, không có lần suy luận Qwen v0.6 thật trên GPU của bạn.
- Đã chạy baseline và replay điểm v0.5 từ JSON bạn gửi, giữ nguyên 3 exact + 1 template + 1 unknown cho baseline, 1 exact + 0 template + 4 unproven cho Agent cũ.
- Hiện *chưa có điểm mới của guided mode*. Cần bạn chạy lệnh trên máy Windows rồi gửi `qwen_agent_guided.json`, `evaluation_private_guided.json` (hoặc nén Outputs) để xác minh.

## Giới hạn

Guided mode có thể cải thiện độ phủ vì controller cung cấp bản tóm tắt chứng cứ. **Nếu điểm tăng, nó là hiệu quả của mô hình + chiến lược điều phối**, không chứng minh model đã biết tự tìm kiếm độc lập. Với bộ dữ liệu công khai, không thể công bố số này là AI blind accuracy. Cần thêm lab holdout riêng chưa rò rỉ đáp án cho benchmark nghiêm ngặt.
