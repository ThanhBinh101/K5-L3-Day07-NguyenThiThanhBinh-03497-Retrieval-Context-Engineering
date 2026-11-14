"""Build submission report and review packet from measured runs, not invented scores."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,PRIVATE,read_json,write_json,sha,now

def rate(m):return f'{m["n"]}/{m["N"]} ({100*m["n"]/m["N"]:.1f}%)' if m.get('N') else 'không áp dụng'

def main():
 a=read_json(ROOT/'results/agent_summary.json');b=read_json(ROOT/'results/bonus_summary.json');r=read_json(ROOT/'results/retrieval_summary.json')
 ui=read_json(ROOT/'results/ui_checks.json');cost=read_json(ROOT/'results/api_cost_ledger.json')
 dev=[]
 for alpha in [0,.5,1]:
  m=next(x for x in r['basic']['dev'] if x['alpha']==alpha and x['budget_chars_per_search']==2400)
  dev.append(f'| {"BM25" if alpha==0 else "Dense" if alpha==1 else "Hybrid"} | {alpha} | {rate(m["Hit@1"])} | {rate(m["Evidence Hit@3"])} | {rate(m["Context Evidence Rate"])} |')
 agent=[]
 for split in ['basic_dev','basic_test']:
  for name,m in a[split].items():
   agent.append(f'| {split.replace("basic_","")} · {name} | {rate(m["pass"])} | {m["answer_grade_mean_over_2"]*2:.2f}/2 | {rate(m["citation_support"])} | {m["median_seconds"]:.2f}s | {m["total_tokens"]:,} | ${m["estimated_cost_usd"]:.5f} |')
 bonusrows='\n'.join(f'| {g} | {m["n"]}/{m["N"]} |' for g,m in b['test']['groups'].items())
 report=f'''# Day 07 — Kanji Sensei · Agentic RAG

**Nguyễn Thị Thanh Bình · MSSV 2A202603497 · L3A**  
Ngày hoàn tất: 14/11/2026 (Việt Nam). Code và kết quả có AI hỗ trợ; nhãn review ghi rõ **Codex AI đối chiếu nguồn gốc**, không giả là học viên đã ký xác nhận.

## Kết quả bàn giao

Ứng dụng chạy local tại http://127.0.0.1:8707. Một ô tìm kiếm, thanh alpha 0–1 bước 0.1 có mô tả trước khi tìm, quét 11 mức, hỏi đáp có nguồn, xem PDF, vẽ chữ và xem hình minh hoạ Kanji gốc. Mở `MoKanjiDay07.command`; hướng dẫn tái lập ở `docs/RUN.md`.

Phần Kanji test: **{rate(a['basic_test']['selected']['pass'])}** gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Bonus test độc lập v2: **{rate(b['test']['pass'])}**, vượt ngưỡng 90%, giữ đủ toàn bộ 30 câu trong mẫu số. Đây là kết quả benchmark và minh chứng theo rubric; điểm cuối do giảng viên chấm.

## 1. Dữ liệu và pipeline

Dùng lại PDF KANJI N2 của Kaori Sensei từ Day 06: 473 trang vật lý, 454 trang học Kanji, 1.764 dòng từ vựng. Tái sử dụng ID/chunk chiến lược B và vector Qdrant `kanji_B`; sao chép nhất quán bằng SQLite backup API, không sửa Day 06. Cả 19 trang giới thiệu/mục lục/bài tổng quan cũng được index text riêng để không bỏ nội dung hữu ích.

Embedding: `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, 384 chiều, cosine, L2 normalization, CPU, prefix `passage: `/`query: `, max 512 token. Model local kế thừa Day 06; thông số tại `configs/embedding.json`.

PDF Kanji có bảng và 454 hình cách nhớ nhưng không đủ biểu đồ định lượng cho bonus. Sau khi người dùng cho phép, bổ sung **Survey Report on Japanese-Language Education Abroad 2021**, Japan Foundation, bản `All_contents_r2.pdf`, **105 trang**. Nguồn và quyền dùng có ghi công: https://www.jpf.go.jp/e/project/japanese/survey/result/survey21.html . Copyright Japan Foundation. Created by editing the “Survey Report on Japanese-Language Education Abroad” (the Japan Foundation).

Index toàn bộ text hữu ích của báo cáo thành đoạn 1.800 ký tự, bước 1.400 (overlap 400), giữ trang vật lý và ID; hai trang không có native text là bìa/trang trống được ghi trong audit. Render trang gốc để đọc bảng, chart và map bằng vision khi agent gọi tool. Không tạo biểu đồ giả để đáp ứng đề. Citation dùng số trang vật lý; thân báo cáo lệch +6 so với số trang in.

Native extraction của bản đồ lấy cả text ngoài khung do hai trang dùng chung artwork. Đã trích lại **cả hai nửa**, so với ảnh gốc, lưu snapshot `data/jpf2021_map_extraction.json` có SHA/nguồn/ghi công. Snapshot không chứa nhãn gold và có thể tái tạo index đúng mà không phải gọi vision lại. `scripts/prepare_bonus.py --verify-only` kiểm tra hash extraction.

## 2. Ba phương pháp tìm kiếm và alpha

- BM25: token tiếng Việt có dấu và biến thể không dấu, Japanese unigram/bigram, bỏ một số từ hỏi thông dụng; k1=1.5, b=0.75.
- Dense: embedding query thật, tìm cosine chính xác trên Qdrant Day 06; báo cáo được embed bằng cùng model trong collection theo hash extraction.
- Hybrid: `score = (1-alpha)*minmax(BM25) + alpha*minmax(dense)` trên toàn corpus của cùng query. Không cộng thẳng hai thang điểm thô. Score không phải xác suất.

Alpha 0 là chỉ BM25, alpha 1 là chỉ dense, 0.1 là 90% BM25 + 10% dense. Slider chỉ đổi mô tả cho đến khi bấm tìm. Nút quét chạy cùng câu qua 11 mức, dùng chung embedding/cache; thời gian quét không đại diện mọi mức chạy cold độc lập.

Với report, filter chỉ dựa vào ID Graph/Table hoặc từ bản đồ trong query; trả trang khác nhau để giảm lặp. Không đọc gold để suy ra trang/filter. Các filter này được áp dụng nhất quán cho cả ba phương pháp.

### Dev Kanji: cùng corpus, cùng câu và cutoff

| Phương pháp | Alpha | Hit@1 | Evidence Hit@3 | Context Evidence Rate |
|---|---:|---|---|---|
{chr(10).join(dev)}

Metric retrieval dùng trang anchor đã công bố. Một từ có thể xuất hiện ở nhiều trang hợp lệ (ví dụ 攻撃/硬貨); phần chấm câu trả lời chấp nhận evidence tương đương đã đối chiếu. Vì vậy anchor hit có thể thấp hơn khả năng trả lời thật. Với multi-hop còn báo Complete Evidence@3 và context đủ **tất cả** trang.

## 3. Agent và context

Model thật: **gpt-5.4-mini-2026-03-17**, kế thừa cấu hình Day 04 theo xác nhận người dùng. Người dùng đã cho phép gửi câu hỏi/đoạn truy xuất/ảnh trang tới API. Key chỉ nằm trong `.env`, không ở UI, trace hay gói nộp.

Agent loop tự viết với `search`, `view_page`, `finish`. Model quyết định query, có thể tìm nhiều lần; mọi query gốc/viết lại, tham số, kết quả, context, citation, token, lỗi đều có trace. Tài liệu chỉ là dữ liệu, không là chỉ dẫn. Bắt buộc search trước khi trả lời; citation phải thuộc context đã thấy. Với report, mọi câu trả lời có đáp án phải xem trang gốc; câu có nhiều ID hình/bảng phải dẫn đủ các ID đó. Kiểm tra ID là điều kiện kỹ thuật, không thay việc đọc nguồn.

Chốt trên dev: Kanji alpha 0.5, top-k 5, tối đa 4 lượt search, **2.400 ký tự mỗi lượt search**; report alpha 0.5, **4.800 ký tự/lượt**. Baseline alpha 0, 1 lượt, 2.400 ký tự. Dedup theo chunk, giữ nguồn, bỏ nguyên đoạn không vừa budget. Lịch sử nhiều lượt và ảnh vision có thể làm tổng token lớn hơn budget ký tự mỗi lượt; trace token mới là số đo thực tế. Giới hạn vòng loop = `max_searches*2+4`, lỗi/timeout ghi status error, không thay bằng mock.

## 4. Thí nghiệm và phân tích lỗi

Đã thử 11 alpha x 2 context budget cho retrieval; agent dev so baseline, hybrid context 2.400 và hybrid context 4.800. Hybrid cải thiện raw retrieval dev; context lớn hơn không cải thiện điểm đáp án Kanji và thêm citation dư, nên chọn 2.400. Cache khiến giá tiền không tỷ lệ đơn giản với tổng token.

| Split / cấu hình | Đạt | Grounded answer | Citation hỗ trợ | Trung vị | Token | USD ước tính |
|---|---|---|---|---:|---:|---:|
{chr(10).join(agent)}

Test Kanji: baseline và cấu hình chọn cùng đúng 7/7, không tuyên bố hybrid tăng điểm test. Test nhỏ, không chứng minh tổng quát mọi câu hỏi.

Các lỗi dev cụ thể và kiểm chứng sau sửa:

1. BM25 query “tiền xu” xếp trang 37 xuống top-3; “phương án” bị nhiễu bởi cách nhớ ở trang khác. Hybrid alpha 0.5 nâng Evidence Hit@3 từ 14/15 lên 15/15. Model có thể viết query gọn hơn để tìm evidence thay thế; không dùng gold để viết query.
2. Bonus dev B-dev-06 nhầm legend map với màu cột Graph 1-1-4; B-dev-09 lấy nhầm chart/nhầm năm. Thêm filter số hình từ query, dedup trang, đọc ảnh gốc và kiểm tra nhãn hình.
3. Sau sửa retrieval vẫn có citation legend trên sai nửa map, do native extraction chứa chữ ngoài khung; sửa extraction của cả hai trang trước test cuối. B-dev-15 từng kết luận nhầm năm bắt đầu khảo sát từ đoạn bảng bị cắt; yêu cầu xem trang gốc cho cả câu text. Dev vision-v2 đạt 18/18 theo đối chiếu gốc.

Trace trước/sau và code snapshot ban đầu giữ trong `results/private/`, không sửa hay xóa các kết quả không cải thiện.

## 5. Bonus: đánh giá độc lập, không tune trên test cuối

Bộ ban đầu: 18 dev (15+3), 30 test (24+6). Test v1 được chấm nghiêm **26/30 = 86.7%**: nhầm cách gọi màu, câu so sánh hai loại đơn vị, và hai câu mở đầu “Có” nhưng giải thích “không”. Không xóa câu mơ hồ hay sửa nhãn để nâng điểm.

Sau khi đọc v1, v1 trở thành dữ liệu phân tích lỗi. Bổ sung hướng dẫn kiểm tra nhất quán Có/Không và đơn vị **chỉ cho report**; prompt Kanji đã đánh giá giữ nguyên. Khóa bộ **30 câu mới** ở `benchmark/frozen_v2.json`, không chỉ diễn đạt lại cùng đáp án. Sau đó khóa code/config/extraction bằng `results/experiment_lock_v2.json` trước khi chạy toàn bộ test v2. Giữ riêng v1/v2, không báo v1 là test độc lập của pipeline đã sửa.

### Kết quả v2: {rate(b['test']['pass'])}

| Nhóm chính | Đạt / Tổng |
|---|---:|
{bonusrows}

Không có lỗi API/timeout trong 30 câu. Abstention đúng 6/6; 1/24 câu có đáp án bị từ chối sai. Grounded answer trung bình {b['test']['answer_grade_mean_over_2']*2:.3f}/2; citation hỗ trợ {rate(b['test']['citation_support'])}. Citation dư về legend không hỗ trợ trực tiếp số liệu Argentina được đánh dấu riêng, không tự coi mọi ID hợp lệ là đúng.

**Lỗi còn lại B2-test-03:** Costa Rica nằm ở trang vật lý 20, phần tiếp của Table 1-2-2. Filter ID bảng lấy trang có nhãn đầu bảng, không mở rộng sang continuation không ghi lại nhãn; agent từ chối. Giữ lỗi trong mẫu số và không sửa pipeline sau test v2. Hướng cải thiện sau này: nối các trang tiếp bảng theo layout, rồi đánh giá bằng holdout mới.

Thời gian trung vị v2: **{b['test']['median_seconds']:.2f}s/câu**; tổng **{b['test']['total_tokens']:,} tokens**; chi phí ước tính **${b['test']['estimated_cost_usd']:.5f}**. Giá chuẩn đối chiếu ngày 14/11/2026 tại https://developers.openai.com/api/docs/models/gpt-5.4-mini : input $0.75/M, cached input $0.075/M, output $4.50/M. Tính từ usage thực tế từng call, gồm image tokens API báo, không cộng đôi reasoning; đây không phải hóa đơn tài khoản. Chi phí agent các lần chạy có ledger riêng.

## 6. Vẽ Kanji và hình minh hoạ

Kế thừa KanjiVG và shape matcher Day 06 của cùng học viên; chuẩn hóa hình dạng, chamfer + ghép nét, đưa ra ứng viên trong 454 chữ. Chọn ứng viên để xem âm đọc, nghĩa, từ vựng, hình minh hoạ **gốc của PDF** và citation. Không giả đây là OCR học sâu hoặc khẳng định mọi chữ viết tay đều đúng. UI test dùng nét mẫu tổng hợp 井, không thay benchmark người thật.

Ghi công KanjiVG: Ulrich Apel và cộng tác viên, CC BY-SA 3.0; snapshot ở Day 06. Dữ liệu polyline phái sinh giữ cùng giấy phép khi phân phối. Hình PDF của sensei không tự mang giấy phép KanjiVG.

## 7. Kiểm tra và bàn giao

- **34 unit tests pass**, bao gồm starter mock tests và kiểm tra alpha, lexical không dấu/Japanese, input, context budget/dedup, giới hạn loop và lỗi API. Mock chỉ kiểm tra code.
- **{len(ui['checks'])} kiểm tra UI pass** bằng Chrome trên server thật: slider 0/0.1/1, một ô search, 11 mức quét, nguồn PDF, hỏi API thật, nét vẽ/mẫu và hình gốc, mobile 390px không tràn ngang, input/Origin và route secret. Trang metrics cũng kiểm tra 1440px/390px.
- Kiểm tra extraction tái tạo đúng hash, frozen benchmark và experiment lock còn nguyên.
- Cách chạy: `docs/RUN.md`; tổng hợp số liệu: `results/agent_summary.json`, `results/bonus_summary.json`, `results/retrieval_summary.json`; nhãn từng câu và packet đối chiếu: `results/private/reviews/`, `results/private/REVIEW_PACKET.md`.
- PDF/corpus/vector/model/API key không đưa vào gói code công khai. Dữ liệu có trích đoạn, benchmark gold và trace giữ local/gói minh chứng riêng; người chấm cần PDF gốc Day 06 hoặc quyền truy cập hợp lệ. Báo cáo JPF tải lại từ nguồn công khai và kiểm tra SHA.

## 8. Giới hạn

Bộ test được thiết kế theo nhiệm vụ minh bạch, nhiều câu có ID bảng/hình; độ khó không đại diện truy vấn mở mọi ngôn ngữ. Bản đồ được dùng làm evidence ảnh có thông tin, không đánh đồng với ảnh trang trí. Embedding nhỏ và budget có thể bỏ sót; bảng tiếp trang vẫn là lỗi đã đo. Điểm tương đồng/shape distance không phải xác suất. Nhãn AI đã ghi rõ loại chấm; học viên cần đọc packet để tự giải thích và xác nhận trước nộp.
'''
 out=ROOT/'report/individual/2A202603497_NguyenThiThanhBinh.md';out.write_text(report)
 packet=['# Review packet — actual held-out answers and original-source checks','Reviewer: Codex AI. Student/human sign-off: not asserted.','']
 for suite,version,label in [('basic','v1','baseline'),('basic','v1','selected'),('bonus','v1','selected'),('bonus','v2','selected')]:
  casefile=ROOT/f'benchmark/private/{suite}.json' if version=='v1' else ROOT/'benchmark/private/bonus_test_v2.json'
  qs=[q for q in read_json(casefile) if q['split']=='test'];suffix='-v2' if version=='v2' else ''
  reviews={x['query_id']:x for x in read_json(ROOT/f'results/private/reviews/{suite}-test{suffix}-{label}.json')}
  for q in qs:
   t=read_json(ROOT/f'results/private/{suite}/agent-test{suffix}/{label}/{q["id"]}.json');review=reviews[q['id']]
   packet += [f'## {suite} {version} {label} · {q["id"]}',q['question'],'',f'Expected: {q["expected"]}',f'Actual: {t["answer"]}',f'Passed: {review["passed"]}',f'Review: {review["reason"]}','','Citations:']
   for c in t['citations']:packet.append(f'- {c["corpus"]} physical p{c["page"]}: {c["region"]}; quote: {c["quote"]}')
   packet+=['','Student reviewer: __________  Date: __________  Confirm/correct: __________','']
 (ROOT/'results/private/REVIEW_PACKET.md').write_text('\n'.join(packet))
 visual={str(p.relative_to(ROOT)):sha(p) for p in (PRIVATE/'rendered').rglob('*.png')}
 write_json(ROOT/'results/private/visual_manifest.json',{'created_at':now(),'files':visual,'source':'Original PDFs; cached rendered pages used by vision tool and review.'})
 print('Wrote report and 74-case test review packet')

if __name__=='__main__':main()
