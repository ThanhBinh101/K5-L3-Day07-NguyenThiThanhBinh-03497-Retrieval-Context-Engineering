# Chạy Kanji Sensei Day 07

Ứng dụng chạy tại http://127.0.0.1:8707. Trên máy hiện tại, nhấp đúp `MoKanjiDay07.command`, hoặc chạy từ thư mục Day 07:

```sh
../K5-L3-Day06-NguyenThiThanhBinh-MSSV-DataIngestionEngineering/.venv/bin/python -m src.web --port 8707
```

Máy mới: Python 3.11+, Poppler (`pdftoppm` trong PATH), tạo `.venv`, cài `requirements.txt`. Giữ Day 06 cạnh Day 07 hoặc đặt `DAY6_ROOT`. Chuẩn bị PDF và model embedding theo README Day 06. Copy `.env.example` thành `.env`, điền key/model có vision và function calling. Không commit `.env`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/prepare.py
curl --fail --location https://www.jpf.go.jp/e/project/japanese/survey/result/dl/survey2021/All_contents_r2.pdf --output data/private/bonus.pdf
.venv/bin/python scripts/prepare_bonus.py
.venv/bin/python -m src.web
```

`prepare.py` đọc Day 06 và tạo bản sao SQLite nhất quán bằng SQLite backup API; không sửa Day 06. Qdrant cần một tiến trình sở hữu mỗi index: dừng web trước khi chạy benchmark CLI. Embedding vẫn dùng model Day 06, prefix query/passage, 384 chiều, cosine, L2 normalization, 512 token. Các trang giới thiệu Day 06 và toàn bộ báo cáo bổ sung được index riêng bằng cùng model. Model embedding ở `DAY6_ROOT/.local/model`.

## Sử dụng

- Một ô tìm kiếm: nhập chữ, nghĩa hoặc câu hỏi.
- Kéo alpha, đọc mô tả trước khi tìm. Alpha 0 là BM25, 1 là dense; các mức giữa là hybrid. UI không tự chạy lại khi kéo.
- Tìm kiếm: xem kết quả, hình minh hoạ, bảng từ vựng và trang nguồn.
- Quét alpha: chạy cùng câu qua 11 mức, xem top-3 và thời gian. Chọn một dòng để đặt alpha, bấm Tìm kiếm để áp dụng. Không dùng chức năng này để tune trên benchmark test.
- Hỏi Sensei: model gọi search và có thể đọc ảnh trang gốc; từ chối nếu thiếu bằng chứng. Câu hỏi và đoạn trích/ảnh trang được gửi tới API đã được người dùng cho phép.
- Vẽ tìm Kanji: viết một chữ, tìm, chọn ứng viên. Đây là so khớp hình học KanjiVG, không phải OCR học sâu. Hình minh hoạ lấy nguyên gốc từ PDF Kaori, không phải ảnh mới được tạo.
- Kho báo cáo: dùng cho câu hỏi số liệu/biểu đồ/bản đồ Japan Foundation năm 2021. Citation dùng số trang vật lý PDF, khác số trang in (+6 với thân báo cáo).

## Benchmark và tái lập

Gold nằm trong `benchmark/private/`, không được code ứng dụng import. Bộ câu hỏi có hash tại `benchmark/frozen.json`. Không ghi đè benchmark đã chốt.

```sh
python scripts/benchmark.py retrieval-dev --suite basic
python scripts/benchmark.py freeze --suite basic
python scripts/benchmark.py agent-dev --suite basic --config baseline
python scripts/benchmark.py agent-dev --suite basic --config small
python scripts/benchmark.py agent-dev --suite basic --config selected
# Tương tự --suite bonus; đọc và chấm dev trước khi chốt.
python scripts/benchmark.py retrieval-test --suite basic
python scripts/benchmark.py agent-test --suite basic --config baseline
python scripts/benchmark.py agent-test --suite basic --config selected
python scripts/benchmark.py agent-test --suite bonus --config selected
```

Các lệnh freeze/test từ chối ghi đè kết quả đã hoàn tất. Chạy lại test chỉ kiểm tra tái lập, không tạo holdout mới; nếu dùng test để sửa cấu hình thì cần bộ test mới được chốt trước lần đánh giá độc lập kế tiếp. Lỗi API phải được giữ trong mẫu số bonus, không thay bằng mock. Các lệnh API có thể tốn phí; token và chi phí ước tính được ghi theo trace.

## Nguồn và quyền

- Kaori Sensei, KANJI N2, PDF 473 trang: quyền dùng lab theo xác nhận học viên tại Day 06. PDF, hình, corpus, gold có trích đoạn và trace giữ local, không đăng công khai.
- Copyright Japan Foundation. Created by editing the “Survey Report on Japanese-Language Education Abroad” (the Japan Foundation). Nguồn: https://www.jpf.go.jp/e/project/japanese/survey/result/survey21.html ; publisher cho phép sử dụng dữ liệu khảo sát khi ghi nguồn. Tải đúng bản `All_contents_r2.pdf`, SHA trong `results/bonus_source.json`.
- KanjiVG, Ulrich Apel và cộng tác viên; CC BY-SA 3.0. Mẫu polyline và thuật toán handwriting kế thừa Day 06 của cùng học viên. Snapshot giữ ở Day 06 `artifacts/kanjivg_snapshot.json`; dữ liệu phái sinh giữ cùng giấy phép khi phân phối.
- API function calling: https://developers.openai.com/api/docs/guides/function-calling . Giá model được đối chiếu https://developers.openai.com/api/docs/models/gpt-5.4-mini ngày 14/11/2026.

## Đánh giá độc lập lần 2 cho bonus

Test bonus v1 được giữ nguyên, chấm nghiêm 26/30. Sau khi đọc lỗi màu sắc, mở đầu Có/Không mâu thuẫn và phép trừ không cùng đơn vị, v1 chỉ còn là dữ liệu phân tích lỗi. Bộ 30 câu mới (không chỉ diễn đạt lại đáp án cũ) ở `benchmark/private/bonus_test_v2.json`, khóa bằng `benchmark/frozen_v2.json` trước khi chạy. Kết quả v2 ở thư mục `agent-test-v2`, không ghi đè v1. Prompt Kanji v1 được giữ nguyên ở `configs/kanji_system_v1.txt`; sửa hướng dẫn kiểm tra phủ định/đơn vị chỉ áp dụng kho report.

```sh
python scripts/benchmark.py retrieval-test --suite bonus --test-version v2 --lock results/experiment_lock_v2.json
python scripts/benchmark.py agent-test --suite bonus --test-version v2 --lock results/experiment_lock_v2.json --config selected
```

Khóa v2 kiểm tra code/config/extraction và bộ test v2. Không sửa code ngữ nghĩa để chạy lại v1 dưới tên đánh giá độc lập. Nhãn review, lý do và hash trace gốc được giữ riêng; không sửa câu trả lời hay loại lỗi khỏi mẫu số.

Hai nửa bản đồ đã có snapshot trích xuất được đối chiếu ở `data/jpf2021_map_extraction.json` (dữ liệu Japan Foundation có ghi công). `prepare_bonus.py` kiểm tra SHA PDF rồi dùng snapshot này để tái tạo đúng index đã đánh giá, không cần gọi lại vision API. `transcribe_maps.py` chỉ dành cho thí nghiệm extraction mới; không chạy để thay snapshot của lần đánh giá đã khóa.
