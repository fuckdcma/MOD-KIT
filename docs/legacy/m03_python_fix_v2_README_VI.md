# Mod Studio AI — Sửa lỗi `NameError: name 'P' is not defined`

## Vì sao xảy ra?
`Setup_Python312.ps1` bản trước dùng `py -3.12 -c '... struct.calcsize("P") ...'`. Khi truyền qua Windows PowerShell 5.1, dấu nháy bên trong argument có thể bị loại bỏ, khiến Python nhận `struct.calcsize(P)` và báo `NameError`. Đây là lỗi script kiểm tra phiên bản, chưa thể kết luận Python 3.12 thiếu.

## Cách làm
1. Trong PowerShell kiểm tra: `py -3.12 --version`. Nếu không xuất hiện Python 3.12, chạy `py -0p` rồi cài Python 3.12 Windows x64.
2. Sao lưu `D:\ModStudioAI\Milestone03\Setup_Python312.ps1` và `Run_M03.ps1` hiện tại nếu đã tùy chỉnh.
3. Giải nén **cả 3 file** `Setup_Python312.ps1`, `Verify_Python312.py`, `Run_M03.ps1` vào `D:\ModStudioAI\Milestone03` (ghi đè hai script cũ). Không xóa thư mục `src`, `AgentInput`, `PrivateEvaluation`, `Outputs`.
4. Chạy:

```powershell
Set-Location D:\ModStudioAI\Milestone03
powershell -NoProfile -ExecutionPolicy Bypass -File .\Setup_Python312.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
```

5. Kết quả scanner sẽ nằm tại `D:\ModStudioAI\Milestone03\Outputs\build_assets.json` nếu thực thi thành công.

## Nếu vẫn lỗi
- Nếu `py -3.12 --version` lỗi: Python 3.12 chưa được Python Launcher tìm thấy. Dùng `py -0p` để kiểm tra.
- Nếu `.venv` báo sai kiến trúc hoặc phiên bản: `Rename-Item .venv .venv_backup` rồi chạy lại setup (không mất dữ liệu dự án).
- Nếu UnityPy báo không tìm được wheel: gửi log pip, không chuyển lại dùng Python 3.15.
- Nếu scanner báo lỗi đọc Unity 6.3: gửi file `build_assets.json` và thông báo lỗi, đó là vấn đề độc lập với cài Python.

Bản sửa thay bước xác minh `python -c` bằng một tệp Python riêng để tránh lỗi quoting. Chưa được kiểm thử trực tiếp trên Windows của bạn.