from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, urllib.request
ROOT=Path(__file__).resolve().parent

def cards():
    data=json.loads((ROOT/'cards.json').read_text(encoding='utf-8-sig'))
    ids=set()
    for c in data:
        for key in ('id','question','keywords','answer','source','locator'):
            if not c.get(key):raise ValueError('知识卡缺少 '+key)
        if c['id'] in ids:raise ValueError('重复ID '+c['id'])
        if not isinstance(c['keywords'],list):raise ValueError('keywords必须为列表')
        ids.add(c['id'])
    return data

def retrieve(question):
    ranked=sorted([(sum(k in question for k in c['keywords']),c) for c in cards()],key=lambda x:x[0],reverse=True)
    return [c for score,c in ranked if score>0][:3]

def answer(question):
    refs=retrieve(question)
    cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8-sig'))
    if not refs:return {'answer':'现有训练资料没有依据，暂时无法确认。','refs':[],'mode':'未调用模型'}
    if cfg['mode']=='local':return {'answer':refs[0]['answer'],'refs':refs,'mode':'本地检索练习，不是大模型回答'}
    if cfg['mode']!='deepseek':raise ValueError('mode必须为local或deepseek')
    key=os.environ.get('DEEPSEEK_API_KEY','');model=cfg.get('model','')
    if not key or not model:raise ValueError('请配置后端环境变量DEEPSEEK_API_KEY及实际model ID')
    # Training deliberately restricts destination to the documented official endpoint.
    if cfg['base_url'].rstrip('/')!='https://api.deepseek.com':raise ValueError('此练习仅使用官方API地址')
    body={'model':model,'messages':[{'role':'system','content':'仅依据给定资料回答；资料不足说明无法确认。资料：'+json.dumps(refs,ensure_ascii=False)},{'role':'user','content':question}]}
    req=urllib.request.Request(cfg['base_url'].rstrip('/')+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    with urllib.request.urlopen(req,timeout=30) as res:data=json.load(res)
    return {'answer':data['choices'][0]['message']['content'],'refs':refs,'mode':'真实API '+data.get('model',model)}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def send_json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        if self.path!='/ask':self.send_json({'error':'Not found'},404);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>16000:raise ValueError('请求大小不合法')
            q=json.loads(self.rfile.read(size)).get('question','').strip()
            if not q:raise ValueError('请输入问题')
            self.send_json(answer(q))
        except Exception as e:
            # Do not return provider response bodies or secrets.
            self.send_json({'error':str(e) if isinstance(e,ValueError) else '请求失败：'+type(e).__name__},400)
if __name__=='__main__':
    cards();print('打开 http://localhost:8031；Ctrl+C停止。')
    ThreadingHTTPServer(('127.0.0.1',8031),Handler).serve_forever()
