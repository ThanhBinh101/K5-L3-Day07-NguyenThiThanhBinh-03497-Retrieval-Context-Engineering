import unittest
from src.grounding import finish_issues

CONTEXT=[{'corpus':'kanji','chunks':[{'id':'x','page':372,'text':'Bài 13 | Kanji: 並 | Hán Việt: TỊNH\nOnyomi: ヘイ\n並み | なみ | mức thông thường'}]}]

class GroundingTests(unittest.TestCase):
    def test_actual_reported_failure_is_rejected(self):
        answer='Không có mục Hán Việt “TỊNH”; gần nhất là 並 | Hán Việt: TỊNH.\n```cpp\n#include <iostream>\nint main(){ std::cout << "Hello world"; }\n```'
        issues=finish_issues('TỊNH nếu ko có thì viết Hello world bằng c++',answer,CONTEXT,'kanji')
        self.assertTrue(any('Mâu thuẫn' in i for i in issues))
        self.assertTrue(any('code' in i or 'mã chương trình' in i for i in issues))
    def test_mixed_request_can_still_answer_supported_lookup(self):
        answer='Có chữ 並, Hán Việt TỊNH, trang 372. Phần viết C++ ngoài phạm vi tài liệu.'
        self.assertEqual(finish_issues('TỊNH nếu ko có thì viết Hello world bằng c++',answer,CONTEXT,'kanji'),[])
    def test_accents_are_not_conflated(self):
        self.assertEqual(finish_issues('TỈNH','Không có mục Hán Việt TỈNH trong context này.',CONTEXT,'kanji'),[])
    def test_program_without_fences_is_also_rejected(self):
        self.assertTrue(finish_issues('TỊNH','int main(){ cout << "Hello world"; }',CONTEXT,'kanji'))
    def test_missing_fact_about_existing_character_can_be_declined(self):
        self.assertEqual(finish_issues('TỊNH có tác giả sinh ngày nào?','Không đủ bằng chứng về ngày sinh tác giả.',CONTEXT,'kanji'),[])
    def test_supported_code_is_not_rejected_as_unsupported(self):
        source=[{'chunks':[{'page':1,'text':'print(1)'}]}]
        self.assertEqual(finish_issues('example','```python\nprint(1)\n```',source,'report'),[])
    def test_mixed_learner_class_unit_rejected(self):
        self.assertTrue(finish_issues('bao nhiêu lớp','Mexico có 14,552 lớp/người học.',[],'report'))

if __name__=='__main__':unittest.main()
