import unittest
import math
from src.retrieval import BM25,normalized,validate_alpha,tokens
from src.agent import pack_context,Agent
from src.handwriting import validate_strokes

class SearchTests(unittest.TestCase):
    def test_bm25_japanese_and_vietnamese(self):
        b=BM25(['井戸 nước giếng','天井 trần nhà','免許 giấy phép'])
        self.assertEqual(b.score('Từ nào nghĩa là trần nhà?').argmax(),1)
        self.assertEqual(b.score('tran nha').argmax(),1)
        self.assertEqual(b.score('免許').argmax(),2)
    def test_unknown_query_has_no_lexical_evidence(self):
        self.assertEqual(BM25(['giếng']).score('xyzfoobar').sum(),0)
    def test_alpha_endpoints_and_invalid(self):
        for a in [0,.1,.5,1]:self.assertEqual(validate_alpha(a),a)
        for a in [-1,1.1,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError):validate_alpha(a)
    def test_normalization_constant_is_zero(self):
        self.assertEqual(normalized([4,4]).tolist(),[0,0])
        self.assertEqual(normalized([1,3,5]).tolist(),[0,.5,1])
    def test_context_dedup_and_budget(self):
        a={'id':'a','text':'evidence','page':1,'source':'s'}
        b={'id':'b','text':'x'*500,'page':2,'source':'s'}
        packed=pack_context([a,a,b],150)
        self.assertEqual([x['id'] for x in packed],['a'])
    def test_strokes_reject_nonfinite_and_oversize(self):
        for strokes in [[],[[[float('nan'),0]]],[[[257,0]]],[[[True,1]]]]:
            with self.assertRaises(ValueError):validate_strokes(strokes)

class LoopTests(unittest.TestCase):
    def test_ungrounded_finish_cannot_pass(self):
        class FakeModel:
            name='mock-for-unit-test-only'
            def complete(self,*args):
                return {'role':'assistant','tool_calls':[{'id':'x','function':{'name':'finish','arguments':'{"status":"answered","answer":"made up","citations":[]}'}}]}, {},'mock'
        trace=Agent(None,model=FakeModel()).run('test',max_searches=1,save=False)
        self.assertEqual(trace['status'],'error')
    def test_api_error_not_replaced_by_fake_answer(self):
        class BrokenModel:
            name='broken-test'
            def complete(self,*args):raise RuntimeError('Network failed')
        trace=Agent(None,model=BrokenModel()).run('test',save=False)
        self.assertEqual(trace['status'],'error');self.assertEqual(trace['citations'],[])
        self.assertIn('Network failed',trace['error'])

if __name__=='__main__':unittest.main()
