# Kết quả xác minh Milestone 03 v0.3 — 2026-11-02

**Nguồn dữ liệu:** `Outputs.rar` do người dùng cung cấp; bốn file `build_assets.json`, `provenance_links.json`, `baseline_static.json`, `evaluation_private.json` được trích xuất từ archive RAR 5. Đây là dữ liệu mới nhất của **UnityTextLab Unity 6000.3.27f2 / Mono**.

## Tổng quan

- Schema thống nhất: `modstudio.m03.v0.3`.
- 6/6 build files scanned; `truncated=false`.
- 32/32 MonoBehaviour, 5/5 TextAsset giải mã; 7 asset text records; 1 reader binding; 0 errors; 0 raw candidates.
- TypeTreeGenerator đã nạp phiên bản Unity `6000.3.27f2` và không ghi lỗi.
- Private evaluator: **3 exact source+text (T002/T003/T005), 1 template (T004), 1 not proven (T001)**.
- Chạy lại offline `provenance`, `baseline`, `evaluate` bằng mã v0.3, evidence REA và ground truth của laboratory: **ba JSON đầu ra khớp hoàn toàn với ba file được gửi**. Chạy lại 22/22 unittest Python đạt. Việc này không thay thế kiểm thử scanner trên PC; scan thực tế được người dùng cung cấp trong archive.

## Năm trường hợp

| Case | Bằng chứng | Kết luận đúng phạm vi |
|---|---|---|
| T001 `New Game` | `level0#path_id=35`, `TMPro.TextMeshProUGUI.m_text` | UI serialized snapshot; **chưa có chứng cứ bản build khôi phục prefab origin**; không tăng điểm |
| T002 `Load Game` | `sharedassets0.assets#path_id=16`, `ModStudioLab.LabStringTable`, `entries[0].key=menu.load` + `entries[0].value=Load Game` | Chứng minh source ScriptableObject key/value, **chưa chứng minh PPtr instance runtime binding** |
| T003 `Quest Completed` | REA IL literal trong `ModStudioLab.HardcodedTextExample.Awake` | Hardcoded managed source proven |
| T004 `Health: {0}/100` | REA IL literal trong `ModStudioLab.RuntimeTextExample.Refresh` | Dynamic format/template proven; không giả định số HP cố định |
| T005 `Hello, Commander` | `resources.assets#path_id=9` TextAsset field `message` | Source text từ external JSON proven |

## T002 — liên kết chưa hoàn tất

Trong `build_assets.json` có reader cấu hình `ModStudioLab.TableTextExample` tại `level0#path_id=40`, key `menu.load`, con trỏ 
`{"m_FileID":3,"m_PathID":16}`. Đối tượng bảng key/value đúng hiện tại là `sharedassets0.assets#path_id=16`. Nhưng 
`reader_bindings[0].binding_status = unresolved_build_pointer`, vì chưa truy m_FileID qua **external file references table của chính serialized file `level0`**. Chỉ so sánh `m_PathID` và key là không đủ để kết luận cùng asset. Chỉ khi `externals[3-1]` xác định chính xác đích `sharedassets0.assets`, rồi kiểm tra path_id + class + key trên đúng file thì mới đánh dấu `serialized_pointer_resolved`.

Ngay cả khi con trỏ trong build được xác minh, điều đó chỉ chứng minh **serialized configuration tại thời điểm build**, chưa chứng minh luồng hoạt động runtime không bị thay đổi.

## Phân biệt trạng thái bằng chứng

- `source_key_value_observed`: bằng chứng tồn tại bản ghi key/value thật trong build.
- `lookup_call_and_key_supported_pointer_unresolved`: REA tìm thấy đường gọi `TryGet` đến TMP setter, reader key trùng, nhưng con trỏ vẫn chưa giải xong.
- `ui_snapshot_only`: giá trị `m_text` không tự chứng minh dữ liệu bắt nguồn từ prefab hay nguồn khác.

## Nhiệm vụ tiếp theo

1. Nâng cấp scanner đọc `SerializedFile.externals` và xác minh pointer `m_FileID / m_PathID` theo file nguồn. Không suy đoán external ref từ basename trùng tình cờ. Kết quả phải kèm `source_file`, index, external path và target object.
2. Giữ T001 `not_proven` trong build-only benchmark. Nếu cần chứng minh serialized prefab gốc, phải bổ sung bằng chứng prefab relationship hoặc thí nghiệm chuyên biệt; dùng reference Editor **chỉ trong evaluator**, không dùng làm đầu vào agent.
3. Khi có provenance chain đủ mạnh, mới chạy Qwen nền local và đo riêng điểm `rule baseline` vs `AI result`.

## Bảo toàn nguồn

Các tệp JSON gốc được lưu trong `evidence/m03/runs/20261102_v03/`, evaluation được đặt tại `benchmarks/reference_DO_NOT_FEED_MODEL/m03/runs/20261102_v03/`. Repo công khai nên việc tách thư mục **không tạo quyền riêng tư hay bảo đảm test mù**.

## SHA-256 tệp JSON gốc

| Tệp | SHA-256 |
|---|---|
| `baseline_static.json` | `2bbca7cdbe793fdebae4e63f471b5613917f80125b250e8ce4ebe83bce94065e` |
| `build_assets.json` | `b27ab1d62c5a100a7897a138a694b86d41e36bef9b53ef81babd2aadef5895dc` |
| `evaluation_private.json` | `ca8c636bd1227aca727ab94ec1d68cc4839a795a6e48af3f45600d2724858a1e` |
| `provenance_links.json` | `ba28e76b2493a39a3bf00716f3f72e09e773fa90bc102d324891f6c63e56d91f` |