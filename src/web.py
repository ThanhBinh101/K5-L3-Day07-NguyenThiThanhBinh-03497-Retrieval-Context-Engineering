"""Loopback UI for Kanji RAG; static files and private source routes are allowlisted."""
import argparse
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from .common import ROOT,PRIVATE,read_json,write_json,now
from .retrieval import Retriever,validate_alpha
from .bonus import ReportRetriever,render_page
from .handwriting import HandwritingMatcher
from .agent import Agent
from .costs import CostEstimator

class Service:
    def __init__(self):
        self.kanji=Retriever();self.report=ReportRetriever(self.kanji)
        self.retrievers={'kanji':self.kanji,'report':self.report}
        self.matcher=HandwritingMatcher(PRIVATE/'templates.json')
        self.inventory={p['page']:p for p in read_json(PRIVATE/'inventory.json')}
        self.costs=None;self.cost_error=None
        self.loading=True;self.error=None;self.agent_lock=threading.Lock()
        threading.Thread(target=self.load,daemon=True).start()
    def load(self):
        try:
            self.kanji.load_dense();self.report.load_dense()
            try:self.costs=CostEstimator()
            except Exception as e:self.cost_error=str(e)
        except Exception as e:self.error=str(e)
        finally:self.loading=False
    def status(self):
        from .model import load_env
        import os
        load_env()
        return {'ready':not self.loading and not self.error,'loading':self.loading,'error':self.error,
                'kanji':len(self.kanji.entries),'vocabulary':sum(len(e['vocabulary']) for e in self.kanji.entries),
                'pages':473,'bonus_pages':105,'model_configured':bool(os.getenv('OPENAI_API_KEY') and os.getenv('MODEL')),
                'model':os.getenv('MODEL'),'embedding':'multilingual-e5-small · 384 chiều',
                'bonus_status':'Chưa chấm test' if not (ROOT/'results/bonus_summary.json').exists() else read_json(ROOT/'results/bonus_summary.json').get('status','Chưa hoàn tất')}
    def retriever(self,payload):
        corpus=payload.get('corpus','kanji')
        if corpus not in self.retrievers:raise ValueError('Kho tài liệu không hợp lệ.')
        return self.retrievers[corpus]
    def decorate(self,result,corpus):
        for r in result['results']:
            r['corpus']=corpus
            r['source_url']=f'/source/{corpus}.pdf#page={r["page"]}'
            r['preview_url']=f'/api/page?corpus={corpus}&page={r["page"]}'
            images=self.inventory.get(r['page'],{}).get('images',[]) if corpus=='kanji' else []
            r['image_url']='/images/'+images[0]['file'] if images else None
        return result
    def search(self,p):
        c=p.get('corpus','kanji');r=self.retriever(p)
        result=r.search(p.get('query'),p.get('alpha',.5),p.get('top_k',5),p.get('lesson'))
        return self.decorate(result,c)
    def sweep(self,p):
        r=self.retriever(p);q=p.get('query');rows=[]
        for i in range(11):
            result=r.search(q,i/10,3,p.get('lesson'))
            result=self.decorate(result,p.get('corpus','kanji'));rows.append(result)
        return {'query':q,'rows':rows,'note':'Quét trên câu đang nhập, không dùng gold/test để chọn alpha.'}
    def ask(self,p):
        if not self.agent_lock.acquire(blocking=False):raise ValueError('Agent đang xử lý câu trước. Vui lòng chờ.')
        try:
            a=Agent(self.kanji,self.report,render_page)
            result=a.run(p.get('query'),p.get('alpha',.5),corpus=p.get('corpus','kanji'))
            if self.costs:
                result['cost_comparison']=self.costs.compare(p.get('corpus','kanji'),p.get('query',''),result)
            return result
        finally:self.agent_lock.release()
    def recognize(self,p):
        result=self.matcher.recognize(p.get('strokes'))
        for c in result['candidates']:
            e=next(e for e in self.kanji.entries if e['kanji']==c['kanji'])
            images=self.inventory[e['page']]['images']
            c.update(entry=e,image_url='/images/'+images[0]['file'] if images else None,
                     source_url=f'/source/kanji.pdf#page={e["page"]}')
        return result

class Handler(BaseHTTPRequestHandler):
    def send(self,status,data,mime='application/json; charset=utf-8'):
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-src 'self'; object-src 'self'")
        self.end_headers();self.wfile.write(data)
    def allowed(self):
        host=self.headers.get('Host','')
        if host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}:return False
        origin=self.headers.get('Origin')
        return origin is None or origin in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
    def do_GET(self):
        if not self.allowed():return self.send(403,{'error':'Chỉ truy cập từ localhost.'})
        u=urlsplit(self.path)
        try:
            if u.path=='/api/status':return self.send(200,self.server.service.status())
            if u.path=='/api/costs':
                service=self.server.service
                if not service.costs:return self.send(503,{'error':service.cost_error or 'Đang chuẩn bị bộ đếm token.'})
                q=parse_qs(u.query)
                return self.send(200,service.costs.compare(q.get('corpus',['kanji'])[0],q.get('query',[''])[0]))
            if u.path=='/api/metrics':
                names=['retrieval_summary.json','selection.json','agent_summary.json','bonus_summary.json']
                return self.send(200,{n:read_json(ROOT/'results'/n) for n in names if (ROOT/'results'/n).exists()})
            if u.path=='/api/page':
                q=parse_qs(u.query);path=render_page(q.get('corpus',['kanji'])[0],int(q.get('page',['0'])[0]))
            elif u.path in ['/source/kanji.pdf','/source/report.pdf']:
                path=PRIVATE/('source.pdf' if 'kanji' in u.path else 'bonus.pdf')
            elif u.path.startswith('/images/'):
                name=u.path.removeprefix('/images/')
                if '/' in name or '..' in name:raise ValueError('Tên ảnh không hợp lệ.')
                path=PRIVATE/'images'/name
            elif u.path in ['/','/app.js','/style.css']:
                path=ROOT/'ui'/('index.html' if u.path=='/' else u.path[1:])
            else:return self.send(404,{'error':'Không tìm thấy.'})
            return self.send(200,path.read_bytes(),mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        except (ValueError,FileNotFoundError) as e:return self.send(400,{'error':str(e)})
        except Exception:return self.send(500,{'error':'Không tải được tài nguyên.'})
    def do_POST(self):
        if not self.allowed():return self.send(403,{'error':'Origin không hợp lệ.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=1024*1024:raise ValueError('Payload không hợp lệ hoặc quá lớn.')
            p=json.loads(self.rfile.read(size))
            if not isinstance(p,dict):raise ValueError('Payload phải là object.')
            methods={'/api/search':'search','/api/sweep':'sweep','/api/ask':'ask','/api/recognize':'recognize'}
            if self.path not in methods:return self.send(404,{'error':'API không tồn tại.'})
            return self.send(200,getattr(self.server.service,methods[self.path])(p))
        except (ValueError,TypeError,KeyError) as e:return self.send(400,{'error':str(e)})
        except Exception as e:return self.send(503,{'error':str(e)})
    def log_message(self,*args):pass

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8707);args=p.parse_args()
    service=Service();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.service=service
    print(f'Kanji Sensei: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    finally:
        if service.kanji.client:service.kanji.client.close()

if __name__=='__main__':main()
