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

23 unit tests pass; 13 kiểm tra UI thật pass, 1440px/390px không tràn ngang, hỏi API thật và chọn nét mẫu 井. `prepare_bonus.py --verify-only` tái tạo đúng extraction; khóa experiment v2 còn nguyên. Mock không được dùng làm bằng chứng chất lượng agent thật.

Để tái lập độc lập, giữ model snapshot, file nguồn, benchmark gold và extraction đúng hash. Việc chạy lại test cũ chỉ là replay, không tạo holdout mới; dùng test để chỉnh thì phải tạo bộ test mới.
