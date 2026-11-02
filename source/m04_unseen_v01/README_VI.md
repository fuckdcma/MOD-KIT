# Mod Studio AI — Milestone 04 / UnityTextLab-B Unseen Holdout v0.1

**Phiên bản:** 2026-11-02 · **Phạm vi:** Unity Editor 6000.3.x / Windows x64 / Mono / TextMeshPro · **Trạng thái:** mã nguồn và Python tests đã chạy; **chưa biên dịch trong Unity trên máy Windows của bạn**.

## Mục đích và giới hạn

Không tiếp tục tối ưu prompt theo 5 câu của UnityTextLab-A. M04 tạo một **project UnityTextLabB riêng** với 20 trường hợp (15 text UI và 5 negative controls) bằng seed ngẫu nhiên 256-bit **được tạo lúc chạy trên máy bạn**. ZIP và public GitHub chứa **mã generator, bộ chấm, Unity Editor builder và test**, không chứa seed, chuỗi sinh ra hoặc đáp án. Private answer chỉ được tạo ở `D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD`.

**Không gửi source UnityTextLabB, `ProjectSettings/M04HoldoutLocal.json`, `seed_PRIVATE.hex`, `ground_truth_PRIVATE.json`, nhật ký chứa câu sinh ra hoặc `Outputs` lên repo public trước khi đã khóa các model outputs.** `M04HoldoutLocal.json` chứa labels thật và là dữ liệu riêng tư. Để chấm nghiêm túc, ngay cả trong ChatGPT cũng tránh tải các file này lên trong giai đoạn model chưa khóa kết quả.

## Các ca được tạo

| Nhóm | Số | Bản chất |
|---|---:|---|
| Prefab serialized + TMP | 3 | Prefab asset và scene instance; **không suy ra prefab origin từ scene snapshot** |
| ScriptableObject key/value | 3 | Bảng serialized, reader và liên kết key |
| Hardcoded CIL -> TMP setter | 3 | Literal trong method C# |
| Runtime-generated format -> TMP | 3 | `string.Format` với `{0}/{1}` và giá trị runtime |
| Resources JSON TextAsset | 3 | `Resources.Load`, `JsonUtility.FromJson` |
| Negative/diagnostic/unused | 5 | Debug.LogWarning, duplicate log text, unused table/JSON/CIL |
| **Tổng** | **20** | 15 positive / 5 negative |

20 case có ID trộn ngẫu nhiên, nội dung token bất ngờ, một số có tiếng Việt. Không lưu đáp án hay thứ tự lên GitHub public. Bộ sinh **không chứng minh mọi dữ liệu bị flatten vào build có thể được truy ngược về prefab asset**.

## Bước 1 — Tạo project Unity B tách biệt

Trong **Unity Hub**, dùng **Unity 6000.3.27f2** tạo một project 2D / Built-in mới tên **UnityTextLabB** tại:

`D:\ModStudioAI\UnityLab\UnityTextLabB`

Không clone hoặc ghi đè UnityTextLab-A. Vào project mới, cài/import **TextMeshPro Essential Resources**. Các script sẽ cần TMP và UnityEngine.UI.

