# Báo cáo xác minh `Outputs.rar` — Mod Studio AI M03

Ngày kiểm tra: 2026-11-02.

## Tệp đầu vào

- `baseline_static.json`: hoàn thành, 4 observation (2 observed, 2 hypothesis), SHA-256 assembly `ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e`.
- `evaluation_private.json`: 5 case, 1 exact, 1 template, 3 not_proven.
- `build_assets.json`: `files_considered=6`, `files_scanned=6`, `truncated=false`, `assets=1`, `errors=32`.

## Kết quả từ bản build

Đã trích xuất `Hello, Commander` từ `resources.assets#path_id=9`, `TextAsset`, `asset_name=dialogue`, JSON key `message`. Đây là chuỗi thật sự thu được từ file `.assets`, không phải suy đoán REA.

32 lỗi MonoBehaviour: `level0` 14, `sharedassets0.assets` 14, `resources.assets` 3, `globalgamemanagers.assets` 1. Ví dụ `Expected to read 532 bytes, but only read 32 bytes`. Nguyên nhân phù hợp nhất là thiếu typetree cho custom MonoBehaviours; cần thử generator từ DLL rồi xác minh.

## Kết quả ghép thử REA + build_assets

Đã kiểm thử bằng cách chạy code sửa v0.2 trên đầu vào REA của Milestone 03 và `build_assets.json` được tải lên:

| Case | Kết quả |
|---|---|
| T001 | Chưa chứng minh `New Game` từ prefab trong build |
| T002 | Chưa chứng minh `Load Game` từ ScriptableObject trong build |
| T003 | `Quest Completed` exact, CIL |
| T004 | `Health: {0}/100` template, CIL |
| T005 | `Hello, Commander` exact, TextAsset JSON |

Kết quả **2 exact + 1 template + 2 not_proven**. Đây là bản ghép lại do code rule-based thực hiện, **không phải điểm AI Qwen** và không có nghĩa source path của prefab được xác định.

## Bản vá

`ModStudioAI_M03_AssetScanner_Fix_v02.zip`: thêm raw candidate scanner (không nâng cấp thành proof), optional TypeTreeGeneratorAPI (phục hồi field layout), ghép TextAsset vào baseline, tăng kiểm tra validation_source_type. 12/12 bài kiểm thử tự động đạt ở môi trường tạo patch; chưa có bản build gốc để kiểm tra tác dụng của TypeTreeGenerator trên máy người dùng.