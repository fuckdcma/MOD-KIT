# Mod Studio AI — Milestone 02 / Text Provenance Collector v0.1

**Phù hợp UnityTextLab Unity 6.3 (6000.3.27f2), Mono, TextMeshPro.** Bộ mã này chỉ phục vụ nghiên cứu trong project Unity Editor do bạn sở hữu. Không chứa hook, injector, BepInEx hay Harmony; không sửa asset của game.

## Mục tiêu

1. Xuất **evidence từ Unity Editor** (đáp án tham chiếu) cho: (a) TMP trong prefab; (b) TMP trong scene; (c) ScriptableObject có `entries[]` chứa `key` và `value`; (d) Resources JSON `{ "id": "...", "message": "..." }`.
2. Ghi font name, shared material, shader, font atlas và material `_MainTex` của các TMP component. `atlas_status=match` chỉ chứng minh cùng texture trong Editor, KHÔNG chứng minh dấu tiếng Việt render đúng.
3. Ghép nguồn evidence với **REA managed CIL** (không thực thi game) trong một bước Python ngoại tuyến.
4. Nếu có `ground_truth_v01.csv`, xuất báo cáo đánh giá **riêng tư**; không đưa đáp án vào input bài kiểm thử mù.

## Bước 1 — Sao lưu và cài file Editor

1. Đóng Play Mode; **File > Save Project** và **Ctrl+S** lưu scene hiện tại.
2. Sao lưu thư mục project UnityTextLab hoặc commit Git trước khi cài tool.
3. Giải nén ZIP này. Copy file `Assets/Editor/ModStudioTextProvenanceCollector.cs` vào:

   `D:\ModStudioAI\UnityLab\UnityTextLab\Assets\Editor\ModStudioTextProvenanceCollector.cs`

   Nếu `Assets/Editor` chưa tồn tại, hãy tạo thư mục mới.
4. Quay lại Unity Editor, chờ biên dịch. Nếu Console có lỗi, **dừng tại đây** và chụp nguyên lỗi; không sửa bừa các script đang chạy.

**Không chép file trong `Assets/Editor` vào thư mục build `UnityTextLab_Data/Managed`.** Script này chỉ hoạt động trong Unity Editor và không được đưa vào bản game.

## Bước 2 — Xuất bằng chứng

1. Trong Unity Editor, mở menu **Tools > Mod Studio AI > Export Text Provenance v0.1**.
2. Nếu Unity hỏi lưu scene đã sửa, chọn Save để dữ liệu khớp với file trên đĩa. Chọn Cancel sẽ ngừng quét.
3. Công cụ duyệt prefab/scene dưới `Assets/`, ScriptableObject `entries[]`, và `*.json` trong `Assets/**/Resources/`. Không chỉnh sửa nội dung những asset này.
4. Tool tự mở thư mục kết quả. Nếu không tự mở, xem trong project:

   `D:\ModStudioAI\UnityLab\UnityTextLab\ModStudioExports\provenance_YYYYMMDD_HHMMSS_mmm\`

   Có 3 file:
   - `text_provenance.jsonl`: từng nguồn text và dữ liệu font liên quan.
   - `manifest.json`: số record theo từng nhóm, Unity version, giới hạn bộ quét.
   - `warnings.txt`: lỗi/asset chưa hỗ trợ (nếu có).

**Kỳ vọng:** ít nhất 1 `prefab_tmp_serialized`, 5 `scene_tmp_serialized`, 1 `scriptable_object_kv`, 1 `resources_json_message`; có thể nhiều hơn vì bộ quét quét toàn bộ project, kể cả TMP mẫu của package/assets. Trạng thái có thể thay đổi theo bố cục project. Nếu prefab chưa được lưu thành asset thật, `prefab_tmp_serialized` có thể bằng 0.

### Phân biệt các nguồn

- `scene_tmp_serialized`: text trong scene tại thời điểm editor quét. Với các đối tượng được script ghi lại khi chạy (`Quest Completed`, `Health`), scene có thể vẫn lưu `...`; **đó không phải lỗi**, vì nguồn runtime được tìm bằng REA.
- `prefab_tmp_serialized`: text trực tiếp của **prefab asset**, khác với prefab instance trong scene nếu bị override.
- `scriptable_object_kv`: `key`/`value` trong `entries[]` được tuần tự hóa.
- `resources_json_message`: chỉ hỗ trợ cấu trúc LabDialogue `id`/`message` trong v0.1. JSON array, localization nhiều ngôn ngữ, binary Unity bundles chưa hỗ trợ.

## Bước 3 — Ghép với REA (không cần chạy REA lần nữa)

Yêu cầu Python 3.10+ trên Windows. Không cần pip thêm thư viện.

Dùng PowerShell (chỉnh `$project` nếu UnityLab ở vị trí khác):

```powershell
$project = 'D:\ModStudioAI\UnityLab\UnityTextLab'
$latest = Get-ChildItem "$project\ModStudioExports" -Directory |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

