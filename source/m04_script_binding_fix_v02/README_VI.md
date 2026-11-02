# Mod Studio AI — M04 Script Binding Repair v0.2

**Khắc phục lỗi UnityTextLab-B hiển thị `...` và cảnh báo BuildPipeline `Script attached ... is missing or no valid script is attached`.**

## Lý do

M04 generator v0.1 đặt **hai MonoBehaviour (`M04TableReader`, `M04JsonReader`) và một ScriptableObject (`M04Table`) chung trong file `M04LabRuntime.cs`**. Unity 6000.x không thể ánh xạ các lớp này một cách không mơ hồ tới một `MonoScript` asset khi serialize scene / table asset. Editor có thể hiển thị một số text trong Play, nhưng BuildPipeline báo missing script trên `M04_Reader_*` và bảng `M04HoldoutTable.asset`. Kết quả build tuy thành công nhưng chưa hợp lệ làm benchmark.

Bản vá tách mỗi MonoBehaviour và ScriptableObject thành file có tên trùng lớp; sửa **sáu reader** và **bảng ScriptableObject** từ chính `ProjectSettings/M04HoldoutLocal.json` *đã có*, không sinh seed mới hoặc thay đổi giá trị private. Đồng thời nó chèn kiểm tra `ValidateBeforeBuild()` trước `BuildPipeline.BuildPlayer` của builder cũ; build sẽ bị chặn nếu còn missing script.

**Chưa được biên dịch bằng Unity Editor trên Windows từ môi trường hiện tại**; đây là bản sửa dựa trên mã nguồn + Unity API và có kiểm thử cấu trúc offline. Nếu có lỗi Unity Console, báo chỉ lỗi, không gửi private seed / spec / ground truth.

## Cài đặt — lưu ý quan trọng

1. **Đóng toàn bộ Unity Editor** và dừng Play Mode.
2. Giải nén ZIP vá mới vào một thư mục tạm; mở PowerShell ở thư mục chứa `Scripts`.
3. Chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Install_M04_ScriptBindingFix.ps1
```

Script chỉ nhận project có tên `UnityTextLabB`, từ chối ghi đè nếu file đích đã tồn tại, và sao lưu `M04LabRuntime.cs`, `.meta`, `M04LabBuilder.cs` trong `D:\ModStudioAI\UnityLab\UnityTextLabB\ProjectSettings\M04PatchBackups`. Các file backup có thể chứa liên kết serialized; **không upload lên GitHub public**.

Script cũ bị loại khỏi thư mục `Assets` sau khi đã sao lưu, vì Unity không được có các định nghĩa lớp trùng nhau.

## Khôi phục liên kết trong Unity

1. Mở lại project UnityTextLabB, đợi Unity biên dịch xong (không có lỗi đỏ).
2. Mở **scene đã có**: `Assets/M04/Scenes/UnseenLabB.unity`. **Không nhấn `Generate Unseen Lab B Scene` lần nữa.**
3. Chọn `Tools > Mod Studio AI > M04 > Repair Missing Script Bindings`. Xác nhận hộp thoại.
4. Chọn `Tools > Mod Studio AI > M04 > Validate Scene Bindings`.
5. Nếu Console in `[M04] Validation OK...`, mở Game/Play và xác nhận **15 label đều hiển thị text; không còn `...`**. Dấu `...` là placeholder thiết kế cho các label đọc runtime (JSON/bảng/hardcoded/format), nên không thể dùng làm kết quả cuối cùng.
6. **Clear Unity Console**, Exit Play, rồi `Tools > Mod Studio AI > M04 > Build Unseen Lab B Windows Mono`.
7. Build thành công **và không còn cảnh báo `Script attached ... is missing`** mới đạt bước kiểm chứng này. Mã builder đã có build guard; nếu sai sẽ throw trước build.

### Những gì repair sẽ thay đổi

- Xóa/thay **duy nhất** `Assets/M04/Data/M04HoldoutTable.asset` (sao lưu file cũ + `.meta` trong `ProjectSettings/M04RepairBackups`), vì file cũ tham chiếu MonoScript không hợp lệ. GUID của asset có thể thay đổi.
- Bỏ missing component và gắn lại đúng `M04TableReader`/`M04JsonReader` tại 6 `M04_Reader_B...`; khôi phục `table`, `key`, `resourceName`, `label` từ private spec *sẵn có*.
- Giữ nguyên 15 UI labels, 3 prefab, generated C# literal/template, seed, ground truth, spec và các file dự án UnityTextLab-A.
- **Build B cũ phải loại khỏi phép chấm**; chỉ dùng build mới sau khi sửa. Sau sửa, hash và GUID thay đổi, nên `seal` phải chạy trên bản build mới.

### Nếu không muốn thay asset trên lab hiện tại

Có thể coi build B hiện tại chỉ là smoke test; khi đó tạo lab khác sau khi cập nhật generator v0.2 trong tương lai. Tuyệt đối không chấm AI trên build có missing scripts. Nếu bạn chọn sửa lab hiện có theo các bước trên, dữ liệu case/seed không bị tạo lại, nhưng build binary được cập nhật và phải niêm phong hash mới.

### Dữ liệu riêng tư

**Không gửi lên ChatGPT hoặc GitHub public:** `seed_PRIVATE.hex`, `ground_truth_PRIVATE.json`, `ProjectSettings/M04HoldoutLocal.json`, source `M04Generated*.cs`, Unity project B đầy đủ, `M04HoldoutTable.asset` hoặc backup của nó. Các ảnh màn hình chứa câu private cũng không nên đưa vào repo public. Hãy gửi **chỉ log validate/build không chứa câu private** để kiểm tra kết quả.

Sau khi có build B sạch cảnh báo, chuyển sang `Scripts\Run_M04.ps1 -Mode seal`, `-Mode rea`, `-Mode evidence` trên **bản M04 v0.1 gốc**, rồi chấm theo giao thức M04 sau khi khóa predictions. Không chạy lại REA hoặc Qwen trên bản build B bị cảnh báo.
