# Chat handoff — Mod Studio AI (2026-11-02)

## Hướng dẫn cho AI ở phiên trò chuyện mới

Đây là hồ sơ chuyển giao kỹ thuật. Trước khi đưa quyết định mới, hãy đọc `ARCHITECTURE_DECISIONS.md`, `PROGRESS.md`, `M03_LATEST_FINDINGS.md`, và các JSON trong `evidence/m03/latest/`. Không khẳng định đã chạy Qwen, hook hay fine-tuning khi chưa có log kiểm chứng. Không dùng `benchmarks/reference_DO_NOT_FEED_MODEL` làm đầu vào của agent lúc đánh giá.

## Sản phẩm và nguyên tắc

- Mod Studio AI và Translator/Localization Studio **là hai ứng dụng riêng**.
- Mod Studio phải tự tìm nguồn text: scene/prefab, ScriptableObject/string table, hardcoded CIL, runtime-generated, JSON/custom manager; lưu provenance gồm asset/object/field/method và mức bằng chứng.
- Mod đầu ra phải hoạt động **độc lập**, không bắt người dùng cài BepInEx/Harmony/MelonLoader/Mod Studio AI. REA là công cụ nghiên cứu, không là loader.
- Định hướng Hook Text & Font Mapping **1:1**, ID/ngữ cảnh ưu tiên hơn exact string; bảo toàn placeholder, rich-text, lifecycle.
- Font SDF: kiểm tra font asset, glyph coverage, atlas, material, shader, padding, gradient/sampling, fallback, clipping và overwrites. Không khẳng định một kỹ thuật chữa được mọi game.
- Unity Mono trước; Unity IL2CPP rồi Unreal. Offline và các tình huống có quyền mod; không bypass anti-cheat.
- REA (npm `rea-agents`) lấy bằng chứng managed metadata/callgraph; UnityPy + TypeTreeGeneratorAPI đọc asset serialized.
- AI lõi dự kiến Qwen3.5-4B, inference local qua llama.cpp Vulkan trên RX 6700 XT 12 GB. LoRA trên cloud khi đủ dữ liệu verified; không fine-tune sớm. RAG phục vụ tài liệu.

## Máy thử nghiệm và đường dẫn Windows

- Windows 11; Unity Editor 6000.3.27f2, Mono Windows x64.
- `D:\ModStudioAI\UnityLab\UnityTextLab` — project Unity nguồn.
- `D:\ModStudioAI\Builds\UnityTextLab\UnityTextLab_Data` — bản build Unity Mono.
- `D:\ModStudioAI\Research\REA` — các báo cáo REA.
- `D:\ModStudioAI\Milestone03` — tool Python; `.venv\Scripts\python.exe` là Python 3.12.10 x64; UnityPy 1.25.4; tpk_ar 0.2.4; TypeTreeGeneratorAPI 0.0.10 trong lần scanner v0.2.
- Model Qwen chưa có bằng chứng chạy thực tế.

## UnityTextLab 5 case chuẩn

| Case | Giá trị | Nguồn thiết kế |
|---|---|---|
| T001 | New Game | Serialized prefab TMP |
| T002 | Load Game | LabStringTable ScriptableObject: menu.load |
| T003 | Quest Completed | ModStudioLab.HardcodedTextExample.Awake |
| T004 | Health: {0}/100, snapshot 75/100 | RuntimeTextExample.Refresh |
| T005 | Hello, Commander | Resources/dialogue.json, key message |

Game đã chạy, Player.log có `sameAtlas=True` cho LiberationSans SDF / LiberationSans SDF Material; vẫn chưa kiểm tra Việt glyph. REA: Assembly-CSharp.dll SHA256 ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e, 16 methods, 9 type defs, 14 fields.

## Kết quả gần nhất

