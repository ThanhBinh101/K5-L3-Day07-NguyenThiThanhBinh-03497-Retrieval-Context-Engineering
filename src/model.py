"""Small OpenAI-compatible client. Secrets never appear in results or errors."""
import json
import os
import shlex
import ssl
import certifi
import urllib.request
import urllib.error
from .common import ROOT


def load_env():
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            line=line.strip().removeprefix('export ')
            if not line or line.startswith('#') or '=' not in line:continue
            k,v=line.split('=',1)
            if k.strip() in {'OPENAI_API_KEY','MODEL','PROVIDER','OPENAI_BASE_URL'}:
                parts=shlex.split(v,comments=True)
                if parts:os.environ.setdefault(k.strip(),parts[0])


class Model:
    def __init__(self):
        load_env()
        self.name=os.environ.get('MODEL','')
        self.key=os.environ.get('OPENAI_API_KEY','')
        self.url=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')+'/chat/completions'
        if not self.key or not self.name:raise RuntimeError('Chưa cấu hình MODEL và OPENAI_API_KEY trong .env.')
    def complete(self,messages,tools,choice='auto'):
        payload={'model':self.name,'messages':messages,'tools':tools,'tool_choice':choice,'max_completion_tokens':3500}
        req=urllib.request.Request(self.url,data=json.dumps(payload).encode(),headers={
            'Content-Type':'application/json','Authorization':'Bearer '+self.key})
        try:
            with urllib.request.urlopen(req,timeout=90,context=ssl.create_default_context(cafile=certifi.where())) as r:data=json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'Model API HTTP {e.code}; kiểm tra model, key hoặc quota.') from None
        except (urllib.error.URLError,TimeoutError):raise RuntimeError('Không kết nối được model API hoặc hết thời gian.') from None
        c=data['choices'][0]
        if c.get('finish_reason')=='length':raise RuntimeError('Model hết giới hạn output; không coi câu trả lời bị cắt là thành công.')
        return c['message'],data.get('usage',{}),data.get('model',self.name)
