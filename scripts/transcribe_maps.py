"""Vision extraction of BOTH map halves, independent of any benchmark/gold."""
import sys,base64,concurrent.futures,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,PRIVATE,read_json,write_json,now
from src.model import Model
from src.agent import tool
from src.bonus import render_page
schema=[tool('transcribe','Transcribe visible map labels and legend. No invented content.',{'text':{'type':'string'}},['text'])]
def run(page):
 path=render_page('report',page);m=Model()
 msg,u,model=m.complete([{'role':'user','content':[{'type':'text','text':'Transcribe ALL visible country/region names, their numeric learner labels, and ALL legend color categories on THIS image. State map title. Only content actually visible inside image, not other half of map or outside page. Do not infer missing legend or cropped labels. Use plain text; describe colors only where swatches visible. Call transcribe.'},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'detail':'high'}}]}],schema,'required')
 text=json.loads(msg['tool_calls'][0]['function']['arguments'])['text']
 write_json(ROOT/f'results/private/map-transcription-{page}.json',{'page':page,'text':text,'usage':u,'model':model,'created_at':now(),'provenance':'Vision extraction from whole original rendered page; benchmark not loaded.'})
 return page,text
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,[2,3]))
 pages=read_json(PRIVATE/'bonus_pages.json')
 for page,text in results:
  pages[page-1]['text']=text;pages[page-1]['extraction']='vision-transcribed visible map half; original native extraction had off-page text from shared map artwork'
 write_json(PRIVATE/'bonus_pages.json',pages)
 print('Vision extracted both map halves; manual AI comparison with original still required.')
