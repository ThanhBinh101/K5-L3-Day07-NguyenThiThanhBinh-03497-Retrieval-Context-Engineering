"""Reproducible dev sweep, freeze, and held-out evaluation. Application never loads gold."""
import argparse
import concurrent.futures
import statistics
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,PRIVATE,read_json,write_json,sha,now
from src.retrieval import Retriever
from src.bonus import ReportRetriever,render_page
from src.agent import Agent,pack_context

def cases(name,split,version="v1"):
    path=ROOT/f'benchmark/private/{name}.json'
    if name=='bonus' and split=='test' and version=='v2':
        path=ROOT/'benchmark/private/bonus_test_v2.json'
        if sha(path)!=read_json(ROOT/'benchmark/frozen_v2.json')['sha256']:raise RuntimeError('V2 frozen hash changed.')
        return read_json(path)
    if sha(path)!=read_json(ROOT/'benchmark/frozen.json')['files'][name]:raise RuntimeError('Frozen benchmark hash changed.')
    return [q for q in read_json(path) if q['split']==split]

def metric(n,d):return {'n':n,'N':d,'rate':n/d if d else None}

def retrieval(r,questions,alpha,budget):
    traces=[]
    for q in questions:
        start=time.perf_counter();out=r.search(q['question'],alpha,5)
        ranked=out['results'];gold=set(q['gold_pages']);ctx=pack_context(ranked,budget)
        traces.append({'query_id':q['id'],'question':q['question'],'answerable':q['answerable'],
            'ranking':[{k:c[k] for k in ['id','page','score','bm25_score','dense_score','text']} for c in ranked],
            'context':ctx,'hit1':bool(gold & {x['page'] for x in ranked[:1]}),
            'hit3':bool(gold & {x['page'] for x in ranked[:3]}),
            'complete_evidence_top3':bool(gold) and gold.issubset({x['page'] for x in ranked[:3]}),
            'context_complete':bool(gold) and gold.issubset({x['page'] for x in ctx}),
            'elapsed_ms':round((time.perf_counter()-start)*1000,2)})
    answerable=[t for t in traces if t['answerable']];N=len(answerable)
    summary={'alpha':alpha,'budget_chars_per_search':budget,'queries':len(traces),
        'Hit@1':metric(sum(t['hit1'] for t in answerable),N),'Evidence Hit@3':metric(sum(t['hit3'] for t in answerable),N),
        'Complete Evidence@3':metric(sum(t['complete_evidence_top3'] for t in answerable),N),
        'Context Evidence Rate':metric(sum(t['context_complete'] for t in answerable),N),
        'median_ms':statistics.median(t['elapsed_ms'] for t in traces),'cost_usd':0,
        'note':'Page-level evidence hit; multi-hop complete requires all gold pages. Citation support needs original review.'}
    return summary,traces

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['retrieval-dev','freeze','retrieval-test','agent-dev','agent-test']);p.add_argument('--suite',choices=['basic','bonus'],default='basic');p.add_argument('--config',choices=['baseline','small','selected','dense'],default='selected');p.add_argument('--run-label',default='');p.add_argument('--test-version',choices=['v1','v2'],default='v1');p.add_argument('--lock',default='results/experiment_lock.json');p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    config_path=ROOT/f'configs/{a.suite}-selected.json'
    if a.command.endswith('-test'):
        lock=read_json(ROOT/a.lock)
        if any(sha(ROOT/f)!=digest for f,digest in lock['files'].items()):raise RuntimeError('Experiment changed after pre-test lock; create a new independent evaluation.')
    if a.command=='freeze':
        if config_path.exists():raise SystemExit('Selection already frozen. Refuse overwrite.')
        rows=read_json(ROOT/'results'/f'{a.suite}_retrieval_dev.json')['configurations']
        best=max(rows,key=lambda x:(x['Evidence Hit@3']['n'],x['Hit@1']['n'],x['Context Evidence Rate']['n'],-abs(x['alpha']-.5),-x['alpha']))
        write_json(config_path,{'created_at':now(),'alpha':best['alpha'],'budget':4800,'top_k':5,'max_searches':4,
            'chosen_on':'dev','rule':read_json(ROOT/'configs/experiments.json')['selection_rule'],
            'benchmark_hash':read_json(ROOT/'benchmark/frozen.json')['files'][a.suite],
            'agent_validation':'Context budget chosen provisionally; agent dev small/selected compared before test.'})
        print('Frozen',a.suite,best['alpha']);return
    r=Retriever();report=ReportRetriever(r);retriever=r if a.suite=='basic' else report
    try:
        if a.command=='retrieval-dev':
            qs=cases(a.suite,'dev');summaries=[]
            # Warm up index once and record separately; latency comparisons below are warm-cache.
            start=time.perf_counter();retriever.load_dense();warm=time.perf_counter()-start
            for alpha in [i/10 for i in range(11)]:
                for budget in [2400,4800]:
                    summary,trace=retrieval(retriever,qs,alpha,budget);summaries.append(summary)
                    write_json(ROOT/f'results/private/{a.suite}/retrieval-dev/a{alpha:.1f}-b{budget}.json',trace)
            write_json(ROOT/f'results/{a.suite}_retrieval_dev.json',{'created_at':now(),'warmup_seconds':warm,'configurations':summaries})
            print(a.suite,[(x['alpha'],x['Hit@1']['n'],x['Evidence Hit@3']['n']) for x in summaries if x['budget_chars_per_search']==4800])
        elif a.command=='retrieval-test':
            selected=read_json(config_path);qs=cases(a.suite,'test',a.test_version);summaries=[]
            for tag,alpha,budget in [('baseline',0,2400),('selected',selected['alpha'],selected['budget'])]:
                summary,trace=retrieval(retriever,qs,alpha,budget);summary['tag']=tag;summaries.append(summary)
                path=ROOT/f'results/private/{a.suite}/retrieval-test{"-v2" if a.test_version=="v2" else ""}/{tag}.json'
                if path.exists():raise RuntimeError('Test run already exists; refuse overwrite.')
                write_json(path,trace)
            write_json(ROOT/f'results/{a.suite}_retrieval_test{"_v2" if a.test_version=="v2" else ""}.json',{'created_at':now(),'configurations':summaries})
            print(summaries)
        else:
            selected=read_json(config_path);split='dev' if a.command=='agent-dev' else 'test';qs=cases(a.suite,split,a.test_version)
            alpha=0 if a.config=='baseline' else 1 if a.config=='dense' else selected['alpha']
            budget=2400 if a.config in ['small','baseline'] else selected['budget']
            max_searches=1 if a.config=='baseline' else selected['max_searches']
            run_label=a.run_label or a.config
            test_suffix='-v2' if split=='test' and a.test_version=='v2' else ''
            folder=ROOT/f'results/private/{a.suite}/agent-{split}{test_suffix}/{run_label}'
            if split=='test' and (folder/'complete.json').exists():raise RuntimeError('Held-out run already complete; refuse overwrite.')
            agent=Agent(r,report,render_page);retriever.load_dense()
            def run(q):
                path=folder/f'{q["id"]}.json'
                if path.exists():return read_json(path)
                result=agent.run(q['question'],alpha,budget,selected['top_k'],max_searches,q['corpus'])
                result['query_id']=q['id'];write_json(path,result)
                print(q['id'],result['status'],round(result['elapsed_ms']/1000,1),'s',flush=True)
                return result
            with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:traces=list(pool.map(run,qs))
            summary={'created_at':now(),'suite':a.suite,'split':split,'config':a.config,'alpha':alpha,'budget':budget,
                'max_searches':max_searches,'queries':len(qs),'errors':sum(t['status']=='error' for t in traces),
                'total_tokens':sum(t['usage'].get('total_tokens',0) for t in traces),
                'median_seconds':statistics.median(t['elapsed_ms']/1000 for t in traces),
                'cost_usd':None,'cost_note':'See provider usage; no price estimate without verified input/output/cache/image rates.',
                'quality':'Pending original-source review, never inferred from status alone.'}
            write_json(folder/'complete.json',summary);write_json(ROOT/f'results/{a.suite}_agent_{split}{test_suffix}_{run_label}.json',summary)
            print(summary)
    finally:
        if r.client:r.client.close()
if __name__=='__main__':main()
