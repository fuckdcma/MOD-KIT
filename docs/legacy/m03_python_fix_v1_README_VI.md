# Mod Studio AI — Sửa lỗi UnityPy trên Python 3.15

## Nguyên nhân đã thấy trong log
- `Run_M03.ps1` chọn `py -3`, nên chạy Python 3.15 ở `C:\Python315`.
- `UnityPy==1.25.4` trên PyPI có wheel Windows x64 cho CPython 3.12 (`cp312-win_amd64`), nhưng log cài Python 3.15 phải biên dịch extension từ source rồi thiếu `io.h`.
- Các bài kiểm thử Milestone 03 (7/7), baseline và evaluate đã đạt; chỉ UnityPy/asset scan bị chặn.

## Cài sửa (không gỡ Python 3.15)
1. Cài **Python 3.12.10 Windows installer 64-bit** từ https://www.python.org/downloads/release/python-31210/ . Đây là bản 3.12 cuối có Windows installer chính thức.
2. Mở PowerShell mới, kiểm tra `py -3.12 --version`.
3. Giải nén **hai file** `Run_M03.ps1` và `Setup_Python312.ps1` vào `D:\ModStudioAI\Milestone03`. **Sao lưu** `Run_M03.ps1` hiện tại trước khi ghi đè; giữ nguyên thư mục `src`, `AgentInput`, `PrivateEvaluation`, `Outputs`.
4. Trong PowerShell: 

```powershell
Set-Location D:\ModStudioAI\Milestone03
powershell -NoProfile -ExecutionPolicy Bypass -File .\Setup_Python312.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
```

Đầu ra: `D:\ModStudioAI\Milestone03\Outputs\build_assets.json`.

## Lưu ý
- Bản vá chỉ thay cách chọn Python; không thay thuật toán REA, dataset, hay code scanner.
- Python được cài vào `.venv` cục bộ, script sẽ không tự chọn Python 3.15.
- Nếu scanner trả `errors` do phiên bản Unity 6.3/type tree, hãy giữ nguyên `build_assets.json` và gửi để phân tích; đó là vấn đề tiếp theo, khác lỗi pip.
- Không chạy `py -3 -m pip install UnityPy` nữa; lệnh này có thể chọn 3.15.