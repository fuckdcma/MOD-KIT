# MOD Studio AI — M04 Evidence-Grounded Agent v1.0 (experimental)

**Ngày:** 2026-11-02  
**Thành phần:** Unity Mono / REA / UnityPy build-only evidence / Ollama `qwen3.5:4b` local  
**Trạng thái:** **24/24 kiểm thử synthetic Python PASS**, CHƯA chạy thật trên Windows/Ollama UnityTextLab-B. **KHÔNG thay thế M03 v0.8**.

## Vì sao cần bản này?

M04 B đã được chấm riêng tư: Static Baseline v0.8 **3/15 khớp có bằng chứng**, 1 false-positive claim; Guided v0.8 **3/15 khớp text + nguồn nhưng 0/15 khớp được validator xác nhận**, 1 false-positive; Autonomous Bounded v0.9 **1/15 có bằng chứng**, 0 false-positive, hoàn tất 3/3. Guided 11/11 nhận định mỗi lần bị từ chối; riêng `guided_r01` bị từ chối do 6 method không có ldstr chỉ định, 4 asset không khớp bằng chứng và 1 loại evidence thiếu/sai.

**Mục tiêu v1.0:** hạn chế hallucination và liên kết sai method/asset bằng cách để model chọn từ **catalog bằng chứng có ID ổn định**; program lấy tất cả trường nội dung và provenance trực tiếp từ đúng bản ghi REA/UnityPy. **Không hứa cải thiện recall hay điểm B** trước khi chạy và chấm thật.

## Cơ chế

1. Tái sử dụng mã validator của **M03 v0.8 đóng băng** qua import động *read-only*. Không copy/chỉnh file M03 trên máy.
2. Thu thập các IL literal nằm trong method có `TMPro.TMP_Text.set_text`. Format template có `{0}` chỉ được phân loại `runtime_generated` khi method có `System.String.Format`. Chú ý: cùng method không chứng minh luồng IL stack vào setter.
3. Nhận các field JSON text được đọc thực từ `TextAsset`; nhận `scriptable_object` chỉ khi **validator đóng băng** có đủ ScriptableObject class/key/value proof. Bản scanner M03 v0.8 chưa tổng quát hóa lớp M04, nên **các field `unknown` tiếp tục bị loại**, không suy diễn nguồn từ PathID hoặc UI scene snapshot.
4. Tạo ID `EV_<hash>` từ **text + nguồn + method + token/offset REA hoặc đường dẫn field**; Qwen nhận từng batch <=10 và trả về chỉ `{ "select": ["EV_..."] }`. Mọi ID sai, trùng, JSON bị cắt, field lạ => retry hoặc `completed:false`; không tự tạo string, tên method, asset path hay confidence từ model.
5. File output chứa quan sát được validator frozen xác nhận `validation_status=observed`, và trace kỹ thuật **không ghi prompt hoặc nội dung candidate**. Chấm M04 sau này phải tách riêng vì đây là **Agent khác phiên bản**.

### Giới hạn minh bạch

- Qwen có thể bỏ sót ứng viên đúng hoặc chọn cả JSON chỉ dùng để log; `observed` là chứng cứ tĩnh, **không phải proof runtime**.
- Không cố gán nhãn prefab/ScriptableObject với một TMP snapshot `unknown`; cần scanner/provenance engine versioned mới và chain of pointers/bindings có thể kiểm chứng.
- Trong một method có cả `Debug.LogWarning` và TMP setter, trùng literal vẫn có thể là false positive do không chứng minh dataflow.
- B cũ đã từng lộ vài chuỗi qua screenshot và đã bị dùng nhiều lần điều chỉnh; **chỉ dùng B để kiểm thử hồi quy**, không gọi nó là unseen benchmark mới.
- Không sử dụng network ngoài Ollama localhost. Không đọc seed, Unity project B hay private ground truth.

## Chạy trên Windows 11

Giải nén ZIP, mở PowerShell tại thư mục có `Scripts`, `src`, `tests`. Giữ nguyên thư mục:

`D:\ModStudioAI\Milestone03\src\modstudio_m03.py`  
`D:\ModStudioAI\Milestone04\Runs_LOCAL`  
`D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_BOUNDED_V09_LOCAL`  
`D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD`

**Bước A — kiểm tra bằng chứng (không chạy Qwen, không tạo thư mục kết quả):**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04_EvidenceGrounded_v10.ps1 -PreflightOnly
```

In JSON chỉ có số lượng candidate và loại nguồn. Bảo đảm M03 v0.8 SHA và REA/UnityPy seal đều khớp.

**Bước B — chạy 3 lần Qwen theo ID, thư mục mới (sau khi A không lỗi):**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04_EvidenceGrounded_v10.ps1
```

Tạo riêng: `D:\ModStudioAI\Milestone04\Runs_EVIDENCE_GROUNDED_V10_LOCAL`  
Kết quả: `Outputs\evidence_r01.json` đến `evidence_r03.json`; tự dừng khi có lượt incomplete. Script từ chối ghi đè thư mục đã tồn tại. Nếu chạy lại phiên bản có thay đổi, chọn **`-NewRunsDir` khác**, giữ nguyên kết quả cũ.

**Bước C — báo cáo số đếm an toàn:**

```powershell
$out='D:\ModStudioAI\Milestone04\Runs_EVIDENCE_GROUNDED_V10_LOCAL\Outputs'
Get-ChildItem $out -Filter 'evidence_r??.json' | Sort-Object Name | ForEach-Object {
  $r=Get-Content $_.FullName -Raw | ConvertFrom-Json
  [pscustomobject]@{
    Run=$_.BaseName; Completed=$r.completed
    Candidates=$r.evidence_catalog_count
    Selected=@($r.observations).Count
    Observed=@($r.observations | Where-Object {$_.validation_status -eq 'observed'}).Count
    ProtocolErrors=@($r.trace | Where-Object {$_.status -eq 'model_protocol_error'}).Count
  }
} | Format-Table -AutoSize
```

**Bước D — kiểm thử synthetic:**

```powershell
& 'D:\ModStudioAI\Milestone03\.venv\Scripts\python.exe' -m unittest discover -s .\tests -v
```

Kiểm thử yêu cầu M03 v0.8 cài sẵn; nếu dùng vị trí khác có thể đặt biến môi trường `MODSTUDIO_FROZEN_M03`.

### Bảo vệ dữ liệu

Chỉ gửi kết quả **đếm tổng hợp** từ Bước A/C lên ChatGPT hoặc GitHub. **Không đăng toàn bộ JSON kết quả**, các bản sao `AgentInput`, mã Unity B sinh ra, `ground_truth_PRIVATE.json`, seed hoặc ảnh có chuỗi test riêng tư. Bản ZIP và mã public này chỉ chứa code/test với chuỗi giả lập.

### Thước đo kế tiếp

- Khả năng hoàn thành: 3/3 `completed:true`, 0 lỗi JSON.
- Độ bao phủ (chưa chấm): `Selected` so với `Candidates`; đếm không phải recall thực tế.
- Bằng chứng: validator observed, không có nhận định bị từ chối (do canonical IDs).
- **Độ đúng 15 positive / 5 negative:** chỉ có sau đánh giá private **riêng, gắn nhãn v1.0**, không được tự gán ước lượng.
- Kiểm tra khả năng tổng quát hóa thực: **khóa mã trước**, sau đó tạo B2 seed mới kín trong project mới và chạy mà không dùng truth để sửa Agent.
