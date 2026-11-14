"""Full-document report retrieval and original-page rendering."""
import subprocess
import re
import threading
from collections import OrderedDict
from pathlib import Path
from .common import ROOT,PRIVATE,read_json,sha
from .retrieval import Retriever,BM25
import numpy as np

class ReportRetriever(Retriever):
    def __init__(self,shared):
        self.shared=shared;self.entries=[];self.by_page={};self.chunks=[]
        self.pages=read_json(PRIVATE/'bonus_pages.json')
        self.collection='jpf2021_'+sha(PRIVATE/'bonus_pages.json')[:12]
        self.figure_pages={}
        for page in self.pages:
            for kind,number in re.findall(r'(Graph|Table)\s+(\d+-\d+-\d+)',page['text'],re.I):
                self.figure_pages.setdefault(kind.lower()+':'+number,set()).add(page['page'])
        for page in self.pages:
            text=page['text']
            for i,start in enumerate(range(0,max(len(text),1),1400)):
                chunk={**page,'id':page['id']+f':c{i}','text':text[start:start+1800]}
                self.chunks.append(chunk)
        self.index={c['id']:i for i,c in enumerate(self.chunks)}
        self.lexical=BM25([c['text'] for c in self.chunks])
        self.lock=shared.lock;self.cache=OrderedDict();self.model=None;self.client=None
    def load_dense(self):
        with self.lock:
            if self.model is not None:return
            self.shared.load_dense();model=self.shared.model;client=self.shared.client
            from qdrant_client import models
            if not client.collection_exists(self.collection):
                vec=model.encode(['passage: '+c['text'] for c in self.chunks],normalize_embeddings=True,batch_size=16,show_progress_bar=False)
                client.create_collection(self.collection,vectors_config=models.VectorParams(size=384,distance=models.Distance.COSINE))
                for start in range(0,len(self.chunks),64):
                    client.upsert(self.collection,[models.PointStruct(id=i,vector=vec[i].tolist(),payload=self.chunks[i]) for i in range(start,min(start+64,len(vec)))])
            if client.count(self.collection,exact=True).count!=len(self.chunks):raise RuntimeError('Report index khác corpus; cần build index mới.')
            self.model,self.client=model,client
    def components(self,query,dense=True):
        with self.lock:
            key=(query,dense)
            if key in self.cache:return self.cache[key]
            lexical=self.lexical.score(query);semantic=np.zeros(len(self.chunks))
            if dense:
                self.load_dense()
                vector=self.model.encode(['query: '+query],normalize_embeddings=True,show_progress_bar=False)[0]
                for p in self.client.query_points(self.collection,query=vector.tolist(),limit=len(self.chunks),with_payload=True).points:
                    semantic[self.index[p.payload['id']]]=p.score
            self.cache[key]=(lexical,semantic)
            if len(self.cache)>256:self.cache.popitem(last=False)
            return lexical,semantic
    def search(self,query,alpha=.5,top_k=5,lesson=None):
        from .retrieval import validate_alpha
        import time
        started=time.perf_counter();alpha=validate_alpha(alpha)
        if not isinstance(query,str) or not 1<=len(query.strip())<=500:raise ValueError('Câu hỏi phải từ 1 đến 500 ký tự.')
        if isinstance(top_k,bool) or not isinstance(top_k,int) or not 1<=top_k<=30:raise ValueError('top_k phải từ 1 đến 30.')
        # Explicit figure identifiers and map mentions come from the user's query, never gold.
        requested=[k.lower()+':'+n for k,n in re.findall(r'(Graph|Table)\s+(\d+-\d+-\d+)',query,re.I)]
        pages=set().union(*(self.figure_pages.get(k,set()) for k in requested)) if requested else set()
        is_map=bool(re.search(r'bản đồ|\bmap\b|country\s*/\s*region',query,re.I))
        if is_map and not requested:pages={2,3}
        lexical,semantic=self.components(query,dense=alpha>0)
        from .retrieval import normalized
        scores=(1-alpha)*normalized(lexical)+alpha*normalized(semantic)
        order=sorted(range(len(scores)),key=lambda i:(-scores[i],self.chunks[i]['page']))
        seen=set();rows=[]
        for i in order:
            c=self.chunks[i]
            if pages and c['page'] not in pages:continue
            if c['page'] in seen:continue
            if alpha==0 and lexical[i]<=0:continue
            seen.add(c['page'])
            rows.append({**c,'score':round(float(scores[i]),6),'bm25_score':round(float(lexical[i]),6),
                         'dense_score':round(float(semantic[i]),6) if alpha else None,'rank':len(rows)+1})
            if len(rows)==top_k:break
        return {'query':query,'alpha':alpha,'method':'bm25' if alpha==0 else 'dense' if alpha==1 else 'hybrid',
                'results':rows,'elapsed_ms':round((time.perf_counter()-started)*1000,2),
                'query_filter':{'figure_ids':requested,'map':is_map,'pages':sorted(pages)},
                'filter_source':'explicit figure/map reference in search query only; no benchmark gold',
                'normalization':'per query min-max over all report chunks; distinct pages in final rank'}

RENDER_LOCK=threading.Lock()
def render_page(corpus,page):
    count=473 if corpus=='kanji' else 105 if corpus=='report' else 0
    if isinstance(page,bool) or not isinstance(page,int) or not 1<=page<=count:raise ValueError('Trang không hợp lệ.')
    out=PRIVATE/'rendered'/corpus
    out.mkdir(parents=True,exist_ok=True)
    target=out/f'page-{page:03}.png'
    with RENDER_LOCK:
        if not target.exists():
            source=PRIVATE/('source.pdf' if corpus=='kanji' else 'bonus.pdf')
            prefix=out/f'tmp-{page}'
            subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','1700','-singlefile','-png',str(source),str(prefix)],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
            prefix.with_suffix('.png').replace(target)
    return target
