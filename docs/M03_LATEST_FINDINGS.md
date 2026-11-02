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


## Đã xác minh đầu ra Windows v0.3 (2026-11-02)

Kết quả thực tế do người dùng cung cấp trong `Outputs.rar` đã giải nén và lưu nguyên văn vào [evidence/m03/runs/20261102_v03](../evidence/m03/runs/20261102_v03/), [private evaluator](../benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_v03/evaluation_private.json) và [báo cáo](../reports/m03/BAO_CAO_XAC_MINH_M03_V03_20261102.md).

- 6/6 files, 32/32 MonoBehaviour, 5/5 TextAssets, 0 parser errors, 7 assets, 1 reader binding.
- **T002 now source+key+value proven**: `ModStudioLab.LabStringTable`, `entries[0].key=menu.load`, `entries[0].value=Load Game`, `sharedassets0.assets#path_id=16`. REA sees `TableTextExample.Start → LabStringTable.TryGet → TMP_Text.set_text` but **serialized pointer unresolved** (`m_FileID=3,m_PathID=16`).
- T001 still **not_proven** as prefab source; a scene TMP snapshot isn't prefab-origin proof.
- evaluator **3 exact + 1 template + 1 unproven** (tool, not Qwen); independently reproduced with Python v0.3.


## Hướng nghiên cứu tiếp — v0.4 (code verified, Windows scan pending)

Bản v0.4 đã được đóng gói: [Source](../source/m03_pointer_v04/), [ZIP](../archives/ModStudioAI_M03_PointerResolver_Fix_v04.zip), [Báo cáo](../reports/m03/BAO_CAO_M03_V04.md). **34/34 unit tests đạt**; chưa có kiểm chứng với bản build Unity 6.3 qua scanner v0.4. Nâng cấp đọc `SerializedFile.externals` theo `m_FileID - 1`, đối chiếu `m_PathID`, class `LabStringTable`, cặp key/value, file basename duy nhất; nếu thiếu, không nâng trạng thái. Score v0.3 người dùng đã tải lên vẫn **3 exact + 1 template + 1 not proven**, không phải Qwen. T001 serialized prefab origin chưa chứng minh.


## Latest verified Windows run — Pointer Resolver v0.4 (2026-11-02)

**v0.4 no longer pending.** [Source scan JSON](../evidence/m03/runs/20261102_v04/build_assets.json) and [provenance graph](../evidence/m03/runs/20261102_v04/provenance_links.json) now show a **real scanner-produced serialized pointer resolution**, under conservative validation:

- `reader_ref=level0#path_id=40`, `m_FileID=3, m_PathID=16`, `external_index=2`, `external_path=sharedassets0.assets`, `resolved_target_ref=sharedassets0.assets#path_id=16`, class `ModStudioLab.LabStringTable`, key `menu.load`.
- `binding_status=serialized_pointer_resolved`; `proof_kind=build_serialized_pointer_not_runtime_behavior`.
- 6/6 build files; 32/32 MonoBehaviour, 5/5 TextAsset; 0 scanner errors, 1 resolved pointer, 7 asset records.
- v0.4 score **3 exact / 1 template / 1 unproven (T001)**; no Qwen test, no runtime hook. T002 source was already counted as exact v0.3; v0.4 improves proof quality.
- Independent local reproduction of `provenance_links.json`, `baseline_static.json`, `evaluation_private.json`: semantic JSON matches 3/3, 34/34 unit tests pass. Uploads use CRLF; regenerated files use LF. SHA-256 manifest included.
- [RAR original](../raw_uploads/Outputs_M03_v04_20261102.rar), [report](../reports/m03/BAO_CAO_XAC_MINH_M03_V04_20261102.md). Respect public repository exposure of evaluation reference.


## Current Qwen local integration (2026-11-02)

- `ollama ps` confirmed Qwen3.5 4B 100% GPU, 3.1GB, context4096.
- First agent run ended at step2 JSON parse (empty/non-JSON content), `completed=false`; no observations. [Trace](../evidence/m03/runs/20261102_ollama_first/qwen_agent.json). `evaluation_private_agent.json` 0/5 is invalid to interpret as performance.
- [v0.5 native Ollama transport fix](../source/m03_ollama_fix_v05/) tested 51/51 offline; old v0.4 static baseline unchanged. New code switches to `/api/chat` `think:false` `format:'json'` when server port=11434. OpenAI endpoint still supported for localhost llama-server 9931.
- **Live Windows Qwen retest pending**; no Qwen intelligence score yet. Tool baseline stays 3 exact + 1 dynamic template + 1 unknown (T001).
