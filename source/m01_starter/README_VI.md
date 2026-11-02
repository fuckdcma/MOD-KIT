# Mod Studio AI — Unity Text Laboratory v0.1

Bộ khởi động mẫu phục vụ nghiên cứu text provenance. Đây không phải app hoặc hook engine hoàn chỉnh. Không sử dụng BepInEx hay Harmony. Mọi tệp C# chỉ chạy trong project Unity do bạn tạo.

## Mục tiêu

Tạo 5 nguồn text khác nhau, build Windows x64 bằng backend Mono, dùng REA phân tích `Assembly-CSharp.dll`, so sánh với ground truth, và tạo các case huấn luyện đã xác minh.

## Tạo project

1. Trong Unity Hub, tạo project **UnityTextLab** kiểu 2D/Built-in, ở `D:\ModStudioAI\UnityLab\UnityTextLab`.
2. Bật Windows x64 + **Scripting Backend = Mono** trong Project Settings > Player > Other Settings.
3. Sao chép thư mục `Assets/Scripts` và `Assets/Resources` từ starter vào `Assets` của Unity project. Nếu Unity hỏi import TextMeshPro essentials, xác nhận.
4. Tạo scene `Assets/Scenes/TextLab.unity`.
5. Tạo **Canvas**, sau đó tạo 5 đối tượng con bằng **UI > Text - TextMeshPro**. Đặt tên lần lượt:
   - `Prefab_NewGame`: gõ text trong Inspector là `New Game`. Kéo đối tượng từ Hierarchy đến `Assets/Prefabs/` để lưu prefab (vẫn giữ instance ở scene).
   - `Table_LoadGame`: để text tạm `...`.
   - `Hardcoded_Quest`: để text tạm `...`.
   - `Runtime_Health`: để text tạm `...`.
   - `External_Greeting`: để text tạm `...`.
6. Dùng RectTransform sắp xếp năm đối tượng theo chiều dọc, đảm bảo nhìn thấy tất cả trên Game view.

## Liên kết script

7. Tạo một GameObject rỗng tên `LabController`.
8. Gắn `TableTextExample`, `HardcodedTextExample`, `RuntimeTextExample`, `ExternalTextExample` vào `LabController`.
9. Tại Project view, nhấn chuột phải **Create > ModStudioAI > Lab String Table**. Tạo asset `LabStringTable.asset`, đặt `Entries` có một hàng `key=menu.load`, `value=Load Game`.
10. Trong Inspector, gán:
    - `TableTextExample`: table = `LabStringTable.asset`; key = `menu.load`; label = `Table_LoadGame`.
    - `HardcodedTextExample`: label = `Hardcoded_Quest`.
    - `RuntimeTextExample`: label = `Runtime_Health`.
    - `ExternalTextExample`: label = `External_Greeting`.
11. Gắn `FontSnapshot` vào `LabController`, chọn label `Prefab_NewGame`. Đây là log chỉ-đọc về font, material và atlas; **không phải hệ thống chẩn đoán tự động**.

## Thử nghiệm

12. Nhấn Play. Kỳ vọng hiển thị: `New Game`, `Load Game`, `Quest Completed`, `Health: 75/100`, `Hello, Commander`. Chỉ số Health giảm 5 mỗi 2 giây.
13. Mở Console; xác nhận không có error. Kiểm tra dòng `[ModStudioLab][SDF]`.

## Build và nghiên cứu REA

14. Vào File > Build Profiles, chọn Windows, build đến `D:\ModStudioAI\Builds\UnityTextLab\UnityTextLab.exe`. Cần bảo đảm scene `TextLab` được đưa vào build.
15. Kiểm tra có `D:\ModStudioAI\Builds\UnityTextLab\UnityTextLab_Data\Managed\Assembly-CSharp.dll`.
16. Cài REA theo repo chính thức `https://github.com/morluto/rea`: sau khi có Node.js tương thích, chạy `npx rea-agents setup` (hoặc `npm install --global rea-agents` nếu muốn CLI). Xem và duyệt mọi thay đổi cấu hình trước khi chấp nhận.
17. Chạy `Research/REA_commands.ps1` sau khi đã đọc và kiểm tra đường dẫn. Nó xuất metadata và CIL, không chạy DLL game.
18. Đối chiếu kết quả REA với `Datasets/ground_truth_v01.csv`. **Không đưa file ground-truth vào lời nhắc của AI khi làm bài test mù.**
19. Với từng case, điền `Datasets/research_case_template.json`, giữ nguồn evidence, loại xác minh và các hạn chế. Chưa chuyển `unverified` thành `verified` nếu chưa đối chiếu.

## Tại sao có source code trong starter?

Project Unity nguồn dùng để tạo *ground truth*. Khi benchmark model, chỉ cung cấp game build/assembly và các tool được phép; giữ source và nhãn đáp án ở phía bộ kiểm thử để tránh rò rỉ kết quả.

## Phần chưa được triển khai

- Hook độc lập / loader / font replacement.
- Phân tích tự động scene và prefab bằng REA (REA managed code không tự giải mã mọi Unity asset).
- AI model, RAG, Google Drive, LoRA training.
- Benchmark SDF nâng cao (hiện mới ghi thông tin trạng thái).

Chỉ sử dụng trên project thử nghiệm và phần mềm bạn có quyền phân tích.
