"""Compare every Kanji benchmark evidence field to full original native PDF text."""
import sys,logging,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pypdf import PdfReader
from src.common import PRIVATE,ROOT,read_json,write_json
logging.getLogger('pypdf').setLevel(logging.ERROR)
r=PdfReader(PRIVATE/'source.pdf');rows=[]
for q in read_json(ROOT/'benchmark/private/basic.json'):
 if not q['answerable']:continue
 for e in q['evidence']:
  text=r.pages[e['page']-1].extract_text()
  quote=e['quote'];parts=[p.strip() for p in quote.split('|')]
  check=all(re.sub(r'\s+','',p) in re.sub(r'\s+','',text) for p in parts)
  expected_check=all(re.sub(r'\s+','',part.strip()) in re.sub(r'\s+','',text) for part in q['expected'].split('|'))
  check=check and expected_check
  rows.append({'id':q['id'],'page':e['page'],'quote_in_original_native_text':check,'method':'full original PDF page text, not copied chunk','original_text':text})
write_json(ROOT/'results/private/basic_original_page_audit.json',rows)
print(len(rows),'source evidence checks; failed',[r['id'] for r in rows if not r['quote_in_original_native_text']])
