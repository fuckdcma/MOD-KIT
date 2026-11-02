# Sync policy, caveats and long-term continuity

## Public repository

Repository `fuckdcma/MOD-KIT` là PUBLIC. Mọi nội dung commit đều có thể được đọc và fork. **`reference_DO_NOT_FEED_MODEL` không phải là thư mục private.** Nếu muốn giữ benchmark thực sự kín, di chuyển reference sang kho riêng có kiểm soát quyền, và chỉ công bố hashes/IDs.

Không commit credentials, private URLs, file thương mại không có quyền phân phối, tài khoản, thông tin nhạy cảm, .env hoặc tokens. Trước khi đẩy source local, kiểm tra `git diff --cached`.

## Không đồng nhất GitHub với transcript của ChatGPT

Kết nối GitHub có thể ghi **file được truy xuất/cung cấp và tài liệu tổng hợp**, không tự trích toàn bộ tin nhắn lịch sử ChatGPT dưới dạng nguyên văn. `docs/CHAT_HANDOFF.md` là snapshot để tiếp tục dự án, không phải export chat. Nếu cần toàn bộ nguyên văn chat, tải bản export qua ChatGPT và tự rà soát thông tin cá nhân trước khi lưu.

## Đồng bộ source và ZIP còn thiếu

Trên PC Windows có git đã xác thực, clone repo và chạy `tools/Sync_Local_Artifacts.ps1` trong repo. Nó có chế độ xem trước; cần `-Push` và xác nhận chủ động mới commit/push. Đọc script trước khi chạy.

Mỗi lần hoàn tất milestone: cập nhật `docs/PROGRESS.md`, `docs/M03_LATEST_FINDINGS.md` hoặc tài liệu milestone mới, upload logs/json/code kèm SHA, và giữ data reference tách khỏi agent inputs.
