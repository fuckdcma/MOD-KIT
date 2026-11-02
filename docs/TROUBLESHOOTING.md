# Environment & troubleshooting — Windows

## Cấu hình xác minh

- Unity Editor 6000.3.27f2, Windows Mono (Assembly-CSharp.dll CIL)
- GPU AMD Radeon RX 6700 XT 12 GB; graphics D3D12
- Python 3.12.10 64-bit dùng riêng qua `D:\ModStudioAI\Milestone03\.venv\Scripts\python.exe`.
- UnityPy 1.25.4, lz4 4.4.5, tpk_ar 0.2.4; TypeTreeGeneratorAPI 0.0.10 cho M03 v0.2.

## Lỗi đã gặp và cách giải quyết

1. **Python 3.15**: pip cố build UnityPyBoost và lz4 từ source, báo MSVC `io.h` missing. Khắc phục bằng Python 3.12.10 x64 và wheel prebuilt.
2. **Setup Python v1**: PowerShell quote lỗi `NameError: name 'P' is not defined`. V2 dùng `Verify_Python312.py`.
3. **UnityPy `tpk_ar` missing**: `--only-binary=:all:` loại sdist-only `tpk_ar`. Cài riêng `& ".\.venv\Scripts\python.exe" -m pip install "tpk_ar==0.2.4"`, rồi chạy Setup skip pip upgrade. V3 tự xử lý.
4. **ExecutionPolicy**: PowerShell chặn trực tiếp `Run_M03.ps1`. Chạy phiên riêng `powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests`; không cần thay policy vĩnh viễn.
5. **UnityPy 32 MonoBehaviour decode errors ở v0.1**: chưa load type trees cho scripted MonoBehaviour. Bản vá v0.2 dùng TypeTreeGeneratorAPI với Managed DLL; trên bản build lab giải mã 32/32.
6. **Unity GPU warnings**: Player.log có ComputeBuffer/D3D12 resource cleanup và Curl warning, chưa có bằng chứng ảnh hưởng text. Chưa xử lý dứt điểm.

## Các lệnh sử dụng

```powershell
cd D:\ModStudioAI\Milestone03
& ".\.venv\Scripts\python.exe" -m pip check
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode scan-assets
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode baseline
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode evaluate
```

Không chạy lại REA nếu assembly hash không đổi. Nếu dùng lệnh trên cho build khác, thu thập lại SHA-256 và ground truth riêng.
