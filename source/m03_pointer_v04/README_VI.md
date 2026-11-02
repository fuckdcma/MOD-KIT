# Mod Studio AI — Milestone 03 / Cross-file PPtr Resolver v0.4

Ngày: 2026-11-02. **Bản vá dành cho UnityTextLab (Unity 6000.3.27f2 Mono)**, dùng với `D:\ModStudioAI\Milestone03` đã chạy v0.3. Đây **không phải** mod runtime.

## Vì sao cần bản vá?

Với `Outputs.rar` từ v0.3 do người dùng gửi, chúng ta xác minh được `LabStringTable` chứa `entries[0].key = menu.load`, `entries[0].value = Load Game` trong `sharedassets0.assets#path_id=16`. REA chứng minh `TableTextExample.Start` gọi `LabStringTable.TryGet` và `TMP_Text.set_text`.

Nhưng reader `level0#path_id=40` chứa 
`table: { m_FileID: 3, m_PathID: 16 }` vẫn được đánh dấu **unresolved_build_pointer**. Trong Unity, `m_FileID` chỉ có nghĩa khi đối chiếu bảng **externals** của đúng serialized file đang chứa reader; so sánh PathID hoặc string giống nhau là chưa đủ.

Bản v0.4 thêm **pointer_file_lookup** đọc `obj.assets_file.externals[m_FileID-1]`, kiểm tra file name duy nhất trong các build assets đã quét, rồi nối **đúng target ref + PathID + class `LabStringTable` + paired key**. Với `m_FileID=0`, kiểm tra target trong cùng file. Nếu thiếu external map hoặc tham chiếu không nhất quán, status vẫn `unresolved_build_pointer`; tuyệt đối không tự đoán.

## Phạm vi chứng minh

- `serialized_pointer_resolved`: quan hệ liên kết **cấu hình serialized tại thời điểm build** đã được tìm thấy, không phải bằng chứng hàm thực sự chạy ở runtime.
- `source_key_value_observed`: key/value có thật trong ScriptableObject từ build. v0.3 đã xác minh mức này.
- `ui_snapshot_only`: scene UI TMP m_text chỉ chứng minh text serialized ở nơi hiển thị. **T001 `New Game` chưa có chứng cứ prefab origin** từ build và phải giữ `not_proven`.
- Không dùng Unity Editor ground truth trong scanner/provenance. Chấm điểm qua evaluator riêng.

## Cài đặt

1. Giải nén ZIP vào thư mục bất kỳ.
2. Mở PowerShell tại thư mục có `Install_Fix_v04.ps1`.
3. Chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v04.ps1
```

Installer sao lưu những file sẽ ghi đè rồi chép mã nguồn, `Run_M03.ps1`, một bài test v0.4 và fixture JSON từ bản build v0.3. Không sửa `.venv`, `AgentInput`, `PrivateEvaluation` hoặc file build Unity.

## Thực hiện trên Windows

```powershell
cd D:\ModStudioAI\Milestone03

powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode provenance
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode baseline
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate
```

Sau đó đọc `Outputs\build_assets.json`: nếu tìm được entry ở `reader_bindings` với `binding_status = "serialized_pointer_resolved"` và `resolved_target_ref = "sharedassets0.assets#path_id=16"`, v0.4 đã nối thành công pointer. File `provenance_links.json` khi đó có trạng thái `serialized_pointer_and_lookup_flow_proven_runtime_unverified` cho `Load Game`.

**Không có gì đảm bảo trước khi chạy thực tế rằng bảng externals của Unity 6.3 sẽ tham chiếu đúng tên file mà scanner đọc được.** Nếu chưa resolve, vẫn phải giữ trạng thái chưa xác minh pointer và gửi hai JSON để xem ngoại lệ hoặc cải tiến resolver.

## Kiểm thử

- Bản v0.4 có **12 bài test mới**, cộng với 22 bài test v0.3. Đã chạy 34/34 đạt trong môi trường tạo bản vá, bao gồm fake UnityPy external table, pointer target đúng và sai, trùng file name, sai key, local PPtr và kiểm tra không nâng điểm dữ liệu v0.3 cũ.
- Test UnityPy synthetic **không thay cho kiểm thử Unity 6.3 thực tế**. Cần chạy `scan-assets` trên máy bạn.
- `baseline` và `evaluate` **không tăng điểm T001**; nguồn prefab không thể được tự suy ra từ `TMP_Text.m_text`.

## Gửi lại khi hoàn tất

Gửi `Outputs\build_assets.json`, `Outputs\provenance_links.json` và `Outputs\evaluation_private.json` (hoặc nén thư mục Outputs). Chúng tôi sẽ kiểm tra pointer mapping cùng các hạn chế, cập nhật GitHub `fuckdcma/MOD-KIT` và tiến tới chạy Qwen local.
