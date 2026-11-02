# Dữ liệu Milestone 03

- `AgentInput/rea_evidence.jsonl`: chứng cứ phương thức từ bản build (REA only), SHA-256 assembly kèm mỗi hàng. Không có đáp án text trong prefab hoặc JSON.
- `Outputs/baseline_static.json`: quan sát do luật tĩnh tạo, `validation_status` thuộc `observed`, `hypothesis`, `rejected`.
- `Outputs/qwen_agent.json`: trace các yêu cầu tool của model local; `completed` chỉ true nếu model gửi action `finish`.
- `Outputs/build_assets.json`: thí nghiệm parse chỉ đọc Unity build assets; source_ref là **file đã build và path_id**, KHÔNG phải đường dẫn asset tác giả.
- `PrivateEvaluation/ground_truth_v01.csv`: dùng riêng sau khi sinh observations, tuyệt đối không có trong prompt hoặc công cụ tra cứu của Agent.
- `Outputs/evaluation_private.json`: đối chiếu text+nguồn; tiêu chí exact/template. Các nguồn chỉ mới biết đường đọc mà chưa biết text không được tính đã chứng minh.

Giới hạn: mô hình không quan sát runtime, không xác minh UI khi chơi, không tạo hook. Khi có thay đổi build, evidence token và MVID có thể đổi; cần tạo lại REA input và đánh giá độc lập.
