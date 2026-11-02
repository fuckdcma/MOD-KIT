# Mod Studio AI — Báo cáo Milestone 02 (Collector + REA)

**Đầu vào:** `provenance_20261102_005843_135.rar` (Unity Editor Collector, `created_utc=2026-11-02T00:58:43.1637733Z`); `members.json`, `assembly_identity.json` từ REA; `ground_truth_v01.csv` của UnityTextLab.

## Kết quả kiểm tra dữ liệu

- File nén đọc được; 3 tệp: `manifest.json`, `text_provenance.jsonl`, `warnings.txt`.
- Manifest: `schema=modstudio.provenance.v0.1`, Unity `6000.3.27f2`, 8 records, 0 warnings.
- Bằng chứng: **5** `scene_tmp_serialized`, **1** `prefab_tmp_serialized`, **1** `scriptable_object_kv`, **1** `resources_json_message`.
- Trùng `record_id`: **0**. Hash SHA-256 nội dung text: **8/8 đúng**. Toàn bộ `verification=observed_not_validated` (theo thiết kế).
- Font: 6/6 record TMP có `atlas_status=match`; 2 record dữ liệu phi-TMP có `atlas_status=unknown`. Đây chỉ là snapshot trong Editor; không chứng minh hỗ trợ dấu Việt hay trạng thái runtime của tất cả UI.
- Đối chiếu REA: 2 báo cáo REA cùng SHA-256 assembly: `ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e`. Bộ phân tích xuất **6** method-level traces có literal hoặc thao tác với setter của TextMeshPro.

## Đối chiếu 5 trường hợp gốc

| Case | Nguồn kỳ vọng | Bằng chứng ứng viên tìm được | Kết quả |
|---|---|---|---|
| T001 — New Game | Prefab serialized | `Assets/Prefabs/Prefab_NewGame.prefab`; instance `Canvas/Prefab_NewGame` có `prefab_text_difference=same` | `found_candidate` |
| T002 — Load Game | ScriptableObject | `Assets/LabStringTable.asset`, `menu.load → Load Game`; REA thấy `LabStringTable.TryGet()` và `TableTextExample.Start()` | `found_candidate` |
| T003 — Quest Completed | Managed hardcoded | REA `ModStudioLab.HardcodedTextExample.Awake` có literal và gọi `TMP_Text.set_text` | `found_candidate` |
| T004 — Health: 75/100 | Runtime-generated | REA `ModStudioLab.RuntimeTextExample.Refresh` có `Health: {0}/100`, `String.Format` và `TMP_Text.set_text` | `found_candidate` |
| T005 — Hello, Commander | Resources JSON | `Assets/Resources/dialogue.json`, `npc.commander.greeting`; REA `ExternalTextExample.Start` gọi Resources/JSON/TMP | `found_candidate` |

**Diễn giải đúng:** 5/5 chỉ là tỷ lệ **tìm được bằng chứng ứng viên** trong project laboratory. Đây **không phải** độ chính xác của model AI và không chứng minh hook đã thực hiện thành công. Mọi dòng `PRIVATE_ground_truth_review.csv` vẫn có `review_status=HUMAN_REVIEW_REQUIRED`.

## Các giới hạn cần giữ rõ

1. Một chuỗi đã được lưu trong scene (`Quest Completed`, `Health: 75/100`) không nhất thiết có nguồn thực là scene. Code có thể gán đè lúc chạy; dùng REA và runtime để quy kết nguồn.
2. Snapshot prefab instance và prefab asset đều là cùng `New Game`, không phải hai câu độc lập để dịch.
3. Token/địa chỉ method của REA chỉ có giá trị với SHA-256 và MVID của bản build đã phân tích.
4. `atlas_status=match` không kiểm tra shader parameters, material overrides, missing Vietnamese glyphs hoặc lỗi SDF sau khi hook.
5. Chưa có phép đo model nền Qwen và chưa train LoRA. Tệp Editor reference và private ground truth tuyệt đối không được đưa vào prompt đánh giá mù.

## Bước tiếp theo — Milestone 03

- Tạo **Build-Only Text Discovery Agent**: chỉ cho model tiếp cận bản build Unity Mono và các công cụ phân tích tĩnh đã cho phép (REA cho CIL, bộ đọc Unity serialized assets chỉ đọc); không cho model thấy project nguồn, Editor Collector output hoặc ground-truth.
- Agent xuất `candidate_text_provenance.jsonl` với source type, string/key, phương thức đọc, bằng chứng, mức chắc chắn, và `unknown` nếu thiếu chứng cứ.
- Bộ evaluator bên ngoài so sánh với 5 case và mở rộng dự án lab thêm 2–3 scene mới để chống học thuộc. Sau đó mới xác lập benchmark model nền và dữ liệu train.