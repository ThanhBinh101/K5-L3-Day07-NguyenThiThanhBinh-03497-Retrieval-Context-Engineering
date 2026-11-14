"""Index every page of the authorized 105-page Japan Foundation report."""
import logging,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pypdf import PdfReader
from src.common import ROOT,PRIVATE,write_json,read_json,sha,now
logging.getLogger('pypdf').setLevel(logging.ERROR)
r=PdfReader(PRIVATE/'bonus.pdf');rows=[]
for n,p in enumerate(r.pages,1):
 text=p.extract_text(extraction_mode='layout') or ''
 rows.append({'id':f'jpf2021:p{n:03}','page':n,'text':text,'source':'Japan Foundation Survey 2021',
              'document_id':'jpf2021','kind':'report','page_label':str(n-6) if 7<=n<=100 else None,
              'region':'whole page; original rendering available via view_page'})
corrections=read_json(ROOT/'data/jpf2021_map_extraction.json')
if sha(PRIVATE/'bonus.pdf')!=corrections['source_sha256']:raise RuntimeError('Bonus PDF differs from verified map extraction snapshot.')
for number,text in corrections['pages'].items():
    rows[int(number)-1]['text']=text
    rows[int(number)-1]['extraction']='vision-transcribed visible map half; original native extraction had off-page text from shared map artwork'
if '--verify-only' in sys.argv:
    generated=(json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode()
    matches=hashlib.sha256(generated).hexdigest()==sha(PRIVATE/'bonus_pages.json')
    print('Extraction snapshot reproducible:',matches)
    raise SystemExit(0 if matches else 1)
write_json(PRIVATE/'bonus_pages.json',rows)
write_json(ROOT/'results/bonus_source.json',{'title':'Survey Report on Japanese-Language Education Abroad 2021',
 'author':'Japan Foundation','version':'All_contents_r2.pdf','url':'https://www.jpf.go.jp/e/project/japanese/survey/result/dl/survey2021/All_contents_r2.pdf',
 'landing_page':'https://www.jpf.go.jp/e/project/japanese/survey/result/survey21.html',
 'accessed_at':now(),'pages':len(r.pages),'sha256':sha(PRIVATE/'bonus.pdf'),
 'permission':'Survey data free to use with citation per publisher Guidelines for Use.',
 'attribution':'Copyright Japan Foundation. Created by editing the Survey Report on Japanese-Language Education Abroad (the Japan Foundation).',
 'indexed_pages':len(rows),'empty_pages':[p['page'] for p in rows if not p['text'].strip()],
 'visual_pipeline':'Native layout text for all pages + verified map-half vision snapshot + original-page vision for report answers. No synthetic chart or gold evidence used for retrieval.',
 'page_numbering':'Citations use physical PDF pages (printed report page + 6).',
 'limitations':'Native text extraction may interleave table cells; visual page verification required. Scanned images cannot be assumed correct from extracted text alone.'})
print(len(rows),'pages; empty',[p['page'] for p in rows if not p['text'].strip()])
for p in rows[:36]:
 print(p['page'],p['text'].strip()[:100].replace('\n',' '))