$tool = 'D:\ModStudioAI\Research\Milestone02\analyze_provenance.py'
$rea  = 'D:\ModStudioAI\Research\REA'
$gt   = 'C:\Users\HP\Desktop\ModStudioAI_Starter_v01\ModStudioAI_Starter_v01\Datasets\ground_truth_v01.csv'
$out  = 'D:\ModStudioAI\Datasets\Milestone02_Review'

python $tool --collector "$($latest.FullName)\text_provenance.jsonl" `
    --members "$rea\members.json" `
    --assembly "$rea\assembly_identity.json" `
    --ground-truth $gt `
    --out $out
```

Lưu ý: trước khi chạy, **copy** `Tools/analyze_provenance.py` trong ZIP vào `D:\ModStudioAI\Research\Milestone02\analyze_provenance.py` (tạo folder nếu chưa có). Kiểm tra lại đường dẫn ground_truth trên máy.

### Đầu ra của Python

- `model_input_rea_evidence.jsonl`: phân tích CIL REA, thích hợp làm **evidence cho thử nghiệm mù** (không có ground truth).
- `REFERENCE_editor_evidence_DO_NOT_USE_IN_BLIND_TEST.jsonl`: dữ liệu từ project nguồn, **chỉ để đối chiếu**, KHÔNG đưa cho AI khi kiểm tra khả năng tự tìm nguồn text bằng bản build.
- `PRIVATE_ground_truth_review.csv`: đối chiếu 5 case đã biết; **không phải nhãn train tự động**, cần người duyệt.
- `evidence_manifest.json`: hash của assembly theo REA, số record và các giới hạn.

Nếu SHA-256 trong `assembly_identity.json` và `members.json` không khớp, script sẽ **báo lỗi và dừng**. Bạn cần cung cấp hai file cùng một bản build.

## Bước 4 — Kiểm tra các case T001–T005

| Case | Kết quả từ Editor/REA cần kiểm tra |
|---|---|
| T001 | Prefab asset `Prefab_NewGame` có `New Game`; scene instance có thể ghi nhận riêng. |
| T002 | ScriptableObject: `menu.load` -> `Load Game`. |
| T003 | REA: `HardcodedTextExample.Awake`, literal `Quest Completed`, gọi `TMP_Text.set_text`. |
| T004 | REA: `RuntimeTextExample.Refresh`, format `Health: {0}/100`; runtime có thể hiển thị 75/100, 65/100... |
| T005 | Resources JSON: `npc.commander.greeting` -> `Hello, Commander`; REA ghi nhận luồng Resources/JsonUtility. |

Trong output Python, `found_candidate` **chỉ** có nghĩa bộ đối chiếu tìm thấy bằng chứng tương ứng, **không** xác nhận AI đã tự tìm đúng hoặc hook hoạt động.

## Cần gửi lại gì?

- 3 file `text_provenance.jsonl`, `manifest.json`, `warnings.txt` do Unity Editor xuất ra.
- Tùy chọn: `PRIVATE_ground_truth_review.csv` sau bước Python.
- Nếu gặp lỗi compile, gửi ảnh Unity Console và 3–5 dòng đầu tiên của lỗi.

## Phạm vi/an toàn dữ liệu

- Chỉ chạy trong Unity Editor của project lab; không có thao tác ghi vào scene, prefab, ScriptableObject hoặc executable.
- Một số API Unity khi mở scene/prefab để đọc có thể kích hoạt callback của script Editor hoặc `OnValidate` trong project. Tool **không chủ động lưu** những thay đổi đó. Sao lưu trước khi chạy.
- Không scan game thương mại/online hoặc anti-cheat trong bước này.
- Chỉ dữ liệu do bạn chủ động upload mới đi ra khỏi máy. Script không gửi dữ liệu lên Internet.
- Chưa hỗ trợ Unity IL2CPP, Unreal, asset bundles, font atlas rendering test, hoặc hook.

## Kiểm thử đã thực hiện bởi người tạo gói

- Python tool: `python -m unittest discover -s Tests -v` — 3 kiểm thử chạy đạt (định dạng JSONL, matcher template Health, đọc REA đã tải lên).
- Đã chạy mô phỏng ghép 3 editor records giả lập + hai tệp REA thực tế và 5 ground-truth case, kết quả đối chiếu 5/5 **trong mô phỏng**. Không được coi là kết quả export Unity thực tế.
- **Chưa thể biên dịch C# trong Unity 6.3 tại môi trường này**. Cần chạy menu trong Unity project trên PC của bạn để xác nhận tương thích và số record thực.

## Tài liệu Unity đã đối chiếu

- `AssetDatabase.FindAssets` — docs.unity.com/en-us/engine/6000.7/script-reference/unityeditor/assetdatabase/findassets
- `PrefabUtility.LoadPrefabContents / UnloadPrefabContents` — docs.unity.com/en-us/engine/6000.7/script-reference/unityeditor/prefabutility/loadprefabcontents
- `AssetDatabase.TryGetGUIDAndLocalFileIdentifier` — docs.unity.cn/6000.0/Documentation/ScriptReference/AssetDatabase.TryGetGUIDAndLocalFileIdentifier.html
- `EditorSceneManager.OpenScene` `OpenSceneMode.Additive` — docs.unity.com/en-us/engine/6000.0/script-reference/unityeditor/scenemanagement/openscenemode
