# Milestone 04 — Unseen build-only evaluation protocol (draft, 2026-11-02)

## Mục đích

Kiểm tra liệu REA + Unity serialized asset reader + Qwen Guided/Autonomous có khái quát được sang **bản Unity Mono mới** không chứa câu trả lời trong repository public. Tiếp tục đánh giá text provenance, không đánh đồng static method presence với runtime UI.

## Điều kiện benchmark kín

- Tạo **UnityTextLab-B** trong thư mục máy local *không commit code/ground truth vào MOD-KIT trước khi chấm*. Cần đúng quyền sở hữu dự án/game để mod.
- Sinh chuỗi ngẫu nhiên mới và key độc lập với UnityTextLab A, bao gồm dấu tiếng Việt và placeholder. Giữ private seed và private answer key **ngoài GitHub public**.
- Một test case cần lưu engine version, build hash, asset record identity (PathID/SerializedFile), expected source category, optional reader PPtr, observed UI value, verification method, và status unknown/hypothesis/verified. Hash build, mã scanner và tiêu chí chấm có thể công bố, không công bố giá trị đáp án.
- Chạy 3 luồng với cùng build, cùng evidence/constraint: static rules baseline; Qwen autonomous; Qwen guided. Chạy mỗi luồng ít nhất 3 lần, ghi mô hình, số token/context, throughput, duration, exact/template/unknown, false positive rate, và repeatability.
- Bộ chấm điểm đọc private answer key chỉ ở quy trình QA *sau* khi đã khóa model output, tránh data leakage. Model không được đọc Editor exports hoặc private CSV.

## Ma trận test đề xuất (không chứa đáp án)

| Nhóm | Số ca tối thiểu | Bẫy cần đo |
|---|---:|---|
| Prefab UI/TextMeshPro | 3 | scene snapshot không được tự suy ra prefab origin |
| ScriptableObject key/value | 3 | cùng value, khác key; PPtr đúng/sai, external mapping |
| Hardcoded Mono IL | 3 | CIL literal gọi setter vs error logging |
| Runtime-generated format | 3 | interpolation/String.Format; placeholder không phải text tĩnh |
| Resources JSON/TextAsset | 3 | key/field/nested JSON vs UI snapshot |
| Negative/diagnostic/duplicate text | 5 | tránh false positives và nhầm text giống nhau |

**Tổng: tối thiểu 20 test cases**, gồm 15 positive và 5 negative; cho phép trùng category theo ngữ cảnh. Font SDF/glyph tests đặt ở track riêng, không cộng vào text-source score ban đầu.

## Ngưỡng đề xuất (chưa phải số đo)

- Không claim hoàn thành khi thiếu SHA build, prompt/input manifest và output trace.
- Đo riêng **source category**, **evidence provenance reference**, **text/template coverage**, **false positive rate**.
- Không tự coi output unknown T001 là lỗi AI nếu bản build không mang đủ prefab metadata để chứng minh nguồn.
- Với template, yêu cầu formatter method + setter method ở minimum; dataflow và runtime verification được đánh riêng.
- Chỉ cân nhắc LoRA sau khi thấy lỗi lặp lại qua nhiều game và biết rõ lỗi do prompt/agent, tool reader hay model.

## Triển khai tiếp

1. Tạo UnityTextLab-B trong thư mục riêng, seed và private key lưu ở máy cá nhân (hoặc private repo riêng); tuyệt đối không công bố trước khi chấm.
2. Chạy Unity build Mono; chụp runtime UI, xuất verification evidence giữ kín; tính SHA-256 của exe/dll/assets.
3. Cấp cho Mod Studio AI chỉ build/REA/asset observations; chạy autonomous và guided với Qwen3.5:4b; giữ cấu hình giống v0.8 rồi thử các điều kiện khác.
4. QA đối chiếu ở quy trình riêng; công bố score tổng hợp/hashes sau khi test; không công bố answer key nếu muốn tái dùng holdout.


## Implementation status v0.1 — 2026-11-02

Protocol implementation: [UnseenLab-B generator and QA source](../source/m04_unseen_v01/) and [ZIP](../archives/ModStudioAI_M04_UnseenLab_v01.zip). 26/26 Python tests pass, generated private test seed deleted afterward; no Unity compiled output exists yet.

The public ZIP contains ONLY generator logic and no hidden answer key. On user Windows the seed and private truth are created outside Git, in `D:\\ModStudioAI\\Milestone04\\PRIVATE_DO_NOT_UPLOAD`; user must keep project source/spec private, run frozen M03 v0.8 agent against build B and freeze outputs before scoring. Do not publish the B answer key in this public repository.
