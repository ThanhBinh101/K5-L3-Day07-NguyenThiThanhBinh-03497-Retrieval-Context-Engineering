"""BM25 + Day 6 dense search; alpha is the normalized dense weight."""
import math
import re
import threading
import time
import unicodedata
from collections import Counter, OrderedDict
import numpy as np
from .common import DAY6, ROOT, PRIVATE, read_jsonl


STOP = set('từ nào nghĩa là gì trong tài liệu theo của và có được cho hãy tìm biết cách đọc một những các bao nhiêu về bằng'.split())

def tokens(text):
    text=unicodedata.normalize('NFKC',text).lower()
    result=[]
    for part in re.findall(r'[^\W_]+',text,flags=re.UNICODE):
        if re.search(r'[\u3040-\u30ff\u3400-\u9fff]',part):
            result.extend(part)
            result.extend(part[i:i+2] for i in range(len(part)-1))
        elif part not in STOP:
            result.append(part)
            folded=''.join(c for c in unicodedata.normalize('NFD',part) if unicodedata.category(c)!='Mn').replace('đ','d')
            result.append('fold:'+folded)
    return result


def validate_alpha(value):
    if isinstance(value,bool):raise ValueError('Alpha phải là số từ 0 đến 1.')
    value=float(value)
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError('Alpha phải từ 0 đến 1.')
    return value


def normalized(values):
    values=np.asarray(values,dtype=float)
    lo,hi=values.min(),values.max()
    return (values-lo)/(hi-lo) if hi>lo else np.zeros_like(values)


class BM25:
    def __init__(self,documents,k1=1.5,b=.75):
        self.docs=[Counter(tokens(t)) for t in documents]
        self.length=np.array([sum(d.values()) for d in self.docs])
        self.avg=max(float(self.length.mean()),1)
        self.k1,self.b=k1,b
        df=Counter(t for d in self.docs for t in d)
        self.idf={t:math.log(1+(len(self.docs)-n+.5)/(n+.5)) for t,n in df.items()}
    def score(self,query):
        out=np.zeros(len(self.docs))
        for t in set(tokens(query)):
            f=np.array([d.get(t,0) for d in self.docs],dtype=float)
            out+=self.idf.get(t,0)*f*(self.k1+1)/(f+self.k1*(1-self.b+self.b*self.length/self.avg))
        return out


class Retriever:
    def __init__(self):
        self.entries=read_jsonl(PRIVATE/'entries.jsonl')
        self.by_page={e['page']:e for e in self.entries}
        self.chunks=read_jsonl(PRIVATE/'chunks_B.jsonl')
        pages=read_jsonl(PRIVATE/'pages.jsonl')
        present={c['page'] for c in self.chunks}
        self.chunks += [dict(id=p['page_id'],page=p['page'],text=p['text'],source='KANJI N2.pdf',
                             document_id='kanji_n2_kaori',kind='overview') for p in pages if p['page'] not in present]
        self.index={c['id']:i for i,c in enumerate(self.chunks)}
        self.lexical=BM25([c['text'] for c in self.chunks])
        self.model=None;self.client=None
        self.lock=threading.RLock();self.cache=OrderedDict()

    def load_dense(self):
        with self.lock:
            if self.model is not None:return
            import os
            os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
            from sentence_transformers import SentenceTransformer
            import torch
            from qdrant_client import QdrantClient,models
            torch.set_num_threads(4)
            model=SentenceTransformer(str(DAY6/'.local/model'),device='cpu',local_files_only=True)
            model.max_seq_length=512
            client=QdrantClient(path=str(ROOT/'.local/qdrant'))
            if client.count('kanji_B',exact=True).count!=454:
                client.close();raise RuntimeError('Day 6 vector index không đủ 454 mục.')
            if not client.collection_exists('kanji_overviews'):
                extra=self.chunks[454:]
                vec=model.encode(['passage: '+c['text'] for c in extra],normalize_embeddings=True,show_progress_bar=False)
                client.create_collection('kanji_overviews',vectors_config=models.VectorParams(size=384,distance=models.Distance.COSINE))
                client.upsert('kanji_overviews',[models.PointStruct(id=i,vector=v.tolist(),payload=c) for i,(c,v) in enumerate(zip(extra,vec))])
            self.model,self.client=model,client

    def components(self,query,dense=True):
        key=(query,dense)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key);return self.cache[key]
            lexical=self.lexical.score(query)
            semantic=np.zeros(len(self.chunks))
            if dense:
                self.load_dense()
                vector=self.model.encode(['query: '+query],normalize_embeddings=True,show_progress_bar=False)[0]
                for collection in ['kanji_B','kanji_overviews']:
                    points=self.client.query_points(collection,query=vector.tolist(),limit=len(self.chunks),with_payload=True).points
                    for p in points:semantic[self.index[p.payload['id']]]=p.score
            self.cache[key]=(lexical,semantic)
            if len(self.cache)>256:self.cache.popitem(last=False)
            return lexical,semantic

    def search(self,query,alpha=.5,top_k=5,lesson=None):
        if not isinstance(query,str) or not 1<=len(query.strip())<=500:raise ValueError('Nhập câu hỏi từ 1 đến 500 ký tự.')
        alpha=validate_alpha(alpha)
        if isinstance(top_k,bool) or not isinstance(top_k,int) or not 1<=top_k<=30:raise ValueError('top_k phải từ 1 đến 30.')
        if lesson is not None and (isinstance(lesson,bool) or not isinstance(lesson,int) or not 1<=lesson<=16):raise ValueError('Bài học phải từ 1 đến 16.')
        started=time.perf_counter()
        lexical,semantic=self.components(query.strip(),dense=alpha>0)
        scores=(1-alpha)*normalized(lexical)+alpha*normalized(semantic)
        # Stable ordering and explicit empty lexical behavior; no arbitrary zero-score results.
        order=sorted(range(len(scores)),key=lambda i:(-scores[i],self.chunks[i]['page']))
        results=[]
        for i in order:
            c=self.chunks[i]
            if lesson is not None and c.get('lesson')!=lesson:continue
            if alpha==0 and lexical[i]<=0:continue
            results.append({**c,'score':round(float(scores[i]),6),'bm25_score':round(float(lexical[i]),6),
                'dense_score':round(float(semantic[i]),6) if alpha>0 else None,
                'entry':self.by_page.get(c['page']),'rank':len(results)+1})
            if len(results)==top_k:break
        return {'query':query,'alpha':alpha,'method':'bm25' if alpha==0 else 'dense' if alpha==1 else 'hybrid',
                'results':results,'elapsed_ms':round(1000*(time.perf_counter()-started),2),
                'normalization':'per query min-max over all 473 indexed pages; score is not probability'}
