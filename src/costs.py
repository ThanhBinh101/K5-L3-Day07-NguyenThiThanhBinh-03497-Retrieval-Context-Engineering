"""Display-only token accounting and counterfactual estimates; never calls a model API."""
import os
import sys
from pathlib import Path
from .common import ROOT,PRIVATE,read_json,read_jsonl,write_json,sha
from .metrics import PRICING

BASE_INSTRUCTION='Trả lời bằng tiếng Việt dựa trên tài liệu được cung cấp, dẫn số trang. Nếu thiếu bằng chứng, nói rõ không đủ thông tin.'


def usage_cost(prompt,cached,completion):
    if min(prompt,cached,completion)<0 or cached>prompt:raise ValueError('Invalid token counts')
    return round(((prompt-cached)*PRICING['input_per_million']+cached*PRICING['cached_input_per_million']+completion*PRICING['output_per_million'])/1_000_000,8)


def measured_usage(trace):
    if not trace:return None
    events=[e for e in trace.get('events',[]) if e.get('event')=='model']
    usages=[e.get('usage',{}) for e in events] or [trace.get('usage',{})]
    prompt=sum(u.get('prompt_tokens',0) for u in usages)
    completion=sum(u.get('completion_tokens',0) for u in usages)
    cached=sum(u.get('prompt_tokens_details',{}).get('cached_tokens',0) for u in usages)
    model=trace.get('resolved_model',trace.get('model',''))
    known=model in {'gpt-5.4-mini','gpt-5.4-mini-2026-03-17'}
    return {'query':trace.get('query',''),'model':model,'status':trace.get('status'),
        'prompt_tokens':prompt,'cached_input_tokens':cached,'uncached_input_tokens':prompt-cached,
        'completion_tokens':completion,'total_tokens':prompt+completion,'model_calls':len(events),
        'estimated_cost_usd':usage_cost(prompt,cached,completion) if known else None,
        'usage_source':'Actual API usage summed across every returned model call; input includes image tokens and repeated context.',
        'created_at':trace.get('created_at'),'trace_id':trace.get('id')}


class CostEstimator:
    def __init__(self):
        # Local fallback keeps the Day 06 environment untouched. Normal installs use requirements.txt.
        try:import tiktoken
        except ImportError:
            sys.path.insert(0,str(ROOT/'.local/cost-deps'))
            import tiktoken
        os.environ.setdefault('TIKTOKEN_CACHE_DIR',str(ROOT/'.local/tiktoken'))
        self.encoding=tiktoken.get_encoding('o200k_base')
        self.cache_path=ROOT/'.local/corpus_costs.json'
        self.cache=read_json(self.cache_path) if self.cache_path.exists() else {}
        self.counts={}
        for corpus,name in [('kanji','pages.jsonl'),('report','bonus_pages.json')]:
            source=PRIVATE/name;fingerprint=sha(source)
            cached=self.cache.get(corpus,{})
            if cached.get('sha256')!=fingerprint or cached.get('encoding')!='o200k_base':
                pages=read_jsonl(source) if name.endswith('jsonl') else read_json(source)
                # One complete text per physical page, not overlapping chunks.
                text='\n\n'.join(f'[Trang {p["page"]}]\n{p["text"]}' for p in pages)
                cached={'sha256':fingerprint,'encoding':'o200k_base','pages':len(pages),
                    'text_tokens':self.count(text),'text_chars':len(text)}
                self.cache[corpus]=cached
            self.counts[corpus]=cached
        write_json(self.cache_path,self.cache)
    def count(self,text):return len(self.encoding.encode(text,disallowed_special=()))
    def latest(self,corpus,query=''):
        files=sorted((ROOT/'results/private/agent').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        for path in files:
            t=read_json(path)
            if t.get('corpus')==corpus and (not query or t.get('query')==query):return t
        return None
    def compare(self,corpus,query='',trace=None):
        if corpus not in self.counts:raise ValueError('Kho tài liệu không hợp lệ.')
        if not isinstance(query,str) or len(query)>500:raise ValueError('Câu hỏi tối đa 500 ký tự.')
        trace=trace or self.latest(corpus,query)
        question=query or (trace.get('query','') if trace else '')
        # Baselines are explicit hypothetical single-call, text-only requests, NOT measured runs.
        overhead=self.count(BASE_INSTRUCTION)+self.count(question)+16
        full_input=self.counts[corpus]['text_tokens']+overhead
        output=300
        actual=measured_usage(trace)
        full={'prompt_tokens_estimate':full_input,'completion_tokens_assumed':output,'model_calls_assumed':1,
            'uncached_cost_usd':usage_cost(full_input,0,output),
            'cached_document_cost_usd':usage_cost(full_input,self.counts[corpus]['text_tokens'],output),
            'fits_context_estimate':full_input+output<=400000}
        question_only={'prompt_tokens_estimate':overhead,'completion_tokens_assumed':output,
            'uncached_cost_usd':usage_cost(overhead,0,output)}
        return {'corpus':corpus,'query':question,'pricing':PRICING,'actual':actual,
            'corpus_text':self.counts[corpus],'full_document':full,'question_only':question_only,
            'assumptions':{'tokenizer':'o200k_base; local estimate, not provider exact request count',
                'baseline':'One call; all selected corpus text, no images, no tool calls; 300 output tokens assumed. Does not measure answer quality.',
                'cache':'Cold baseline assumes no cache. Warm alternative assumes all document text cached; actual eligibility/hits are not guaranteed.',
                'local_retrieval_api_cost_usd':0,'local_compute':'CPU/electricity cost and one-time ingestion not measured.',
                'meaning':'This compares full-document/question-only strategies with the observed whole RAG agent run, not causal savings from each individual step.'}}
