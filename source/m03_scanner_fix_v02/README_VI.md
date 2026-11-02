# Mod Studio AI — Milestone 03 Asset Scanner Fix v0.2

## Kết quả từ gói Outputs.rar (02/11/2026)

- 6/6 file Unity build đã được xem xét; `truncated=false`.
- UnityPy giải mã thành công 1 TextAsset: `Hello, Commander` từ `resources.assets#path_id=9` với trường JSON `message` và `asset_name=dialogue`.
- 32 đối tượng `MonoBehaviour` báo lỗi thiếu phần dữ liệu sau header, phân bố: `level0` 14; `sharedassets0.assets` 14; `resources.assets` 3; `globalgamemanagers.assets` 1.
- `baseline_static.json` và `evaluation_private.json` cũ chỉ chấm REA: 1 text nguyên vẹn + 1 template + 3 chưa chứng minh.
- Khi ghép chính **bằng chứng TextAsset đã xuất** với REA (được chạy/kiểm chứng offline bằng chính các file gửi), bản chấm mới là **2 text nguyên vẹn + 1 template + 2 chưa chứng minh**. Đây KHÔNG phải điểm AI Qwen.

## Sửa gì?

1. Dùng **TypeTreeGeneratorAPI** (không bắt buộc, nhưng khuyến nghị) và DLL trong `<Build>_Data/Managed` để cố tạo typetree cho các MonoBehaviour thiếu cấu trúc. *Không đảm bảo thành công trên mọi game/Unity phiên bản*.
2. Khi không thể parse MonoBehaviour, thu chuỗi UTF-8 có độ dài dạng Unity vào `raw_candidates`. **Dữ liệu thô này chỉ là ứng viên; KHÔNG được chấm thành bằng chứng nguồn chính xác**.
3. Ghi `mono_script` (assembly và tên class) nếu có thể truy vết `m_Script` để hỗ trợ nghiên cứu sau này.
4. Baseline mặc định đọc `Outputs/build_assets.json` (nếu có) để ghép các chuỗi `external_json` được giải mã từ TextAsset.
5. Kiểm tra `source_type` trong bộ xác thực bằng chứng để tránh giả mạo nguồn dữ liệu bằng các kết quả asset khác kiểu.
6. Giữ REA input và private evaluation tách nhau, không đưa ground truth vào tin nhắn model.

## Cài đặt

**Không chép file vào thư mục Unity game hoặc vào Assets của project.** Chỉ chép bản vá vào Milestone03.

1. Giải nén ZIP bất kỳ chỗ nào, rồi mở PowerShell tại thư mục chứa `Install_Fix_v02.ps1`.
2. Chạy (mặc định dùng `D:\ModStudioAI\Milestone03`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install_Fix_v02.ps1
```

Installer sao lưu file cũ vào `D:\ModStudioAI\Milestone03\Backups\M03_AssetFix_v02_<time>`, rồi thay **chỉ** `src\modstudio_m03.py`, `Run_M03.ps1` và thêm `tests\test_scanner_v02.py`. Không đụng vào `.venv`, REA hay báo cáo cũ.

3. Thêm thư viện tái tạo TypeTree (khuyến nghị; đã có wheel Windows x64 cho Python 3.12):

```powershell
cd D:\ModStudioAI\Milestone03
& '.\.venv\Scripts\python.exe' -m pip install 'TypeTreeGeneratorAPI==0.0.10'
& '.\.venv\Scripts\python.exe' -m pip check
```

4. Chạy lại scan, sau đó baseline và evaluate **đúng thứ tự**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode baseline
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate
```

5. Gửi 2 file:

- `D:\ModStudioAI\Milestone03\Outputs\build_assets.json`
- `D:\ModStudioAI\Milestone03\Outputs\evaluation_private.json`

Nếu scanner báo lỗi từ `TypeTreeGeneratorAPI`, gửi thêm log PowerShell. Nếu chưa cài `TypeTreeGeneratorAPI`, scanner vẫn chạy bằng fallback thô, nhưng không thể cam kết tìm được 2 case còn thiếu.

## Cách xem candidate

Mở `build_assets.json`, tìm:

- `assets`: chuỗi có cấu trúc được giải mã từ bản build; `asset_text` được xem xét bằng chứng có điều kiện.
- `raw_candidates`: chuỗi độ dài dạng Unity từ byte stream, **chỉ là ứng viên**, không chứng minh đường dẫn prefab/scene/class.
- `errors`: lỗi giải mã theo `file`, `path_id`, `stage`.
- `type_tree_generator`: thông tin module đã nạp chưa, Unity version đã dựng được và lỗi khởi tạo.
- `stats`: số MonoBehaviour parse được, số TextAsset, số candidate.

**Quy tắc an toàn bằng chứng:** Thấy `New Game` trong `raw_candidates` vẫn KHÔNG chứng minh nó đến từ prefab. Thấy `Load Game` trong `raw_candidates` cũng KHÔNG chứng minh nó đến từ `LabStringTable`. Cần metadata class/field hoặc kiểm thử riêng để kết luận.

## Độ tin cậy

- 12/12 kiểm thử Python đạt trong môi trường tạo patch: 7 kiểm thử gốc + 5 mới. Test bổ sung kiểm tra raw string parser, chống nâng cấp ứng viên chưa chứng minh thành proof, kiểm tra source_type và JSON lồng nhau.
- Kết hợp **các đầu ra thực tế bạn đã gửi** với REA cho kết quả 2 exact + 1 template + 2 not_proven.
- Không có file build `.assets` của bạn trong môi trường tạo bản vá, nên chưa thể thử nhánh TypeTreeGenerator trực tiếp trên Unity 6000.3.27f2 của PC bạn. Phải quét lại trên máy bạn để xác thực.

## Đặc điểm kỹ thuật

- Chỉ đọc dữ liệu bản build, không tạo hook, không inject code, không ghi file game.
- Không sử dụng dữ liệu Editor/ground truth làm đầu vào scan.
- `raw_candidates` giới hạn tối đa 2.000 mục; giới hạn mỗi object 25 chuỗi để tránh output vô hạn. Với game lớn, nên điều chỉnh giới hạn theo batch sau.
