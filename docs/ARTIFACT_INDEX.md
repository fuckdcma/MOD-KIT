# Artifact index — snapshot 2026-11-02

## Snapshot nguyên gốc

[archives/MODKIT_Chat_Artifacts_20261102.zip](../archives/MODKIT_Chat_Artifacts_20261102.zip) đã được đưa vào nhánh main. Bao gồm 88 file sẵn có trong phiên này: ZIP/RAR, PNG, JSON/CSV, log, báo cáo, code và source extracts. Bên trong ZIP có MANIFEST_SHA256.json với SHA-256/size của từng file.

## Tệp đọc trực tiếp trên GitHub

- [Hồ sơ bàn giao](CHAT_HANDOFF.md)
- [REA](../evidence/m01/rea/) và [Player.log](../evidence/m01/runtime/Player.log)
- [M03 build-only JSON](../evidence/m03/latest/)
- [M02 & M03 reports](../reports/)
- [Dữ liệu tham chiếu](../benchmarks/reference_DO_NOT_FEED_MODEL/) — PUBLIC, không phải secret
- [Source code](../source/) — được bổ sung theo các commit riêng; nếu liên kết chưa tồn tại, giải nén snapshot ZIP để lấy source.

## Các giới hạn

Không có API tự động xuất nguyên văn lịch sử chat ChatGPT. Phần đã lưu chỉ là *tài liệu bàn giao + toàn bộ file hiện vật khả dụng*. Bản UnityTextLab đang nằm trên máy tác giả có thể có scene/prefab/build khác những file đã tải lên; không coi các tệp cục bộ chưa đồng bộ là đã có trên GitHub.

Mỗi lần có milestone mới, cập nhật cả source, evidence và CHANGELOG. Không commit token/secret, thư mục .venv/Library, game thương mại hoặc trọng số model không được phép chia sẻ.
