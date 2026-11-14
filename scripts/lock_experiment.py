"""Lock semantics and config before the first held-out evaluation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,PRIVATE,write_json,sha,now
p=ROOT/'results/experiment_lock.json'
if p.exists():raise SystemExit('Already locked; refusing overwrite.')
files=[f'src/{n}.py' for n in ['agent','bonus','retrieval','model','common']]+['configs/basic-selected.json','configs/bonus-selected.json','configs/experiments.json','benchmark/frozen.json','data/private/bonus_pages.json','scripts/benchmark.py']
write_json(p,{'locked_at':now(),'policy':'All tuning on dev completed; no test has been run. Any semantic changes after this lock require a fresh independent test set.',
 'files':{str(f):sha(ROOT/f) for f in files},'model':'gpt-5.4-mini-2026-03-17'})
print('Locked final configuration before test')
