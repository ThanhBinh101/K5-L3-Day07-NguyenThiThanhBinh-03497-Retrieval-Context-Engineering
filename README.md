# Kanji Sensei — Day 07 đã triển khai

**Nguyễn Thị Thanh Bình · 2A202603497 · L3A**

Ứng dụng local: **http://127.0.0.1:8707**. Mở `MoKanjiDay07.command` hoặc xem [hướng dẫn chạy](docs/RUN.md).

- Một ô tìm kiếm, alpha 0–1 bước 0.1: 0 = BM25, 1 = dense, ở giữa = hybrid. Có mô tả trước khi tìm và quét 11 mức.
- Model thật điều phối retrieval, trả lời có citation, xem ảnh trang gốc và từ chối khi thiếu bằng chứng.
- Vẽ Kanji → chọn ứng viên → âm đọc, từ vựng, hình minh hoạ gốc và trang PDF.
- Dùng lại 454 Kanji/1.764 từ vựng của Day 06; bổ sung báo cáo Japan Foundation 105 trang cho bonus.

| Kiểm chứng | Kết quả |
|---|---|
| Kanji test, cấu hình chọn | 7/7 (5 có đáp án + 2 thiếu bằng chứng) |
| Bonus test v1, giữ nguyên trước sửa | 26/30 (86,7%) |
| Bonus test độc lập v2 sau khi khóa lại | **29/30 (96,7%)**, đạt ngưỡng ≥90% |
| Unit tests | 34 pass |
| UI Chrome | 13 kiểm tra pass; desktop/mobile |

[Báo cáo đầy đủ](report/individual/2A202603497_NguyenThiThanhBinh.md) · [Số liệu bonus](results/bonus_summary.json) · [So sánh retrieval](results/retrieval_summary.json) · [Quy trình benchmark](benchmark/README.md)

Nhãn chất lượng do Codex AI đối chiếu nguồn gốc, không giả là học viên đã ký xác nhận. V1 được giữ đủ kết quả và lỗi; v2 dùng câu hỏi mới, khóa trước thực thi. Điểm cuối do giảng viên chấm. Dữ liệu có trích đoạn, gold, trace, PDF và key giữ local; gói code và minh chứng riêng được mô tả ở `SUBMISSION_STATUS.md`.

## Bản vá grounding v3

Đã sửa lỗi câu “TỊNH nếu ko có thì viết Hello world bằng c++”: trả 並 — TỊNH, trang 372; chặn code ngoài evidence và phủ nhận nhãn Hán Việt đã tìm thấy. 34 unit tests pass, kiểm tra live trên câu đã báo lỗi, phân biệt dấu và yêu cầu lập trình ngoài phạm vi. Các kết quả 7/7, 29/30 ở trên thuộc pipeline v2 đã khóa; không đổi tên thành điểm của v3. Xem `results/grounding_patch.json`. Câu hỏi mơ hồ về đơn vị vẫn cần cải thiện; đây chưa phải bộ kiểm chứng ngữ nghĩa đầy đủ.

## Đề bài gốc

# Day 7 — Agentic RAG

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
