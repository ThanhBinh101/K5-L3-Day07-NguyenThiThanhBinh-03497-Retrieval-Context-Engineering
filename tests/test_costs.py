import unittest
from src.costs import usage_cost,measured_usage

class CostTests(unittest.TestCase):
    def test_cached_tokens_are_not_charged_twice(self):
        self.assertAlmostEqual(usage_cost(1000,800,100),.00066)
        self.assertAlmostEqual(usage_cost(1000,0,100),.0012)
    def test_repeated_calls_and_reasoning_not_double_counted(self):
        trace={'model':'gpt-5.4-mini-2026-03-17','events':[
            {'event':'model','usage':{'prompt_tokens':1000,'completion_tokens':100,'prompt_tokens_details':{'cached_tokens':800},'completion_tokens_details':{'reasoning_tokens':50}}},
            {'event':'search'},
            {'event':'model','usage':{'prompt_tokens':2000,'completion_tokens':200,'prompt_tokens_details':{'cached_tokens':1000}}}]}
        x=measured_usage(trace)
        self.assertEqual(x['prompt_tokens'],3000);self.assertEqual(x['completion_tokens'],300)
        self.assertEqual(x['cached_input_tokens'],1800);self.assertEqual(x['total_tokens'],3300)
        self.assertEqual(x['model_calls'],2)
        self.assertAlmostEqual(x['estimated_cost_usd'],.002385)
    def test_missing_trace_and_unknown_price(self):
        self.assertIsNone(measured_usage(None))
        x=measured_usage({'model':'other-provider-model','usage':{'prompt_tokens':100,'completion_tokens':10}})
        self.assertEqual(x['total_tokens'],110);self.assertIsNone(x['estimated_cost_usd'])
    def test_impossible_cached_count_rejected(self):
        with self.assertRaises(ValueError):usage_cost(10,11,0)

if __name__=='__main__':unittest.main()
