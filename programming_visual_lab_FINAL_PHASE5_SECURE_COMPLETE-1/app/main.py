from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from .executor import execute
import json, os, urllib.request, urllib.error

BASE=Path(__file__).resolve().parent
app=FastAPI(title='Programming Visual Lab',version='4.0.0',description='Execution-first programming and DSA visual laboratory')
ALLOWED_ORIGINS=[x.strip() for x in os.environ.get('PVL_ALLOWED_ORIGINS','http://127.0.0.1:8000,http://localhost:8000').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

class RunRequest(BaseModel):
    code:str=Field(min_length=1,max_length=24000)
    language:str=Field(default='python',pattern='^(python|java|c|cpp|javascript)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java','c','cpp','javascript'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint)
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java|c|cpp|javascript)
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java','c','cpp','javascript'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java','c','cpp','javascript'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java','c','cpp','javascript'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}

    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java','c','cpp','javascript'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
)
    timeout_ms:int=Field(default=4000,ge=250,le=10000)
    stdin:str=Field(default='',max_length=8000)

@app.get('/')
def index():
    html=(BASE/'static'/'index.html').read_text(encoding='utf-8')
    html=html.replace('</body>', '<script src="/static/input-bridge.js"></script></body>')
    return HTMLResponse(html)
@app.get('/api/health')
def health(): return {'ok':True,'version':'5.0.0','phases':['1','2','3','4','5'],'languages':['python','java'],'execution_mode':os.environ.get('PVL_EXECUTION_MODE','docker'),'sandbox_image':os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')}
@app.post('/api/run')
def run(req:RunRequest):
    return execute(req.code,req.language,req.timeout_ms,req.stdin)

class AIRequest(BaseModel):
    action:str=Field(pattern='^(generate|explain|debug|fix|optimize|tests|hint))
    code:str=Field(default='',max_length=24000)
    language:str=Field(default='python',pattern='^(python|java))
    error:str=Field(default='',max_length=12000)
    prompt:str=Field(default='',max_length=6000)

@app.post('/api/ai')
def ai(req:AIRequest):
    code=req.code.strip()
    lang=req.language
    api_key=os.environ.get('OPENAI_API_KEY','').strip()
    base=os.environ.get('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.environ.get('OPENAI_MODEL','gpt-5-mini')
    if not api_key:
        return {'ok':False,'configured':False,'error':'AI provider is not configured. Set OPENAI_API_KEY on the server; never put the key in frontend JavaScript.'}
    tasks={
      'generate':'Generate a correct, beginner-friendly program for the user request. Return code first, then a short explanation.',
      'explain':'Explain the supplied code step by step in simple language. Mention important variables, loops and functions.',
      'debug':'Find likely bugs using the supplied code and actual runtime error. Explain the cause and give a corrected version.',
      'fix':'Fix the supplied code using the actual runtime error when available. Return the complete corrected code and a short explanation.',
      'optimize':'Suggest safe performance/readability improvements while preserving behavior. Explain complexity before and after.',
      'tests':'Create useful executable test cases including normal, boundary and edge cases for the supplied code.',
      'hint':'Give a progressive DSA/programming hint without immediately giving away the complete solution.'
    }
    system=("You are the Programming Visual Lab coding assistant. Be accurate and security-conscious. "
            "Do not claim code was executed unless execution output is supplied. Language: "+lang+".")
    user=tasks[req.action]+"\n\nUSER REQUEST:\n"+req.prompt[:6000]+"\n\nCODE:\n"+code[:24000]+"\n\nRUNTIME OUTPUT/ERROR:\n"+req.error[:12000]
    payload=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.2}).encode()
    try:
        request=urllib.request.Request(base+'/chat/completions',data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.loads(response.read().decode('utf-8'))
        answer=data.get('choices',[{}])[0].get('message',{}).get('content','').strip()
        if not answer: return {'ok':False,'configured':True,'error':'AI provider returned an empty response.'}
        return {'ok':True,'configured':True,'title':req.action.title(),'answer':answer,'model':model}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','ignore')[:1000]
        return {'ok':False,'configured':True,'error':f'AI provider HTTP {e.code}: {detail}'}
    except Exception as e:
        return {'ok':False,'configured':True,'error':f'AI provider request failed: {e}'}
