# Milestone 03 — mới nhất: TypeTree v0.2

Nguồn: các tệp do người dùng tải lên ngày 2026-11-02: `build_assets.json`, `baseline_static.json`, `evaluation_private.json`. Dữ liệu JSON gốc nằm trong repo để kiểm tra độc lập.

| Chỉ số từ Build Asset Scanner | Kết quả |
|---|---|
| Schema | `modstudio.m03.v0.2` |
| File đã quét | **6/6**, không truncated |
| MonoBehaviour | **32/32 đã giải mã** |
| TextAsset | **5/5 đã giải mã** |
| Asset observations | **7** |
| errors / raw_candidates | **0 / 0** |
| TypeTreeGenerator | import OK, loaded `6000.3.27f2`, errors_by_version rỗng |

## Nguồn phát hiện

| Text | Build evidence | Kết luận hợp lệ |
|---|---|---|
| New Game | `level0#path_id=35`, `TMPro.TextMeshProUGUI.m_text` | Có trong scene UI; **prefab origin chưa chứng minh** |
| Load Game | `level0#path_id=31`, `TMP_Text.m_text`; `sharedassets0.assets#path_id=16`, `ModStudioLab.LabStringTable.entries[0].value` | Value và ScriptableObject class đã thấy; key/reader chain cần link; evaluator hiện chưa chấp nhận |
| Quest Completed | `level0#path_id=32`, `TMP_Text.m_text` + REA `HardcodedTextExample.Awake` ldstr | Chứng minh C# hardcoded |
| Health: 75/100 | `level0#path_id=33`, TMP snapshot + REA `RuntimeTextExample.Refresh` template `Health: {0}/100` | Chứng minh *template*, không phải giá trị runtime bất biến |
| Hello, Commander | `level0#path_id=34` TMP snapshot + `resources.assets#path_id=9` TextAsset `dialogue.message` | Chứng minh external JSON TextAsset |

**Không được quy nguồn** cho scene-stored `m_text` nếu giá trị cuối cùng do method runtime hoặc ScriptableObject cập nhật.

## Private evaluation (log công cụ)

- `exact_text_and_source_proven=2` (T003, T005)
- `format_template_and_source_proven=1` (T004)
- `unproven=2` (T001, T002).

T001 và T002 đã xuất hiện dưới dạng text *trong build*, nhưng `source_type='unknown'`, không đủ để sửa điểm chấm. Kết quả là **tool baseline**, không phải điểm của mô hình Qwen.

## Công việc kế tiếp

1. Nối ScriptableObject asset → `LabStringTable.TryGet` key → `TableTextExample.Start` → TMP object, kiểm chứng T002.
2. Truy vết prefab source, scene instance relationship và object identity cho T001; có thể không khôi phục đầy đủ original prefab path từ bản build.
3. Đưa schema provenance, evidence refs, confidence vào one canonical report; giữ `unknown` khi thiếu bằng chứng.
4. Chuẩn bị local llama-server Vulkan, Qwen3.5-4B GGUF, benchmark agent không nhìn reference.


## Phát triển tiếp theo — v0.3 (code test offline, chưa có scan Windows)

- [Source v0.3](../source/m03_provenance_v03/) được kiểm thử với **22/22 tests** (12 cũ, 10 mới). Mock TypeTree/UnityPy synthetic nhằm chứng minh chính sách không tự nâng score khi thiếu key; **không phải bằng chứng đã chạy UnityPy v0.3 trên build thật**.
- v0.3 `scan-assets` thu `metadata.entry_key` khi có cùng entry `entries[N].key/value` và class `ModStudioLab.LabStringTable`, cùng `reader_bindings` của `TableTextExample` nếu tìm thấy.
- `provenance_links.json` tách `source_key_value_observed` và trạng thái `reader...pointer_unresolved`; vẫn không cho phép gán `serialized_prefab` chỉ từ `level0#path_id=35`.
- Trên **JSON v0.2 thực** đã có, chạy lại baseline bằng code v0.3 vẫn cho **2 exact + 1 template + 2 unproven**. Cần quét lại trên PC để kiểm tra T002. Chưa chạy Qwen.
- PowerShell evaluator mặc định chấm baseline, không tự ưu tiên file Qwen cũ; `-EvaluateTarget agent` là tùy chọn rõ ràng.

[Tải bản vá](../archives/ModStudioAI_M03_Provenance_Fix_v03.zip) · [Báo cáo](../reports/m03/BAO_CAO_M03_V03.md).
