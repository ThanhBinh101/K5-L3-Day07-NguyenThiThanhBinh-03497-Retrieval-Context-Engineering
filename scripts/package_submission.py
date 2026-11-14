"""Build separate local source and evidence bundles; no secrets, PDFs, vectors or models."""
import sys,zipfile,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,PRIVATE,read_json,write_json,sha,now
from src.model import load_env
import os

def main():
 out=ROOT/'output';out.mkdir(exist_ok=True)
 source=[]
 for p in ROOT.rglob('*'):
  if not p.is_file():continue
  r=p.relative_to(ROOT);parts=r.parts
  if any(x in {'.git','.venv','.local','__pycache__','node_modules','output'} for x in parts):continue
  if any(str(r).startswith(x) for x in ['data/private/','results/private/','benchmark/private/']):continue
  if p.name.startswith('.env') and p.name!='.env.example':continue
  if p.suffix in {'.pyc','.pdf','.sqlite'} or p.name in {'.DS_Store','server.log'}:continue
  source.append(p)
 evidence=[]
 for folder in ['benchmark/private','results/private']:
  evidence += [p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix not in {'.pyc','.pdf','.sqlite'}]
 # Include exact text extraction snapshots required to reproduce hashes; no original PDF or model.
 evidence += [PRIVATE/name for name in ['entries.jsonl','chunks_B.jsonl','pages.jsonl','bonus_pages.json','inventory.json','manifest.json']]
 load_env();secret=os.getenv('OPENAI_API_KEY','').encode()
 if not secret:raise RuntimeError('Secret scan requires configured key, never prints it.')
 bundles=[]
 for name,files in [('Day07-Code.zip',source),('Day07-Evidence-PRIVATE.zip',evidence)]:
  unique=sorted(set(files));manifest={str(p.relative_to(ROOT)):sha(p) for p in unique}
  for p in unique:
   if secret in p.read_bytes():raise RuntimeError('Secret scan found configured key; packaging stopped.')
  target=out/name
  with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
   for p in unique:z.write(p,str(p.relative_to(ROOT)))
   z.writestr('BUNDLE_MANIFEST.json',json.dumps({'created_at':now(),'files':manifest,'configured_key_scan':'passed'},ensure_ascii=False,indent=2))
  bundles.append({'name':name,'files':len(unique),'bytes':target.stat().st_size,'sha256':sha(target),'configured_key_scan':'passed'})
 write_json(out/'manifest.json',{'created_at':now(),'bundles':bundles})
 print([(x['name'],x['files'],round(x['bytes']/1024/1024,2)) for x in bundles])

if __name__=='__main__':main()