Giải nén `ModStudioAI_M04_UnseenLab_v01.zip`, mở PowerShell tại thư mục giải nén và chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Create_M04_Local.ps1
```

Generator đòi project tồn tại và phiên bản Editor 6000.3.x. Nó từ chối nếu có file output cũ, đường dẫn project là UnityTextLab thay vì UnityTextLabB, hoặc private dir nằm trong project/Git worktree. Không hỗ trợ `--seed` trong CLI để tránh seed xuất hiện trong history. Kết quả trả về `eval_id` và `case_count=20`, **không in chuỗi private**.

Nếu đã tạo thành công, **không chạy lại** lên cùng project: muốn benchmark B2, tạo project mới và generator phiên bản mới.

## Bước 2 — Tạo scene và build Mono trong Unity Editor

Unity biên dịch các C# mới. Đợi hết Import/Compile lỗi trước khi làm tiếp. Ở menu:

- `Tools > Mod Studio AI > M04 > Generate Unseen Lab B Scene`
- Mở scene `Assets/M04/Scenes/UnseenLabB.unity`, nhấn Play; nhìn thấy 15 dòng UI; 5 negative không được sử dụng làm UI.
- Chọn **Windows x64 / Scripting Backend Mono** trong Player Settings, sau đó:
- `Tools > Mod Studio AI > M04 > Build Unseen Lab B Windows Mono`

Default build: `D:\ModStudioAI\Builds\UnityTextLabB\UnityTextLabB.exe`; DLL: `D:\ModStudioAI\Builds\UnityTextLabB\UnityTextLabB_Data\Managed\Assembly-CSharp.dll`.

Scene builder từ chối tạo lại nếu scene đã tồn tại để ngăn thay đổi benchmark sau khi bắt đầu. Build sử dụng Unity `BuildPipeline.BuildPlayer` trực tiếp; tùy Build Profile, yêu cầu Windows module đã được cài. **Chưa có kiểm thử compile/run Unity Editor trong container hiện tại**; nếu có compile error, gửi chỉ **thông báo lỗi, không kèm private source/spec/truth**.

## Bước 3 — Niêm phong hash build + chạy M03 v0.8 *đóng băng*

Không sửa `D:\ModStudioAI\Milestone03` hoặc các câu prompt để đạt điểm B. Các lệnh sau dùng `.venv` và mã M03 đã test với UnityTextLab-A, nhưng **đọc đường dẫn B riêng biệt**.

```powershell
# Chạy từ thư mục ZIP M04 đã giải nén
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04.ps1 -Mode seal
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04.ps1 -Mode rea
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04.ps1 -Mode evidence
```

`-Mode rea` dùng CLI `rea` đã cài từ M01–M03 và xuất `assembly_identity.json`, `members.json` mới vào `Milestone04\REA_B`; không ghi đè báo cáo A. `-Mode evidence` dùng **M03 v0.8** để xuất `Runs_LOCAL/AgentInput/rea_evidence.jsonl`, `build_assets.json`, cùng `Runs_LOCAL/Outputs/baseline_r01.json` và `provenance_links.json`. Nếu scanner không hiểu lớp ScriptableObject tên mới, **giữ nguyên trạng thái unknown**; đó là dữ liệu cho nghiên cứu M04, không phải lỗi cần sửa trước khi chấm.

> Nếu bạn dùng REA ở vị trí khác PATH, hãy tự xuất 2 file `members.json` và `assembly_identity.json` theo cú pháp REA bạn đã dùng trước đây vào `D:\ModStudioAI\Milestone04\REA_B`, rồi bỏ qua lệnh `-Mode rea`.

## Bước 4 — Chạy Qwen 3.5 4B local (mỗi chiến lược 3 lượt)

Cần Ollama `qwen3.5:4b` đã có và API localhost ở port 11434:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04.ps1 -Mode probe
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04.ps1 -Mode autonomous -Repeats 3
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04.ps1 -Mode guided -Repeats 3
```

Tệp xuất là `Outputs/autonomous_r01.json`, `...r02.json`, `...r03.json`, `guided_r01.json`, ...r03.json`; **không ghi đè** nếu đã tồn tại. Lượt không `completed:true` không được tính là đúng hoặc 0/20; giữ trace và phân loại lỗi vận hành. Đánh giá gồm 3 runs/strategy, không gộp guided và autonomous.

**Không chạy evaluator M03** với `ground_truth_v01.csv` cũ; nó chứa đáp án UnityTextLab-A và có thể sai khi dùng B.

## Bước 5 — Chấm riêng tư sau khi đã khóa tất cả lượt model

Sau khi đã có 3 lượt guided + 3 lượt autonomous **hoàn tất**, chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Evaluate_M04_Private.ps1
```

Script sao chép bản gốc có SHA256 vào `PRIVATE_DO_NOT_UPLOAD\locked_predictions_YYYYMMDD_HHMMSS`, tạo `metrics_PRIVATE_*.json` (có chi tiết case, **không tải lên**), và `Runs_LOCAL\metrics_public_AGGREGATE_ONLY.json` (chỉ có tổng và SHA; có thể chia sẻ sau chấm).

Bộ chấm M04 phân biệt `source_and_text_matches` với `observed_supported_matches` (bằng chứng method/asset mức tĩnh). **Chúng không chứng minh dataflow hay UI runtime**. Prefab yêu cầu nguồn prefab asset thực sự, không phải `level0#path_id`. Duplicate log text mơ hồ được báo riêng, không tùy tiện kết luận sai/đúng chỉ vì chuỗi giống UI.

## Dữ liệu được và không được chia sẻ

- Có thể chia sẻ sớm: mã generator M04, log kiểm thử không chứa nội dung case, hash build/REA, `metrics_public` sau chấm.
- Chỉ sau khi mô hình đã tạo và khóa outputs: Agent traces, UnityPy JSON và REA evidence có thể được dùng để kiểm toán, nhưng nếu muốn tái sử dụng holdout kín thì **không công bố các chuỗi đó trên GitHub public**.
- Không chia sẻ: seed, private truth, `ProjectSettings/M04HoldoutLocal.json`, Unity source generated có literal riêng, private metrics per-case.

## Giới hạn v0.1

- Python tests xác minh generator, cấu trúc C# bằng kiểm tra tĩnh, cách chấm và policy; **không tương đương Unity Editor compilation**.
- Hardcoded scriptable class detection trong M03 v0.8 chưa khái quát hóa; giữ nguyên để đo generalization. Cần report lỗi scanner nếu gây exception thật.
- M04 không tạo runtime hook/mod/font SDF. Kết quả text provenance và font track cần được chấm riêng.
- Giữ các file/private answers ngoài GitHub public (repo `fuckdcma/MOD-KIT`).
