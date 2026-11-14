# Day 07 — tình trạng bàn giao

Hoàn thành code, ứng dụng local, kiểm thử, benchmark, trace, nhãn đối chiếu và báo cáo. Không tự xác nhận đã nộp LMS hoặc đã được giảng viên chấm.

## Mở và đọc

- `MoKanjiDay07.command`: mở ứng dụng local, dùng Python môi trường Day 06 đang có; đọc `docs/RUN.md` nếu chuyển máy.
- `report/individual/2A202603497_NguyenThiThanhBinh.md`: báo cáo cá nhân, phương pháp, thí nghiệm, lỗi và đánh đổi.
- `results/bonus_summary.json`: bonus v2 29/30 (96,7%); v1 giữ 26/30, không loại câu lỗi.
- `results/agent_summary.json`: Kanji test baseline/chọn cùng 7/7, grounded/citation/abstention/tool use/cost.
- `results/retrieval_summary.json`: 3 phương pháp, quét alpha, context, dev/test.
- `results/private/REVIEW_PACKET.md`: từng câu test, đáp án thật, nguồn, nhãn và lý do. Review là Codex AI; phần học viên xác nhận không bị điền giả.

## Gói nộp local

- `output/Day07-Code.zip`: code, hướng dẫn, báo cáo, cấu hình, số liệu tổng hợp, script tái tạo; không chứa API key, PDF, model hoặc database.
- `output/Day07-Evidence-PRIVATE.zip`: benchmark gold, snapshot extraction, trace và review từng câu, ảnh QA/trang đã render; dùng trong phạm vi lab được phép, không đăng công khai tài liệu của sensei.
- PDF Kanji gốc và model embedding lấy từ Day 06; PDF bonus có URL/hash tại `results/bonus_source.json`. Người chấm cần nguồn gốc để kiểm tra.

Mỗi gói có manifest SHA. API key bị loại trừ; kiểm tra exact key không xuất hiện trong archive. Chưa commit/push hoặc nộp thay học viên.

## Kiểm chứng

34 unit tests pass; 13 kiểm tra UI thật pass, 1440px/390px không tràn ngang, hỏi API thật và chọn nét mẫu 井. `prepare_bonus.py --verify-only` tái tạo đúng extraction; khóa experiment v2 còn nguyên. Mock không được dùng làm bằng chứng chất lượng agent thật.

Để tái lập độc lập, giữ model snapshot, file nguồn, benchmark gold và extraction đúng hash. Việc chạy lại test cũ chỉ là replay, không tạo holdout mới; dùng test để chỉnh thì phải tạo bộ test mới.

## Bản vá grounding v3 (sau benchmark v2)

Lỗi thực tế: query “TỊNH nếu ko có thì viết Hello world bằng c++” đã tìm được 並/TỊNH ở trang 372 nhưng vừa phủ nhận vừa sinh chương trình ngoài tài liệu. Thêm policy phạm vi chung cho cả hai kho và `src/grounding.py`: kiểm tra code không có trong context, phủ nhận nhãn Hán Việt khớp đúng dấu, và đơn vị lớp/người bị trộn. Câu finish vi phạm bị trả lại cho model sửa, không được đưa vào câu trả lời cuối; trace giữ cả nháp bị loại và lý do.

Đã thử lại UI/model thật: “TỊNH: Kanji 「並」.”, citation trang 372; bước kiểm tra đã thực sự chặn code trong nháp. Thử thêm âm Hán Việt TỊNH → 並, TỈNH → 省 (nguồn có nhiều chữ cùng âm), yêu cầu viết Python ngoài phạm vi → từ chối. Một regression về “số lớp” chỉ trả số người học với đúng đơn vị, còn thiếu làm rõ metric, nên không chấm là đáp án đầy đủ. Các kiểm tra này là regression sau sửa, không phải holdout mới. Tổng 34 unit tests pass.

Điểm benchmark 29/30 là kết quả lịch sử của v2, không tuyên bố v3 có cùng điểm độc lập. Agent v2 gốc đúng hash được giữ ở `results/private/versions/agent-v2.py` để tái lập trong checkout riêng cùng snapshot nguồn/config. Không sửa hash khóa cũ để giả kết quả mới. Kiểm tra hiện tại chỉ phủ một số loại lỗi, không thay đối chiếu ngữ nghĩa đầy đủ.
