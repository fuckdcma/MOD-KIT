# MOD-KIT — Mod Studio AI Project Library

**Repository tài liệu và dữ liệu kỹ thuật dài hạn của dự án Mod Studio AI.** Mốc lưu: 2026-11-02.

## Đọc theo thứ tự

1. [CHAT_HANDOFF.md](docs/CHAT_HANDOFF.md) — hồ sơ bàn giao khi chuyển sang cuộc trò chuyện khác.
2. [ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) — nguyên tắc và quyết định đã chốt.
3. [PROGRESS.md](docs/PROGRESS.md) — tiến độ Milestone 01–03.
4. [M03_LATEST_FINDINGS.md](docs/M03_LATEST_FINDINGS.md) — các kết quả build-only mới nhất.
5. [ARTIFACT_INDEX.md](docs/ARTIFACT_INDEX.md) — vị trí file được lưu và phần chưa đồng bộ.
6. [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — sự cố Windows/Python/UnityPy.
7. [SYNC_AND_PRIVACY.md](docs/SYNC_AND_PRIVACY.md) — quy trình đồng bộ, bảo mật, giới hạn archive.

## Tầm nhìn

Mod Studio AI nghiên cứu nguồn text và font, trích xuất nguồn gốc văn bản, nghiên cứu điểm can thiệp bằng REA, tạo adapter mapping text/font 1:1 và kiểm thử mod độc lập. **Ứng dụng Việt hóa là sản phẩm riêng.** Unity Mono được ưu tiên; IL2CPP và Unreal để giai đoạn sau.

## Trạng thái hiện tại

| Giai đoạn | Trạng thái |
|---|---|
| M01 UnityTextLab & REA | Đạt trong laboratory |
| M02 Editor Provenance | 8 bản ghi, 5/5 case đối chiếu với dữ liệu nguồn |
| M03 UnityPy TypeTree v0.2 | 6/6 file, 32/32 MonoBehaviour, 0 lỗi |
| M03 bộ chấm hiện tại | 2 exact / 1 template / 2 unproven |
| Qwen local / LoRA / hook standalone | Chưa kiểm thử hoàn chỉnh |

**Không đồng nhất số liệu công cụ với năng lực AI.**

> **Cảnh báo:** Repository hiện là **public**. Các tệp trong `benchmarks/reference_DO_NOT_FEED_MODEL` chỉ được tách theo quy ước — không hề riêng tư. Việc đưa ground truth công khai có thể làm nhiễm benchmark; muốn một blind test thực sự cần tập đáp án ngoài public repo.

Không thể tự động chép nguyên văn toàn bộ transcript ChatGPT sang đây qua các công cụ hiện có. Kho này lưu bản ghi bàn giao và những file có thể truy xuất; xem [giới hạn](docs/SYNC_AND_PRIVACY.md).

## Snapshot hiện vật 2026-11-02

- [Tải toàn bộ hiện vật đã có trong sandbox (ZIP)](archives/MODKIT_Chat_Artifacts_20261102.zip): 88 file, gồm các ZIP/RAR mã nguồn, ảnh, logs, báo cáo và JSON, có manifest SHA-256. **Không phải bản export nguyên văn toàn bộ chat.**
- [Hồ sơ bàn giao](docs/CHAT_HANDOFF.md) để tiếp tục phiên ChatGPT sau.
- [Mã nguồn được duyệt trên GitHub](source/) sẽ được đồng bộ thành các tệp riêng; xem [chỉ mục](docs/ARTIFACT_INDEX.md).

### Final synchronization status

[Snapshot status / SHA-256 manifest](docs/SNAPSHOT_STATUS.md): archived 88 available original files, published 47 browsable source/evidence text files. Source copies were checked against original SHA-256/Git object IDs. Raw chat messages are **not** exported.


## Milestone 03 v0.3 — Provenance Linker (2026-11-02)

- [Mã nguồn & installer v0.3](source/m03_provenance_v03/) · [Tải gói ZIP](archives/ModStudioAI_M03_Provenance_Fix_v03.zip)
- [Báo cáo v0.3](reports/m03/BAO_CAO_M03_V03.md); 22/22 unit tests; **chưa chạy scanner v0.3 trên PC Windows**.
- Bản v0.3 giải quyết việc bảo toàn `LabStringTable.entries[N].key` cùng `entries[N].value`; T001 prefab origin vẫn chưa có proof. **Điểm chấm thực tế hiện vẫn 2 exact +1 template +2 not proven cho dữ liệu v0.2**.


## Milestone 03 v0.4 — Cross-file PPtr Resolver (2026-11-02)

- [Source, tests and installer v0.4](source/m03_pointer_v04/) · [Download ZIP](archives/ModStudioAI_M03_PointerResolver_Fix_v04.zip) · [Engineering report](reports/m03/BAO_CAO_M03_V04.md)
- **34/34 local synthetic unit tests passed.** Unity 6.3 v0.4 build scan has **not** been run on the user's PC; do not claim pointer resolved until new scan.
- v0.3 real run: **3 exact + 1 template + 1 unproven (T001)**. New resolver checks actual serialized file external table before linking T002 reader to table.
