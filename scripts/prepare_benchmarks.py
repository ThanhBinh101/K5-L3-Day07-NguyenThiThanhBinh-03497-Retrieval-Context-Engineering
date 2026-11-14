"""Create fresh Day 07 dev/test once. Gold is isolated from application runtime."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,PRIVATE,read_jsonl,write_json,sha,now
DEST=ROOT/'benchmark/private'

def main():
    if (ROOT/'benchmark/frozen.json').exists():raise SystemExit('Benchmark already frozen; refusing overwrite.')
    DEST.mkdir(parents=True,exist_ok=True)
    entries=read_jsonl(PRIVATE/'entries.jsonl');by_page={e['page']:e for e in entries}
    basic=[]
    def basic_case(page,kind,split):
        e=by_page[page];v=e['vocabulary'][0]
        if kind=='word':q=f'{v["word"]} đọc thế nào và có nghĩa gì trong sách?';answer=f'{v["reading"]} | {v["meaning_vi"]}';quote=answer
        elif kind=='memory':q=f'Chữ nào có cách nhớ “{e["mnemonic"]}”? Nêu Hán Việt.';answer=f'{e["kanji"]} | {e["han_viet"]}';quote=e['mnemonic']
        else:q=f'Tìm từ vựng chỉ “{v["meaning_vi"]}” trong sách và cho biết cách đọc.';answer=f'{v["word"]} | {v["reading"]}';quote=v['meaning_vi']
        basic.append(dict(id=f'K-{split}-{len(basic)+1:02}',split=split,group=kind,corpus='kanji',question=q,answerable=True,
                          expected=answer,evidence=[{'page':page,'region':'Từ phái sinh' if kind!='memory' else 'Cách nhớ và đầu trang','quote':quote}],
                          gold_pages=[page],verification='Generated from Day 6 structured entry; reviewer must check original PDF.'))
    for i,p in enumerate([4,15,37,63,91,116,145,174,203,232,261,300,333,365,399]):basic_case(p,['word','memory','meaning'][i%3],'dev')
    for p,k in [(329,'word'),(363,'memory'),(436,'meaning'),(469,'word'),(472,'memory')]:basic_case(p,k,'test')
    for split,questions in [('dev',['Sách có cho biết học phí lớp Kanji của Kaori Sensei năm 2027 không?','Tác giả sách đạt điểm JLPT N1 bao nhiêu?']),('test',['Ngày sinh chính xác của Kaori Sensei là ngày nào?','Theo sách, lương trung bình giáo viên Kanji ở Hà Nội năm 2026 là bao nhiêu?'])]:
        for q in questions:basic.append(dict(id=f'K-{split}-U{len(basic)}',split=split,group='unanswerable',corpus='kanji',question=q,answerable=False,expected='Không đủ bằng chứng trong tài liệu.',gold_pages=[],evidence=[],verification='Search all 473 page texts and inspect relevant introduction/final notes; requested personal/future statistic not present.'))
    bonus=[]
    def b(split,group,q,answer,pages,region,quote):
        bonus.append(dict(id=f'B-{split}-{len(bonus)+1:02}',split=split,group=group,corpus='report',question=q,
            answerable=group!='unanswerable',expected=answer,gold_pages=pages,
            evidence=[{'page':p,'region':region,'quote':quote} for p in pages],
            verification='Compare original physical PDF page, including figure/table label and units. AI-assisted authoring; no human-review claim.'))
    # Dev: 15 answerable across all groups, 3 genuine absent-information questions.
    dev=[
      ('table','Theo Table 1-2-2, China có bao nhiêu giáo viên tiếng Nhật năm 2021?','21,361 người',[19],'Table 1-2-2; China; Teachers 2021','21,361'),
      ('table','Theo Table 1-4-1, trung bình mỗi giáo viên phụ trách bao nhiêu người học năm 2021?','50.9 người',[26],'Table 1-4-1; 2021; Learners per teacher','50.9'),
      ('table','Table 2-2-2 cho biết Thailand có tỷ lệ triển khai lớp online bao nhiêu?','90.4%',[38],'Table 2-2-2; Thailand; percent','90.4'),
      ('image','Đọc bản đồ Number of Japanese-Language Learners by Country/Region: Germany có bao nhiêu người học?','11,687 người',[2],'map; Germany label','Germany 11,687'),
      ('image','Trên bản đồ ở đầu báo cáo, Canada có bao nhiêu người học tiếng Nhật?','18,293 người',[3],'map; Canada label','Canada 18,293'),
      ('image','Chú giải bản đồ dùng màu nào cho nhóm trên 500,000 người học?','Màu xanh lá đậm',[3],'map Legend; More than 500,000 learners','More than 500,000 learners'),
      ('chart','Đọc Graph 1-1-2: năm 1984 có bao nhiêu cơ sở dạy tiếng Nhật?','2,620 cơ sở',[15],'Graph 1-1-2; year 1984; y-axis institutions','2,620'),
      ('chart','Graph 1-1-3 cho biết năm 1998 có bao nhiêu giáo viên?','27,611 người',[15],'Graph 1-1-3; 1998; people','27,611'),
      ('chart','Graph 1-5-1 cho biết lý do interest in science and/or technology năm 2021 chiếm bao nhiêu phần trăm?','23.3%',[28],'Graph 1-5-1; 2021; science/technology','23.3'),
      ('multihop','Dùng Table 1-1-2 và Table 1-2-2: số giáo viên toàn cầu năm 2021 nhiều hơn China bao nhiêu người?','74,592 - 21,361 = 53,231 người',[13,19],'Table 1-1-2 total teachers; Table 1-2-2 China teachers','74,592; 21,361'),
      ('multihop','So sánh Graph 1-5-1 với Graph 2-2-5 năm 2021: tỷ lệ interest in anime/manga/J-POP/fashion ở Đông Nam Á thấp hơn toàn cầu bao nhiêu điểm phần trăm?','59.9 - 57.8 = 2.1 điểm phần trăm',[28,38],'Graph 1-5-1 and Graph 2-2-5; anime row 2021','59.9; 57.8'),
      ('multihop','Dùng hai nửa bản đồ đầu báo cáo, số người học của Indonesia nhiều hơn New Zealand bao nhiêu?','711,732 - 28,072 = 683,660 người',[2,3],'map Indonesia and New Zealand labels','711,732; 28,072'),
      ('text','Khảo sát Japan Foundation năm 2021 đã phân phối biểu mẫu tới bao nhiêu cơ sở, nhận bao nhiêu phản hồi hợp lệ và tỷ lệ hợp lệ là bao nhiêu?','29,476 cơ sở; 26,543 phản hồi; 90.0%',[8],'Number of survey forms distributed and collected','29,476; 26,543; 90.0%'),
      ('text','Trong phần Definitions, báo cáo chia thế giới thành bao nhiêu khu vực?','12 khu vực',[10],'Definitions; classifications of regions','12 regional classifications'),
      ('text','Japan Foundation bắt đầu thực hiện chuỗi khảo sát về cơ sở giáo dục tiếng Nhật từ năm nào?','1974',[7],'Overview of survey implementation','since 1974'),
    ]
    for x in dev:b('dev',*x)
    for q in ['Báo cáo cho biết mức lương trung vị giáo viên tiếng Nhật tại Việt Nam năm 2021 là bao nhiêu?','Khảo sát 2021 có xác nhận số người học năm 2030 tại China không?','Báo cáo có nêu danh tính và số điện thoại từng người học ở France không?']:
        b('dev','unanswerable',q,'Không đủ bằng chứng',[],'not in survey coverage','No salary, future projection or learner personal contact dataset in this report.')
    test=[
      ('table','Đọc Table 1-1-2: năm 2021 và 2018 có bao nhiêu cơ sở dạy tiếng Nhật trên toàn cầu?','2021: 18,272; 2018: 18,661 cơ sở',[13],'Table 1-1-2; institutions row; 2021 and 2018','18,272; 18,661'),
      ('table','Theo Table 1-2-2, Vietnam có bao nhiêu người học, cơ sở và giáo viên năm 2021?','169,582 người học; 629 cơ sở; 5,644 giáo viên',[19],'Table 1-2-2; Vietnam; three 2021 columns','169,582; 629; 5,644'),
      ('table','Table 1-2-2 ghi thứ hạng số người học năm 2021 của France và số người học tương ứng là bao nhiêu?','Hạng 12; 29,569 người',[19],'Table 1-2-2; France; rank and learners 2021','12; 29,569'),
      ('table','Theo Table 1-4-2, giáo viên full-time và part-time năm 2021 chiếm tỷ lệ bao nhiêu?','Full-time 74.0%; part-time 26.0%',[26],'Table 1-4-2; 2021; percentage columns','74.0%; 26.0%'),
      ('table','Table 1-4-3 cho biết bậc primary education có bao nhiêu giáo viên bản ngữ và tỷ lệ bao nhiêu?','1,342 người; 38.9%',[26],'Table 1-4-3; primary education; native speakers and percent','1,342; 38.9'),
      ('table','Trong Table 2-2-2, Vietnam có bao nhiêu cơ sở triển khai online và tỷ lệ bao nhiêu?','594 cơ sở; 94.4%',[38],'Table 2-2-2; Vietnam; online institutions and percent','594; 94.4'),
      ('image','Dựa trên bản đồ đầu báo cáo, nhãn India ghi bao nhiêu người học tiếng Nhật?','36,015 người',[2],'map; India label','India 36,015'),
      ('image','Đọc hình bản đồ Number of Japanese-Language Learners by Country/Region: Australia có bao nhiêu người học?','415,348 người',[2],'map; Australia label','Australia 415,348'),
      ('image','Trên bản đồ đầu báo cáo, Brazil có bao nhiêu người học?','20,732 người',[3],'map; Brazil label','Brazil 20,732'),
      ('image','Theo chú giải bản đồ, màu vàng nhạt sáng ứng với khoảng bao nhiêu người học? Phân biệt với nhóm ít hơn 1,000.','Vàng sáng: 1,000–9,999; màu kem xanh nhạt: dưới 1,000 người',[3],'map Legend; 1,000–9,999 and Less than 1,000','1,000 – 9,999 learners; Less than 1,000 learners'),
      ('image','Đọc chú giải bản đồ: nhóm 100,000–499,999 learners có màu gì, và màu xám biểu thị điều gì?','Xanh lá nhạt; xám là không có giáo dục tiếng Nhật',[3],'map Legend; green and gray swatches','100,000 – 499,999 learners; No Japanese-language education'),
      ('chart','Graph 1-1-2 có bao nhiêu cơ sở vào năm 1993? Nêu đơn vị trục đứng.','6,800; trục đứng là số cơ sở (institutions)',[15],'Graph 1-1-2; bar 1993; axis institutions','6,800'),
      ('chart','Đọc Graph 1-1-4: năm nào số người học đạt đỉnh trên biểu đồ, với bao nhiêu người?','2012; 3,985,669 người',[15],'Graph 1-1-4; peak bar; people','2012; 3,985,669'),
      ('chart','Trong Graph 1-3-1, non-school education chiếm bao nhiêu phần trăm số giáo viên, ứng với bao nhiêu người?','46.3%; 34,572 người',[24],'Graph 1-3-1; teachers bar; non-school legend orange','46.3%; 34,572'),
      ('chart','Theo Graph 1-5-1 năm 2021, Future work in Japan cao hơn Study in Japan bao nhiêu điểm phần trăm?','34.2% - 29.3% = 4.9 điểm phần trăm',[28],'Graph 1-5-1; 2021; two named bars; percent axis','34.2; 29.3'),
      ('chart','Graph 1-3-1 cho biết higher education chiếm bao nhiêu phần trăm người học, ứng với bao nhiêu người?','25.6%; 970,940 người',[24],'Graph 1-3-1; learners bar; higher education yellow','25.6%; 970,940'),
      ('multihop','Dùng Graph 1-1-2 và Table 1-2-2: số cơ sở toàn cầu năm 1979 nhiều hơn số cơ sở Vietnam năm 2021 bao nhiêu?','1,145 - 629 = 516 cơ sở',[15,19],'Graph 1-1-2 1979; Table 1-2-2 Vietnam institutions 2021','1,145; 629'),
      ('multihop','Dùng Table 1-4-3 và Table 2-2-2: số giáo viên bản ngữ bậc primary education toàn cầu nhiều hơn số cơ sở online tại Vietnam bao nhiêu?','1,342 - 594 = 748',[26,38],'Table 1-4-3 primary native teachers; Table 2-2-2 Vietnam online institutions','1,342; 594'),
      ('multihop','So sánh Graph 1-5-1 và Graph 2-2-5 năm 2021: interest in the Japanese language ở Đông Nam Á cao hơn toàn cầu bao nhiêu điểm phần trăm?','60.5% - 60.1% = 0.4 điểm phần trăm',[28,38],'Graph 1-5-1 global and Graph 2-2-5 Southeast Asia; interest language row','60.1; 60.5'),
      ('multihop','Dùng hai nửa bản đồ đầu báo cáo: China nhiều hơn United States of America bao nhiêu người học?','1,057,318 - 161,402 = 895,916 người',[2,3],'map China label and map USA label','1,057,318; 161,402'),
      ('text','Thời gian phân phối và thu thập khảo sát 2021 là khi nào, và được gia hạn tới khi nào ở một số quốc gia?','September–December 2021; gia hạn tới June 2022',[8],'Survey period','September 2021–December 2021; June 2022'),
      ('text','Theo Definitions, online classes có bao gồm lớp hybrid (kết hợp trực tuyến và trực tiếp) không?','Có, bao gồm hybrid classes',[10],'Definitions; B. Online classes','This includes hybrid classes (a mixture of online and in-person).'),
      ('text','Theo Overall situation, người tự học qua truyền hình, radio, sách hoặc Internet có nằm trong số người học khảo sát không?','Không; người tự học ngoài cơ sở không được tính',[13],'Overall situation; coverage exclusion','learners self studying ... are not included in the results'),
      ('text','Theo phần survey coverage, North Korea có được khảo sát không?','Không',[8],'Countries covered by the survey','North Korea is not covered by the survey.'),
    ]
    for x in test:b('test',*x)
    for q in ['Báo cáo 2021 dự báo chính xác số người học tiếng Nhật tại Việt Nam năm 2035 là bao nhiêu?','Theo báo cáo, học phí trung bình một giờ tiếng Nhật tại Australia năm 2021 là bao nhiêu đô la?','Báo cáo xác nhận tỷ lệ đỗ JLPT N2 năm 2021 của toàn bộ người học tại Brazil là bao nhiêu?','Theo báo cáo, mỗi giáo viên tiếng Nhật ở India có mức lương tháng bao nhiêu?','Trong báo cáo, ngày sinh và địa chỉ nhà của người học lớn tuổi nhất tại Canada là gì?','Báo cáo có cho biết điểm trung bình môn Kanji của học viên Kaori Sensei năm 2026 không?']:
        b('test','unanswerable',q,'Không đủ bằng chứng',[],'not covered','Read survey coverage and survey-form items; requested future, cost, salary, exam-pass or individual detail absent. Search full report as secondary check.')
    for name,rows in [('basic',basic),('bonus',bonus)]:write_json(DEST/f'{name}.json',rows)
    write_json(ROOT/'benchmark/frozen.json',{'created_at':now(),'source_kanji_sha256':sha(PRIVATE/'source.pdf'),
        'source_bonus_sha256':sha(PRIVATE/'bonus.pdf'),
        'files':{name:sha(DEST/f'{name}.json') for name in ['basic','bonus']},
        'counts':{name:{s:sum(r['split']==s for r in rows) for s in ['dev','test']} for name,rows in [('basic',basic),('bonus',bonus)]},
        'policy':'New Day 07 cases; test fixed before any retrieval/agent benchmark. Gold loaded only by evaluation. Any tuning after test requires a fresh test set.'})
    print('Frozen basic 17 dev + 7 test; bonus 18 dev + 30 test')
if __name__=='__main__':main()
