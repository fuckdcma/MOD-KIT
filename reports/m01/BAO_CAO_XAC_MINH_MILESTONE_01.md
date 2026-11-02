# Báo cáo xác minh UnityTextLab — Milestone 01

Ngày xác minh: 2026-11-02. Nguồn: ảnh chụp UnityTextLab, `Player.log`, `ground_truth_v01.csv`; đối chiếu với REA `assembly_identity.json` và `members.json` được cung cấp trong lượt trước.

## Tóm tắt

- 5/5 mục văn bản có mặt trên ảnh chụp, nội dung đúng theo ca thử nghiệm.
- `T004`: ảnh chụp hiển thị `Health: 65/100`, ground truth là `75/100`; không phải lỗi vì đây là chuỗi động, mã `RuntimeTextExample.Update -> Refresh` làm thay đổi health.
- Unity `6000.3.27f2`, Mono; DX12, AMD RX 6700 XT, log nhận `12242 MB` bộ nhớ đồ họa.
- Dòng `[ModStudioLab][SDF]` ghi `sameAtlas=True` cho `Prefab_NewGame` với LiberationSans SDF và shader TextMeshPro/Mobile/Distance Field. Không suy rộng sang toàn bộ UI, không chứng nhận dấu tiếng Việt.
- Log có `Curl error 35`, cảnh báo info queue D3D12, `ComputeBuffer` chưa dispose và một resource D3D12 chưa giải phóng. Không thấy exception C# của ModStudioLab trong log được cung cấp; chưa đủ dữ liệu để kết luận không có rò rỉ hoặc lỗi đồ họa.

## Xác minh riêng từng mẫu

| ID | Ground truth | Trên ảnh | Bằng chứng nguồn từ REA | Tình trạng nguồn |
|---|---|---|---|---|
| T001 | New Game | New Game | Assembly không đủ chứng minh dữ liệu prefab | Chờ đọc prefab/scene |
| T002 | Load Game | Load Game | `TableTextExample.Start -> LabStringTable.TryGet`, key `menu.load` | Chờ xác minh trực tiếp nội dung asset |
| T003 | Quest Completed | Quest Completed | `HardcodedTextExample.Awake` literal và `TMP_Text.set_text` | Có bằng chứng tĩnh mạnh |
| T004 | Health: 75/100 (ban đầu) | Health: 65/100 | `RuntimeTextExample.Update -> Refresh` và `Health: {0}/100` | Có bằng chứng tĩnh + runtime ảnh |
| T005 | Hello, Commander | Hello, Commander | `ExternalTextExample.Start -> Resources.Load -> JsonUtility.FromJson -> TMP_Text.set_text` | Chờ xác minh trực tiếp dữ liệu JSON |

## Điều kiện lên dataset train

- Các mẫu này đủ điều kiện làm **tập hạt giống cho thu thập bằng chứng**, không nên tự động gán cả năm là `verified_train`.
- Đánh dấu `T003`, `T004` là đối chiếu tĩnh + hiển thị đạt; `T001`, `T002`, `T005` còn khâu xác minh source asset/JSON.
- Tạo bộ kiểm thử độ phủ nguồn (asset + code + runtime) trước khi train Qwen, vì REA static CIL không tự chứng minh toàn bộ text trong scene, prefab, ScriptableObject hoặc JSON.
- Khi thu thập thêm log hãy gắn `assembly SHA256`, `MVID`, `Unity version`, `scene`, `object path`, `screenshot id`, `ground_truth revision` và `evidence timestamp` để tránh nhầm dữ liệu từ nhiều bản build.

## Bước tiếp theo đề xuất

1. Bảo lưu bản build Unity Mono hiện tại và hai JSON REA làm baseline.
2. Thêm công cụ thu thập metadata chỉ đọc trong Unity Editor để xuất trường text từ prefab/scene và ScriptableObject; với Resources JSON, lưu một bản đối chiếu trường text từ nguồn gốc của lab.
3. Thêm ca text tiếng Việt `Tiếng Việt: ă â ê ô ơ ư đ — Á À Ả Ã Ạ` và các thử nghiệm font SDF có chủ đích. Giữ baseline font chạy tốt trước khi tạo lỗi.
4. Tạo 2-3 bản build mẫu cùng tên nội dung nhưng khác nguồn text để thử khả năng phân biệt provenance; chạy REA, sau đó benchmark Qwen nền trước khi LoRA.

**Lưu ý:** Bản báo cáo chỉ đánh giá bằng chứng đã cung cấp, không xác nhận đã chạy thử hook hay đã fine-tune model.