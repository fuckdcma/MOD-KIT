# Milestone 03 — Kiểm chứng Qwen v0.5 và phân tích nguyên nhân

Ngày: 2026-11-02. Nguồn: `Outputs.rar` người dùng vừa gửi, chứa 6 file JSON; log PowerShell chạy 51/51 tests, Agent completed=true.

## Chỉ số từ JSON gốc

| Kết quả | Giá trị |
|---|---|
| Model (từ log) | `qwen3.5:4b`, Ollama localhost, GPU 100% trong lần đo trước |
| Agent v0.5 | `completed=true`, 2 observations, 3 bước |
| Qwen v0.5 | **1/5 exact + 0/5 template + 4/5 not_proven** |
| Rule-based static baseline | **3/5 exact + 1/5 template + 1/5 not_proven** |
| Unity build scan | 6/6 files, 32/32 MonoBehaviour, 5/5 TextAsset, 0 errors, 1 serialized pointer resolved |

Qwen v0.5 gọi lần lượt `search_literals('Quest')` → `inspect_method('ModStudioLab.HardcodedTextExample.Awake')` → `finish`. Hai observations:

1. `Quest Completed`: đúng chuỗi CIL của `HardcodedTextExample.Awake`, được validator chấp nhận và evaluator tính T003.
2. `[ModStudioLab] HardcodedTextExample: missing label.`: cũng là CIL literal trong phương thức, nhưng là chuỗi lỗi chẩn đoán; **không chứng minh có đường dữ liệu đi vào TextMeshPro setter**. Validator v0.5 chấp nhận literal ở mức phương thức, gây nguy cơ đếm nhầm khi báo cáo toàn bộ text phát hiện.

## Phân biệt bản chất lỗi

- **Không phải lỗi giao thức:** native API Ollama đã phản hồi JSON hợp lệ và Agent hoàn thành.
- **Lỗi độ phủ điều tra:** Agent tự dừng sau 1 phương thức, không đọc nguồn ScriptableObject, TextAsset, dynamic template.
- **Giới hạn bằng chứng:** REA method-level ldstr + setter chưa đủ chứng minh IL stack-to-setter dataflow. Không tự quảng cáo literal báo lỗi là text UI.
- **T001 vẫn chưa chứng minh nguồn prefab**, ngay cả khi build chứa `New Game` trong UI snapshot.

## Biện pháp v0.6

- `guided` mode: phát bản tổng hợp toàn bộ nhóm nguồn hợp lệ từ build+REA cho model, trong context 4096. Công cụ không tự điền observations.
- `autonomous` mode: giữ v0.5 để tiếp tục đánh giá khả năng model chọn tool độc lập.
- Heuristic `candidate_only` cho log/error literals; không coi nó là UI source trước khi truy vết dataflow.
- 66/66 Python tests pass; **chưa chạy Qwen guided v0.6 thực tế trên PC**.

Lưu ý: điểm tăng nhờ guided không tương đương Qwen tự khám phá. Dataset UnityTextLab ở repo PUBLIC; cần holdout riêng cho đánh giá khả năng tổng quát.
