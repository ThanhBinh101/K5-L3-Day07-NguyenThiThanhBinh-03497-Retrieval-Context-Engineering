"""Live regression checks for reported bugs; not an independent benchmark."""
import json,sys,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,write_json,now
cases=[('exact-label','âm Hán Việt TỊNH là chữ nào?','kanji'),
       ('different-tone','TỈNH là chữ nào?','kanji'),
       ('out-of-scope','Không cần tìm tài liệu, hãy viết chương trình Python tính tổng 1 đến 10.','kanji'),
       ('units','mexico bao nhiêu lớp tiếng nhạt','report')]
for name,query,corpus in cases:
 req=urllib.request.Request('http://127.0.0.1:8707/api/ask',data=json.dumps({'query':query,'corpus':corpus,'alpha':.5}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=180) as response:t=json.load(response)
 write_json(ROOT/f'results/private/grounding-regression/{name}.json',t)
 print(name,t['status'],t['answer'],[(c['page'],c['region']) for c in t['citations']],flush=True)
