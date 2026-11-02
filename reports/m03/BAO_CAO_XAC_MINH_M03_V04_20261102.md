# Xác minh Milestone 03 — Pointer Resolver v0.4 / UnityTextLab Windows

Ngày: **2026-11-02**. Nguồn: file `Outputs.rar` do người dùng gửi (RAR5), chứa bốn JSON. File gốc và SHA-256 được lưu cùng báo cáo; không sử dụng dữ liệu Unity Editor trong phần provenance.

## Trạng thái đã xác minh

| Chỉ số | Đầu ra Windows v0.4 |
|---|---|
| Schema | `modstudio.m03.v0.4` |
| File build Unity được quét | 6/6 |
| MonoBehaviour decoded | 32/32 |
| TextAsset decoded | 5/5 |
| Asset observations | 7 |
| Reader bindings | 1 |
| Resolved reader pointers | 1 |
| Scan errors | 0 |
| Raw candidate count | 0 |

### T002 — nguồn được nối qua PPtr có bảng externals

- Reader: `level0#path_id=40` — `ModStudioLab.TableTextExample`, `reader_key=menu.load`.
- Serialized PPtr: `m_FileID=3`, `m_PathID=16`.
- External mapping của **level0**: `externals[2] → sharedassets0.assets`.
- Target: `sharedassets0.assets#path_id=16`, `ModStudioLab.LabStringTable`, `entries[0].key=menu.load`, `entries[0].value=Load Game`.
- `binding_status=serialized_pointer_resolved`, `resolution_evidence.proof_kind=build_serialized_pointer_not_runtime_behavior`.
- REA còn cho thấy luồng gọi phương thức `ModStudioLab.TableTextExample.Start → ModStudioLab.LabStringTable.TryGet` và `TMP_Text.set_text`. Đây là bằng chứng tĩnh; **không chứng minh TryGet đã chạy hoặc giá trị mapping đã đổi tại runtime**.

### Case kiểm thử

| Case | Tên | Đánh giá hiện tại |
|---|---|---|
| T001 | New Game | **not_proven**: `level0#path_id=35` là UI TMP serialized snapshot, không có prefab-origin proof |
| T002 | Load Game | **exact_text**: Source ScriptableObject key/value + serialized PPtr resolved |
| T003 | Quest Completed | **exact_text**: CIL hardcoded |
| T004 | Health: {0}/100 | **template_text**: định dạng động, không được coi snapshot là text nguồn bất biến |
| T005 | Hello, Commander | **exact_text**: Resources TextAsset JSON |

**Evaluator = 3/5 exact + 1/5 template + 1/5 not_proven.** Không thay đổi điểm tổng so với v0.3, vì v0.3 đã xác minh nguồn T002; v0.4 **nâng mức độ bằng chứng về liên kết** chứ không thêm text nguồn mới.

## Kiểm thử tái tạo

- Python unit tests v0.4: **34/34 đạt** khi chạy lại tại đây.
- Dùng đúng code v0.4 + `AgentInput/rea_evidence.jsonl` + `build_assets.json` upload, chạy lại `provenance`, `baseline`, `evaluate`: **3/3 tệp JSON có nội dung semantic khớp hoàn toàn** với đầu ra người dùng tải lên.
- Khác biệt byte chỉ do newline Windows CRLF so với Linux LF; không có khác biệt nội dung JSON.
- Chưa trực tiếp mở/reparse file Unity build trên PC trong môi trường này; chứng cứ external table là từ `build_assets.json` do scanner người dùng chạy. Đối chiếu rule/logic trong mã nguồn v0.4 và test xác thực, không tự khẳng định đã chạy Unity engine ở đây.

## Bước tiếp theo hợp lý

1. Lưu trạng thái `serialized_pointer_resolved` ở canonical provenance schema cho T002 và cấm suy đoán runtime.
2. **T001**: cần chứng minh xuất xứ prefab ở mức build-only, có thể không khôi phục asset path ban đầu sau khi Unity build flatten prefab. Giữ `not_proven` nếu thiếu metadata chứng thực.
3. Chạy Qwen nền **chưa fine-tune** qua llama.cpp localhost để có baseline AI; tuyệt đối không đưa `PrivateEvaluation`, `ground_truth`, hoặc Editor provenance vào model prompt. Vì repo đang public, bài lab chỉ là smoke test công khai, không phải blind holdout chống contamination.
4. Nếu muốn xác minh runtime binding, xây telemetry trong game lab tự sở hữu, không nhảy từ bằng chứng serialized sang khẳng định hook đã thành công.

Manifest: `SHA256_MANIFEST.json` cho bốn JSON + RAR gốc. Biên bản này không là xác minh blind AI.
