import hashlib
import json
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DAY6 = Path(os.environ.get('DAY6_ROOT', str(ROOT.parent / 'K5-L3-Day06-NguyenThiThanhBinh-MSSV-DataIngestionEngineering')))
PRIVATE = ROOT / 'data/private'

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def now():
    return datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()
