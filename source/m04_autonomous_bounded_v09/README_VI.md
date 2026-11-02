# MOD Studio AI — M04 Autonomous Bounded Context v0.9 (experimental)

**Mục đích:** kiểm tra lỗi `invalid_json` + `finish=length` ở lượt Autonomous của UnityTextLab-B mà **không sửa M03 v0.8 đã đóng băng** và không ghi đè kết quả M04 cũ.

## Bằng chứng đã có (được người dùng cung cấp)

- Ollama `qwen3.5:4b` probe thành công; Guided gốc **3/3 `completed:true`**, mỗi lượt 11 nhận định *chưa chấm điểm*.
- Autonomous 1280 token: 7 hành động tool thành công, 3 lỗi JSON ở bước 8; các phản hồi kết thúc bằng `finish=length`.
- Autonomous retry 2560 token, 900 giây, **trong thư mục riêng**: vẫn `completed:false`, cùng ba lỗi bước 8 với các chi tiết **giống hệt**. Hai file REA/UnityPy đầu vào đã được kiểm tra SHA-256 khớp.
- Việc tăng `num_predict` chưa giải quyết được lỗi; **không chứng minh** Ollama bỏ qua tham số hay context là nguyên nhân duy nhất. Code cũ đặt Ollama `num_ctx=4096`, và lịch sử các lần gọi tool tích lũy theo thời gian — đó là một rủi ro thực tế có thể thử nghiệm.

## Những thay đổi trong v0.9, so với v0.8

1. **Giữ nguyên REA/asset scanner, bộ lọc và validator bằng chứng**; sử dụng nguyên tắc xác thực cũ (có kiểm tra fingerprint các đoạn mã).
2. **Thay cách chạy Autonomous**: mỗi lượt chỉ gửi system prompt + một yêu cầu ngắn chứa một `evidence_ledger` được tính lại từ các kết quả tool thực. Không nối toàn bộ lịch sử chat.
3. Giới hạn ledger ~5.400 ký tự; các bản ghi vẫn giữ loại bằng chứng gốc và phương thức / PathID. Các nhãn `unknown` không được tự nâng cấp thành `observed`.
4. Đổi Ollama native `num_ctx` từ **4096 sang 8192**. Đặt `num_predict=2560` và timeout 900 giây trong thí nghiệm mặc định. Đây là **hai thay đổi có chủ đích trong một thí nghiệm**, do đó không thể tách ảnh hưởng của từng thay đổi từ kết quả đầu tiên.
5. Tăng `max_steps` lên **16**. Nếu vẫn không ra `finish` hợp lệ, báo `completed:false`, không suy diễn đáp án và không chấm điểm.
6. Một script PowerShell duy nhất kiểm tra fingerprint đầu vào, sao chép đúng hai file build-only, xác minh SHA-256, và chạy dưới thư mục **hoàn toàn mới**; không cần tải lại assets/REA, không cần sửa Unity hay `.venv`.

**Trạng thái:** 7/7 kiểm thử Python được chạy thành công trong môi trường xây gói. **Chưa được kiểm tra với Ollama/Qwen hoặc PowerShell thực trên máy Windows của người dùng**. Đây là công cụ nghiên cứu, không phải kết quả benchmark.

## Cách chạy trên Windows 11

1. Giữ nguyên các thư mục và file đã có:

   - `D:\ModStudioAI\Milestone03\src\modstudio_m03.py` (M03 v0.8)
   - `D:\ModStudioAI\Milestone04\Runs_LOCAL` (bản gốc với Guided 3/3)
   - `D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_2560_LOCAL` (thử nghiệm thất bại lần 2)

2. Giải nén ZIP v0.9 vào một thư mục mới, mở PowerShell ngay **thư mục có `Scripts`, `src`, `tests`**, chạy:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\Run_M04_Autonomous_v09.ps1
   ```

   Script sẽ tạo thư mục *mới*:
   `D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_BOUNDED_V09_LOCAL`

   Nếu thư mục này tồn tại, script **từ chối chạy và không ghi đè**. Không xóa kết quả cũ để chạy lại. Thay vào đó tạo tên khác bằng `-NewRunsDir` và ghi rõ mã phiên bản.

3. Kiểm tra kết quả (chỉ số an toàn, không lộ chuỗi):

   ```powershell
   $out = 'D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_BOUNDED_V09_LOCAL\Outputs'
   Get-ChildItem $out -Filter 'autonomous_r??.json' | Sort-Object Name | ForEach-Object {
       $r = Get-Content $_.FullName -Raw | ConvertFrom-Json
       [pscustomobject]@{
           Run = $_.BaseName
           Completed = $r.completed
           Observations = @($r.observations).Count
           InvalidJSON = @($r.trace | Where-Object { $_.code -eq 'invalid_json' }).Count
           FinishLength = @($r.trace | Where-Object { $_.detail -match 'finish=length' }).Count
           LastAction = @($r.trace)[-1].action
       }
   } | Format-Table -AutoSize
   ```

4. Có thể xác minh 7 kiểm thử Python bằng môi trường M03 v0.8 hiện có:

   ```powershell
   & 'D:\ModStudioAI\Milestone03\.venv\Scripts\python.exe' -m unittest discover -s .\tests -v
   ```

## Cần phân biệt các phép đo

- `autonomous_r01` **gốc** 1280: `completed:false` — **vẫn tính thất bại vận hành lần đầu**.
- `autonomous_r01` **retry** 2560 / context4096: `completed:false` — **vẫn tính thất bại lần 2**.
- `autonomous_r01..r03` v0.9 / context8192 / bounded history: một nghiên cứu mới, **không thay thế** r01/r02/r03 gốc.
- Guided v0.8: 3/3 hoàn tất, **11 nhận định mỗi lần không đồng nghĩa với 11 câu đúng**.
- Không chạy `Evaluate_M04_Private.ps1` trên một tập hợp lẫn lộn thiếu lượt, hoặc có `completed:false`. Nếu cần chấm riêng v0.9 sau này phải làm **scoring protocol versioned** với báo cáo rõ lượt lỗi và lượt thành công.

## Bảo vệ dữ liệu riêng tư

ZIP chỉ có mã nguồn public. Không chứa seed, chuỗi UnityTextLab-B, `ground_truth_PRIVATE.json`, dữ liệu game build, AgentInput hoặc raw output. Script v0.9 **chỉ đọc** REA/UnityPy từ `Runs_LOCAL/AgentInput` và sao chép tới thư mục local mới; không bao giờ đọc bộ đáp án ở `PRIVATE_DO_NOT_UPLOAD`. Các file `Outputs/autonomous_*.json` **có thể chứa các chuỗi trong game**; chỉ gửi bảng đếm ở trên, không đưa toàn bộ trace lên GitHub public.

### Đặc biệt

- Tool ledgers có thể bỏ qua một số bằng chứng do giới hạn kích thước; khi đó khả năng tìm đủ nguồn text **có thể giảm**, dù tỷ lệ JSON hợp lệ tăng. Hai chỉ số đó phải được đánh giá riêng.
- `num_ctx=8192` có thể làm tăng VRAM/RAM hoặc thời gian chạy tùy phần cứng Ollama. Nếu xảy ra OOM/timeout, giữ báo cáo và kiểm tra `ollama ps`; không xóa/ghi đè.
- Nâng ngữ cảnh và thu gọn lịch sử **không bảo đảm** Qwen hoàn thành. Không tính 0 observations ở lượt incomplete là 0/20 đúng.
