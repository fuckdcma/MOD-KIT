# Mod Studio AI — Milestone 03 / Provenance Linker v0.3

Ngày: 2026-11-02. Bản vá cho UnityTextLab (Unity 6000.3.27f2, Mono) và đường chạy `D:\ModStudioAI\Milestone03`.

## Mục đích

Bản v0.2 đã giải mã 32/32 `MonoBehaviour` nhưng chỉ xuất `LabStringTable.entries[0].value = Load Game`, bỏ sót `entries[0].key`. Vì vậy **không thể kết luận** đó là cặp key/value đúng, dù REA đã phát hiện `LabStringTable.TryGet`.

Bản v0.3 bổ sung **liên kết cặp key/value từ đúng cùng object serialized**, thông tin cấu hình reader (nếu có), báo cáo chứng cứ build-only và quy tắc không dùng scene TMP snapshot để giả mạo nguồn prefab.

### Cấu trúc bằng chứng

- `source_key_value_observed`: `MonoBehaviour` phải giải mã được và class chính xác `ModStudioLab.LabStringTable`, thuộc `entries[N].value`, có `entries[N].key` cùng entry. Đây là bằng chứng **nguồn trong build**, không tự xác nhận game runtime đã chọn bản ghi.
- `reader_calls_observed_key_or_pointer_not_linked`: REA chứng minh `TableTextExample.Start` có gọi `LabStringTable.TryGet` rồi `TMP_Text.set_text`; chưa chứng minh instance reader trỏ chính xác tới asset nào.
- `lookup_call_and_key_supported_pointer_unresolved`: nếu Unity build có reader key trùng key trong table, vẫn chưa đảm bảo PPtr được resolve. Giữ nguyên trạng thái chờ xác nhận.
- `ui_snapshot_only`: `TMP_Text.m_text` trong `level0` chỉ xác nhận text UI serialized; **không thể khẳng định prefab source**.
- Text hardcoded & runtime format tiếp tục dựa vào REA IL literal; external JSON dựa vào TextAsset.

## Cài đặt

Giải nén ZIP vào thư mục bất kỳ. Mở PowerShell tại thư mục có `Install_Fix_v03.ps1`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v03.ps1
```

Installer chỉ sao lưu và chép **3 file**: `src\modstudio_m03.py`, `Run_M03.ps1`, `tests\test_provenance_v03.py`. Không xóa `.venv`, AgentInput, PrivateEvaluation, hoặc Outputs. Không cần chạy lại REA khi assembly DLL không đổi.

Chạy bằng PowerShell không sửa ExecutionPolicy vĩnh viễn:

```powershell
cd D:\ModStudioAI\Milestone03
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode provenance
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode baseline
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate
```

File mới: `Outputs\provenance_links.json` (build-only), cùng `build_assets.json`, `baseline_static.json`, `evaluation_private.json` mới.

## Mục tiêu và hạn chế

- Cần xác nhận `build_assets.json` mới có field `metadata.entry_key = "menu.load"` trong class `LabStringTable`. Đây là **dự kiến**, chưa chạy thực tế TypeTree mới trên PC của bạn.
- Nếu có đủ bằng chứng key/value, **T002 có thể được ghi nhận source+text** mà vẫn chú thích runtime reader binding chưa chứng minh. Điểm đánh giá dự kiến có thể từ 2 exact lên 3 exact. Đây chỉ là kỳ vọng, không phải kết quả chạy thực tế.
- **T001 vẫn chưa đạt**: Unity build có `New Game` ở `level0`, nhưng không khôi phục được đường prefab gốc, GUID và relation đáng tin chỉ từ đó.
- Dữ liệu Unity Editor / ground truth **không** được dùng trong scanner hoặc `provenance_links.json`. `evaluate` riêng đọc bảng đáp án.
- Không dùng REA/UnityPy để hook hoặc sửa game ở phiên này.

## Cần gửi sau khi chạy

`Outputs\build_assets.json`, `Outputs\provenance_links.json`, `Outputs\evaluation_private.json` và log lỗi nếu có.

## Dữ liệu nghiên cứu

Các trường 
`asset_type`, `metadata.mono_script.full_class_name`, `field_path`, `entry_key`, `reader_bindings` cần được giữ khi phiên mới/AI hoặc repo GitHub phân tích kết quả. `schema=modstudio.m03.v0.3` phân biệt bản vá với output cũ.

**Lưu ý chấm điểm:** `-Mode evaluate` mặc định chỉ chấm `baseline_static.json`, tránh vô tình chấm file Qwen cũ. Muốn chấm Qwen sau khi chạy agent, dùng `-Mode evaluate -EvaluateTarget agent`; kết quả nằm trong `evaluation_private_agent.json`.
