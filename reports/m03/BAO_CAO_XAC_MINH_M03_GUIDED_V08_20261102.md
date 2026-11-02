# Báo cáo xác minh Milestone 03 — Qwen Guided v0.8

**Ngày:** 2026-11-02 (Asia/Ho_Chi_Minh)  
**Nguồn dữ liệu:** `Outputs.rar` và `Pasted text.txt` do người dùng tải lên, cùng mã nguồn evaluator v0.8 đang lưu trong bản vá. Dữ liệu gốc được bảo toàn theo manifest SHA-256.

## Kết quả đã kiểm chứng

- Người dùng cài `Semantic Validation Fix v0.8` thành công và chạy **96/96 tests** Windows, `OK`.
- `qwen_agent_guided.json`: `completed = true`, `strategy = guided`, **4 observations**, `trace` có một lời gọi Qwen `finish` sau controller evidence brief. Không có lỗi parse/timeout trong trace lần này.
- Evaluator mới: **exact 3/5, dynamic template 1/5, unproven 1/5**.
- Đã chạy lại evaluator từ Python v0.8 với tệp ground truth lab và chính output mới. Toàn bộ JSON kết quả **khớp về nội dung** với tệp Windows của người dùng.
- Khóa assembly REA SHA-256: `ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e`.

## Đối chiếu từng ca

| Case | Text/mẫu | Nguồn Qwen xác định | Kết quả |
|---|---|---|---|
| T001 | New Game | Không có kết luận prefab proven | `not_proven` — phù hợp mức bằng chứng hiện có |
| T002 | Load Game | `scriptable_object`, `sharedassets0.assets#path_id=16` | `exact_text` |
| T003 | Quest Completed | `hardcoded_managed`, `HardcodedTextExample.Awake` | `exact_text` |
| T004 | Health: {0}/100 | `runtime_generated`, `RuntimeTextExample.Refresh` | `template_text` |
| T005 | Hello, Commander | `external_json`, `resources.assets#path_id=9` | `exact_text` |

## So sánh v0.7 và v0.8

| Kỳ đo | Exact | Template | Chưa xác minh | Số nhận định |
|---|---:|---:|---:|---:|
| Qwen Guided v0.7 (backup trong RAR) | 3 | 0 | 2 | 8 |
| **Qwen Guided v0.8** | 3 | 1 | 1 | 4 |
| Rule-based baseline | 3 | 1 | 1 | Không áp dụng |

Nhận định quan trọng: Qwen v0.8 đã **tự ghi** `source_type=runtime_generated` cho `Health: {0}/100`. Không phải validator tự động đổi nhãn. Với mô hình Guided, tool đã tóm tắt các nguồn REA/build-only trước khi Qwen suy luận: không suy diễn rằng năng lực autonomous đã tăng.

## Giới hạn và tiêu chí dừng

1. Nhãn `observed` của CIL vẫn là **bằng chứng tĩnh cấp phương thức** (`ldstr`, `String.Format`, `TMP_Text.set_text`), chưa chứng minh toàn bộ stack dataflow và callsite được thực thi tại runtime.
2. T001 `New Game` mới có UI snapshot; không tự nhận source prefab.
3. UnityTextLab đã được công bố lên repository public cùng ground truth. Đó là **functional regression**; không dùng làm secret blind benchmark chống ghi nhớ.
4. Một lượt Guided đạt ngang baseline **không chứng minh khả năng tổng quát**. Không nên fine-tune chỉ dựa trên một game lab.
5. File `qwen_agent.json` trong RAR là kết quả Agent chế độ khác có từ lần trước; phiên đo mới phải dùng `qwen_agent_guided.json`.

## Quyết định bước tiếp theo

**Chấp nhận Milestone 03 / chức năng Guided trên 5-case UnityTextLab là đạt ngưỡng baseline** (3 exact + 1 template + 1 unknown). Chuyển sang **Milestone 04 — unseen build-only holdout**, đồng thời giữ T001 là hạng mục provenance chưa hoàn tất, không gắn nhãn đã giải được prefab.

Toàn bộ tệp gốc, SHA-256 và báo cáo so sánh nằm trong snapshot v0.8 ở GitHub MOD-KIT. Không đưa evaluator/Editor ground truth cho Qwen.
