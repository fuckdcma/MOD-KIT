# Mod Studio AI — Xác minh Qwen Guided v0.7 (2026-11-02)

## Nguồn quan sát

- Người dùng tải lên `Pasted text.txt` (log PowerShell) và `Outputs.rar` (9 JSON) sau khi chạy Milestone 03 v0.7 trên Windows.
- Đã giải nén RAR5 read-only; có `qwen_agent_guided.json`, `evaluation_private_guided.json`, `ollama_probe.json` cùng các báo cáo baseline/asset/provenance cũ.
- Kiểm tra byte SHA-256 trong `INPUT_FILE_SHA256_MANIFEST.json`. Không có yêu cầu nào được gửi từ môi trường phân tích này tới Ollama của người dùng.

## Đã xác minh

| Chỉ số | Kết quả |
|---|---|
| Windows Python tests | 80/80 theo log người dùng |
| Ollama probe | `status=ok`, 5,56 giây |
| Guided Agent | `completed=true` |
| Số observations Qwen tạo | 8 |
| Trace | 3 lượt tác vụ; 1 lượt `invalid_json, finish=length`, đã retry thành công |
| Model | `qwen3.5:4b`, Ollama localhost |
| Guided evaluation | **3 exact + 0 dynamic template + 2 unproven** |
| Static baseline cùng build | **3 exact + 1 dynamic template + 1 unproven** |

## Đối chiếu từng trường hợp

- **T001 New Game:** Không có bằng chứng prefab origin, giữ `not_proven`.
- **T002 Load Game:** Qwen tìm đúng `scriptable_object` trong `sharedassets0.assets#path_id=16`. Bằng chứng serialized pointer đã giải ở v0.4; chưa chứng minh hành vi runtime.
- **T003 Quest Completed:** Qwen tìm đúng `hardcoded_managed` ở `HardcodedTextExample.Awake`.
- **T004 Health: {0}/100:** Qwen tìm ra literal, **nhưng gán `hardcoded_managed`**, trong khi method `RuntimeTextExample.Refresh` có `System.String.Format` và `TMP_Text.set_text`, cần `runtime_generated` ở mức template. Vì vậy evaluator không tính T004.
- **T005 Hello, Commander:** Qwen tìm đúng `external_json` ở `resources.assets#path_id=9`.

Trong 8 nhận định còn có 3 chuỗi lỗi chẩn đoán và một key `menu.load`. v0.7 gắn 4 nhận định đó `candidate_only` (không chứng minh text UI). Riêng T004 từng được đánh dấu `observed` dù model phân loại sai loại nguồn. Điều này là lỗ hổng về **semantic validation**, không phải là thành tích mới.

## V0.8 — rà soát lỗi và kiểm thử hồi quy

- Bản v0.8 bổ sung điều kiện source-type consistency đối với IL literals, và hướng dẫn prompt phân biệt dynamic template / hardcoded / ScriptableObject key / chẩn đoán.
- Khi chấm lại **chính 8 observations cũ** bằng v0.8: 3 `observed`, 5 `candidate_only`, điểm giữ nguyên **3 exact + 0 template + 2 unproven**. Không tự sửa output do model tạo.
- Baseline rule-based từ REA + build v0.7 vẫn là **3 exact + 1 template + 1 unproven**.
- **96/96 Python unit tests offline đạt** (80 cũ + 16 mới), không phải benchmark live Qwen v0.8.

## Kết luận & bước tiếp

Giao tiếp Ollama và GPU đã chạy thành công, tuy nhiên Guided Qwen vẫn bỏ sót phân loại T004. Cần chạy lại v0.8 trên Windows để đo tác động của hướng dẫn; không nâng điểm từ kiểm tra offline. `T001` chỉ hiện như TMP UI snapshot, không tự nhận prefab origin. UnityTextLab là bài kiểm tra chức năng công khai, cần thêm game holdout riêng để đánh giá tổng quát. Source evidence không phải IL stack-to-setter proof hoặc runtime behavior.
