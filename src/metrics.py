"""Measured trace metrics. Quality labels must be reviewed against original sources."""
from collections import Counter
from .common import read_json,ROOT

PRICING={'model':'gpt-5.4-mini','input_per_million':.75,'cached_input_per_million':.075,'output_per_million':4.50,
    'source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini','verified_date':'2026-11-14',
    'basis':'Standard API estimate from actual prompt/completion/cached usage, including image input tokens reported by API; not invoice.'}

def estimate_cost(trace):
    if not trace.get('resolved_model',trace.get('model','')).startswith('gpt-5.4-mini'):return None
    cost=0
    for e in trace.get('events',[]):
        if e.get('event')!='model':continue
        u=e.get('usage',{});prompt=u.get('prompt_tokens',0);cached=u.get('prompt_tokens_details',{}).get('cached_tokens',0)
        cost+=((prompt-cached)*.75+cached*.075+u.get('completion_tokens',0)*4.5)/1_000_000
    return round(cost,8)

def summarize(traces,reviews):
    labels={r['query_id']:r for r in reviews};answered=[t for t in traces if t['status']=='answered']
    supported=[];grades=[];context_grades=[];abstention=[];false_abstention=0;pass_count=0
    for t in traces:
        r=labels.get(t['query_id'])
        if r is None:raise ValueError(f'Missing review for {t["query_id"]}')
        supported+=r.get('citation_support',[])
        if r['answerable']:
            grades.append(r['answer_grade']);context_grades.append(r.get('context_grade',0))
            false_abstention+=t['status']=='abstain'
        else:abstention.append(r.get('abstention_correct',False))
        pass_count+=r['passed']
    n=len(traces);costs=[estimate_cost(t) for t in traces]
    return {'queries':n,'pass':{'n':pass_count,'N':n,'rate':pass_count/n if n else None},
        'answer_grade_counts':dict(Counter(grades)),'answer_grade_mean_over_2':sum(grades)/(2*len(grades)) if grades else None,
        'context_grade_counts':dict(Counter(context_grades)),
        'citation_support':{'n':sum(supported),'N':len(supported),'rate':sum(supported)/len(supported) if supported else None},
        'answers_with_citations':sum(bool(t['citations']) for t in answered),'answered':len(answered),
        'abstention':{'n':sum(abstention),'N':len(abstention),'rate':sum(abstention)/len(abstention) if abstention else None},
        'answerable_false_abstention':false_abstention,'errors':sum(t['status']=='error' for t in traces),
        'tool_use':{'n':sum(any(e['event']=='search' for e in t['events']) for t in traces),'N':n},
        'search_call_distribution':dict(Counter(sum(e['event']=='search' for e in t['events']) for t in traces)),
        'total_tokens':sum(t['usage'].get('total_tokens',0) for t in traces),
        'estimated_cost_usd':round(sum(c for c in costs if c is not None),6),'pricing':PRICING,
        'reviewer_type':'AI-assisted original-source review by Codex; not a student/human sign-off.'}
