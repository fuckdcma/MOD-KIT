# Architecture decisions — Mod Studio AI

| Chủ đề | Quyết định / ràng buộc |
|---|---|
| Ranh giới sản phẩm | Mod Studio AI chỉ reverse-engineering/extraction/hook/font mapping; Translator Studio riêng |
| Phạm vi đầu | Unity Mono, Windows offline, project tự tạo |
| Engine tiếp theo | Unity IL2CPP, rồi Unreal |
| Mod distribution | Standalone, không yêu cầu BepInEx/Harmony/MelonLoader/AI runtime |
| REA | Công cụ nghiên cứu metadata/IL/method/callgraph; không runtime loader |
| Asset pipeline | UnityPy + TypeTree + reader riêng, chỉ đọc build; Editor collector chỉ làm reference |
| Text discovery | Cả prefab/scene, string table, hardcoded, runtime-generated, JSON/custom manager |
| Text identity | Bảo toàn key, object path, field, callsite, bối cảnh; không dùng text gốc làm ID duy nhất |
| Text mapping | Bảo toàn placeholder/rich-text và kiểm tra lifecycle, tránh mapping nhầm câu đồng dạng |
| Font mapping | Font asset + material preset + shader + atlas + glyph metrics, kiểm thử SDF thực nghiệm |
| AI | Qwen3.5-4B là ứng viên, local llama.cpp Vulkan; dùng tool evidence và RAG |
| Huấn luyện | LoRA SFT theo case verified trên Colab/Kaggle khi đủ dữ liệu; checkpoint resumable |
| Test | Split theo game/dự án; blind eval build-only không đọc Editor ground truth |
| Mục tiêu dataset | 1700 là mục tiêu tham khảo, không là điều kiện phải hoàn tất mới thử model |
| An toàn | Không can thiệp hoặc vượt anti-cheat; kiểm thử trong game có quyền mod |

## Data lifecycle

`Game build → REA static evidence + Asset reader → identity / provenance hypotheses → verified findings → adapter spec → compiler → runtime and SDF validation → training cases`.

`Unity Editor collector → ground truth / QA only` (không cho agent build-only xem).

Dữ liệu phải có `evidence_ref`, engine/game/version/hash, source_type, object identity, confidence/verification, test result, provenance và train/validation/test split. Chuỗi thấy trong `TMP_Text.m_text` là **snapshot nơi hiển thị**, không tự xác định nguồn gốc.

## Khác với kế hoạch cũ

Một số đề xuất lúc đầu gộp Translation Engine vào Mod Studio hoặc cho phép mod phụ thuộc loader bên ngoài; quyết định cuối cùng của dự án là **hai ứng dụng riêng và mod độc lập**. Ưu tiên quyết định hiện hành trên các bản thảo cũ trong `docs/legacy/`.