- **M01:** game lab, ảnh UI, 2 báo cáo REA, Player.log đều có; text hiển thị; runtime Health đổi theo thời gian.
- **M02:** Editor Collector xuất 8 record: 5 scene TMP, 1 prefab TMP, 1 ScriptableObject, 1 Resources JSON; 0 cảnh báo; đủ 5 case khi đối chiếu với ground truth.
- **M03 v0.1:** REA CIL chứng minh hardcoded + template; UnityPy scan bản đầu tìm JSON, nhưng 32 lỗi MonoBehaviour.
- **M03 v0.2, JSON mới nhất 2026-11-02:** quét 6 file; **32/32 MonoBehaviour decoded**, 5/5 TextAsset decoded; 7 asset observations, 0 errors, 0 raw candidates; TypeTreeGenerator loaded Unity 6000.3.27f2.
- Giá trị `New Game` ở `level0#path_id=35` trong `TMP_Text.m_text`, **không chứng minh asset prefab nguồn**.
- `Load Game` ở `level0#path_id=31` (TMP UI) và `sharedassets0.assets#path_id=16` (`ModStudioLab.LabStringTable.entries[0].value`), hiện source_type='unknown' trong scan. Có bằng chứng lớp ScriptableObject, nhưng evaluator chưa xác nhận toàn bộ provenance.
- `Quest Completed` và `Health: 75/100` cũng trong scene TMP; đây là snapshot UI, không phải nguồn gốc; REA mới chứng minh hardcoded và dynamic template.
- `Hello, Commander` trong `resources.assets#path_id=9`, `TextAsset dialogue.message` chứng minh external JSON.
- Evaluator v0.2 vẫn **2 exact + 1 template + 2 not_proven**. Không sửa điểm bằng cách đoán. M03 là **rule-based tool baseline**, chưa đánh giá AI.

## Công việc kế tiếp ưu tiên

1. Nâng cấp provenance linker: nối `LabStringTable.entries[0].value` với `TableTextExample.Start -> LabStringTable.TryGet`, lấy key thật `menu.load` từ asset và xác minh T002.
2. Với T001, phân biệt `level0` scene TMP, đối tượng thuộc prefab/instance và serialized prefab origin bằng object identity + prefab relationship; chỉ nâng điểm khi chứng minh được.
3. Kết hợp REA + asset scanner để tạo report `observed/likely/unproven` có bằng chứng cụ thể và hạn chế.
4. Sau khi tool có năng lực kiểm chứng đáng tin, chạy Qwen3.5-4B GGUF bằng llama.cpp Vulkan localhost, đo first baseline agent chưa fine-tune.
5. Mở rộng lab bằng các ca SDF known-good/known-bad, glyph Việt, dynamic string, trùng chuỗi đa ngữ cảnh, material overwrite.
6. Chuẩn hóa case provenance/version/hash, giữ holdout riêng theo game; không đưa ground truth của build này vào prompt đánh giá.

## Lưu trữ

Repo này là **public**. Các file từ ChatGPT chưa được commit đầy đủ (đặc biệt các ZIP tool, ảnh screenshot, thư mục code giải nén) được nêu trong `ARTIFACT_INDEX.md`. Có công cụ `tools/Sync_Local_Artifacts.ps1` để người dùng tự đồng bộ nguồn local sau khi kiểm tra. Hồ sơ này không phải bản sao nguyên văn toàn bộ cuộc chat.


## Cập nhật v0.3 — cuối ngày 2026-11-02

Đã phát triển, test Python **22/22 đạt** và commit [Provenance Linker v0.3](../source/m03_provenance_v03/) cùng [ZIP cài đặt](../archives/ModStudioAI_M03_Provenance_Fix_v03.zip). Bản này đọc key/value serialized trên cùng `LabStringTable`, bảo toàn `TableTextExample.key` và PPtr dưới dạng metadata, phân loại `TMP_Text.m_text` là UI snapshot; không tự nhận prefab origin hoặc runtime binding. Cần **cài bản v0.3 trên máy Windows rồi scan-assets mới**. Trên JSON v0.2 đã được người dùng gửi, điểm vẫn **2 exact / 1 template / 2 unproven**; chỉ khi JSON v0.3 có paired key từ build mới có khả năng nâng T002 lên source+text proven. **Chưa có log thực tế v0.3.**

Chạy PowerShell trong `D:\\ModStudioAI\\Milestone03`: `tests` → `scan-assets` → `provenance` → `baseline` → `evaluate`, theo README tại `source/m03_provenance_v03/README_VI.md`. Gửi `build_assets.json`, `provenance_links.json`, `evaluation_private.json` để tiếp tục.
