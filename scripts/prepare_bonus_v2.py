"""Fresh holdout after v1 was inspected and became error-analysis data. Never overwrite v1."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,write_json,sha,now
path=ROOT/'benchmark/private/bonus_test_v2.json'
if path.exists():raise SystemExit('Already frozen; refuse overwrite.')
rows=[]
def add(group,q,answer,pages,region):
 rows.append({'id':f'B2-test-{len(rows)+1:02}','split':'test','corpus':'report','group':group,'question':q,
  'answerable':group!='unanswerable','expected':answer,'gold_pages':pages,
  'evidence':[{'page':p,'region':region,'quote':answer} for p in pages],
  'verification':'Compare original rendered pages; new answers/targets, not paraphrases of v1 cases.'})
for x in [
 ('table','Theo Table 1-2-2 năm 2021, Mexico có bao nhiêu cơ sở và giáo viên tiếng Nhật?','139 cơ sở; 612 giáo viên',[19],'Table 1-2-2; Mexico; Institutions and Teachers 2021'),
 ('table','Đọc Table 1-2-2: Finland có bao nhiêu người học năm 2021 và mức tăng so với 2018 bao nhiêu phần trăm?','1,584 người; tăng 457.7%',[19],'Table 1-2-2; Finland; Learners 2021 and increase/decrease'),
 ('table','Theo Table 1-2-2, Costa Rica có bao nhiêu người học năm 2021 và hạng bao nhiêu?','829 người; hạng 60',[20],'Table 1-2-2 continuation; Costa Rica; rank and learners 2021'),
 ('table','Trong Table 1-4-2, năm 2021 có bao nhiêu giáo viên full-time và bao nhiêu part-time (đơn vị người)?','55,207 full-time; 19,385 part-time',[26],'Table 1-4-2; 2021; People columns'),
 ('table','Table 1-4-3: higher education có bao nhiêu giáo viên bản ngữ và tỷ lệ bản ngữ bao nhiêu?','4,593 người; 21.5%',[26],'Table 1-4-3; Higher education; native speakers and percent'),
 ('table','Theo Table 2-2-2, Indonesia có bao nhiêu cơ sở triển khai online và tỷ lệ bao nhiêu?','2,405 cơ sở; 81.3%',[38],'Table 2-2-2; Indonesia; online institutions and percent'),
 ('image','Đọc nhãn Italy trên bản đồ đầu báo cáo: số người học tiếng Nhật là bao nhiêu?','8,387 người',[2],'map Italy label'),
 ('image','Bản đồ Number of Japanese-Language Learners by Country/Region ghi Russia có bao nhiêu người học?','12,426 người',[2],'map Russia label'),
 ('image','Trong bản đồ đầu báo cáo, Sri Lanka có bao nhiêu người học tiếng Nhật?','9,746 người',[2],'map Sri Lanka label'),
 ('image','Trên bản đồ đầu báo cáo, nhãn Argentina ghi số người học là bao nhiêu?','4,486 người',[3],'map Argentina label'),
 ('image','Đọc hình bản đồ ở đầu báo cáo: New Caledonia có bao nhiêu người học tiếng Nhật?','3,426 người',[3],'map New Caledonia label'),
 ('chart','Đọc Graph 1-1-3: năm 1993 có bao nhiêu giáo viên, và đơn vị của trục đứng là gì?','21,034; trục đứng People (người)',[15],'Graph 1-1-3; bar 1993 and y-axis'),
 ('chart','Graph 1-1-2: số cơ sở năm 2012 là bao nhiêu?','16,046 cơ sở',[15],'Graph 1-1-2; bar 2012'),
 ('chart','Trong Graph 1-3-1, primary education chiếm bao nhiêu phần trăm số người học và tương ứng bao nhiêu người?','8.7%; 331,534 người',[24],'Graph 1-3-1; Number of learners; primary education blue'),
 ('chart','Theo Graph 1-5-1 năm 2021, Interest in the Japanese language cao hơn Interest in anime/manga/J-POP/fashion bao nhiêu điểm phần trăm?','60.1 - 59.9 = 0.2 điểm phần trăm',[28],'Graph 1-5-1; 2021; top two rows'),
 ('chart','Graph 1-3-1: secondary education chiếm bao nhiêu phần trăm số cơ sở, tương ứng bao nhiêu cơ sở?','50.3%; 9,192 cơ sở',[24],'Graph 1-3-1; Number of institutions; secondary education green'),
 ('multihop','Dùng Table 1-4-2 và Table 1-2-2: số giáo viên full-time toàn cầu năm 2021 nhiều hơn tổng số giáo viên tại Australia năm 2021 bao nhiêu người?','55,207 - 3,052 = 52,155 người',[26,19],'Table 1-4-2 full-time People; Table 1-2-2 Australia Teachers 2021'),
 ('multihop','Dùng hai nửa bản đồ đầu báo cáo: Thailand nhiều hơn Canada bao nhiêu người học?','183,957 - 18,293 = 165,664 người',[2,3],'map Thailand and map Canada labels'),
 ('multihop','Dùng Graph 1-1-3 và Table 1-2-2: số giáo viên toàn cầu năm 1979 nhiều hơn số giáo viên India năm 2021 bao nhiêu người?','4,097 - 1,132 = 2,965 người',[15,19],'Graph 1-1-3 1979; Table 1-2-2 India Teachers 2021'),
 ('multihop','So sánh Graph 1-5-1 và Graph 2-2-5: tỷ lệ Study in Japan năm 2021 ở Đông Nam Á cao hơn toàn cầu bao nhiêu điểm phần trăm?','37.8 - 29.3 = 8.5 điểm phần trăm',[28,38],'Graph 1-5-1 and Graph 2-2-5; Study in Japan 2021'),
 ('text','Phần Survey content cho biết có bao nhiêu phiên bản biểu mẫu khảo sát được chuẩn bị?','19 phiên bản',[8],'(4) Survey content; Nineteen versions'),
 ('text','Theo Survey method, có phải mỗi quốc gia chỉ được dùng đúng một phương pháp khảo sát không? Giải thích ngắn.','Không; có thể kết hợp nhiều phương pháp phù hợp môi trường truyền thông từng nước',[9],'B. Survey form distribution and collection method'),
 ('text','Theo Definitions phần non-school education, cơ sở không có phòng học vật lý và chỉ dạy online nhưng xác định được người học có được bao gồm không?','Có',[10],'C(D) Non-school education; last sentence'),
 ('text','Theo Definitions, “institutions associated with the Government of Japan” là các cơ sở do loại tổ chức nào thành lập?','Tổ chức liên quan đến Chính phủ Nhật Bản',[10],'D(C) Institutions associated with the Government of Japan'),
]:add(*x)
for q in [
 'Báo cáo cho biết tổng chi tiêu mua giáo trình tiếng Nhật của các cơ sở tại Germany năm 2021 là bao nhiêu?',
 'Theo báo cáo, thu nhập trung vị theo giờ của giáo viên tiếng Nhật ở Mexico năm 2021 là bao nhiêu?',
 'Báo cáo có dự báo số người học tiếng Nhật ở New Zealand năm 2040 không?',
 'Theo báo cáo, điểm JLPT N1 trung bình của giáo viên tiếng Nhật tại Finland năm 2021 là bao nhiêu?',
 'Báo cáo có thống kê số giờ mỗi người học tại Sri Lanka dành riêng cho viết Kanji mỗi tuần không?',
 'Theo báo cáo, tên và địa chỉ nhà của học viên nhỏ tuổi nhất tại Argentina là gì?',
]:add('unanswerable',q,'Không đủ bằng chứng',[],'Not among survey coverage/items or aggregate published data; full report search and source-form review required.')
write_json(path,rows)
write_json(ROOT/'benchmark/frozen_v2.json',{'created_at':now(),'file':str(path.relative_to(ROOT)),'sha256':sha(path),
 'counts':{'table':6,'image':5,'chart':5,'multihop':4,'text':4,'unanswerable':6},
 'reason':'V1 test inspected for errors: contradictory yes/no openings, ambiguous color wording and incomparable-unit question. V1 retained in full; v2 is new independent holdout, not a rerun or paraphrase set.',
 'no_test_tuning':'This file frozen before v2 retrieval or agent run. V1 failures remain reported.'})
print('Frozen 30 new v2 questions before running v2')
