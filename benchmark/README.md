# Benchmark Day 07

Bộ cơ bản mới: 17 dev (15 có đáp án + 2 thiếu bằng chứng), 7 test (5 + 2). Không dùng lại 5 câu test đã xem ở Day 06 để chọn cấu hình.

Bộ bonus riêng cho Japan Foundation 2021: 18 dev (15 + 3), 30 test (24 + 6). Test có 6 bảng, 5 ảnh/bản đồ, 5 biểu đồ, 4 multi-hop, 4 text; mỗi câu chỉ một nhóm chính. Bản đồ chứa dữ liệu/legend dùng làm evidence, không phải hình trang trí.

Câu hỏi, đáp án, page/region/quote và lý do thiếu bằng chứng ở `private/basic.json`, `private/bonus.json`; giữ local vì chứa trích đoạn. Có thể tái tạo bằng `scripts/prepare_benchmarks.py` trên snapshot đúng, ở checkout sạch chưa có frozen file. Script từ chối ghi đè bộ đã khóa. Hash và thời điểm khóa trong `frozen.json`.

Gold chỉ được evaluation đọc. `src/agent.py`, `src/retrieval.py`, `src/bonus.py` và web không import benchmark/gold. Filter dựa trên số bảng/hình hoặc từ bản đồ trong query, không lấy trang chuẩn từ gold. Mọi query viết lại bởi model được ghi riêng trong tool trace.

Metric retrieval là hit theo trang anchor đã công bố, không khớp chuỗi đáp án. Với multi-hop, báo thêm Complete Evidence@3 và Context Evidence Rate yêu cầu tất cả trang. Có thể có evidence thay thế hợp lệ ở trang khác: phần review câu trả lời đối chiếu bản gốc và chấp nhận bằng chứng tương đương, không sửa ranking/điểm để khớp gold. Vì vậy metric anchor có thể thấp hơn mức đáp án được hỗ trợ thực tế.

Chấm câu trả lời bằng đối chiếu nguồn gốc, không suy ra từ `status=answered` hoặc citation ID hợp lệ. Nhãn AI ghi rõ người/loại chấm; học viên cần tự kiểm tra trước nộp, không giả nhận xét AI là ký xác nhận của con người. Test độc lập chỉ chạy sau khi chốt pipeline; nếu dùng kết quả test để chỉnh, phải có bộ test mới.

## Holdout bonus v2

V1 được giữ đủ 30 câu và mọi lỗi. Sau phân tích lỗi v1, tạo 30 câu v2 có đáp án/đích mới, vẫn đủ 6 bảng + 5 ảnh + 5 biểu đồ + 4 multi-hop + 4 text + 6 thiếu bằng chứng. Thời điểm/hash ở `frozen_v2.json`. V1 không còn là test độc lập của pipeline đã sửa; v2 mới dùng để báo kết quả cuối. Không loại câu mơ hồ/đơn vị sai khỏi mẫu số v1 để tăng điểm.
