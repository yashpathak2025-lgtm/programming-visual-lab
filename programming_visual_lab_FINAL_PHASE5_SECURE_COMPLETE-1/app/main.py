from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from .executor import execute
import json, os

BASE=Path(__file__).resolve().parent
app=FastAPI(title='Programming Visual Lab',version='4.0.0',description='Execution-first programming and DSA visual laboratory')
ALLOWED_ORIGINS=[x.strip() for x in os.environ.get('PVL_ALLOWED_ORIGINS','http://127.0.0.1:8000,http://localhost:8000').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

class RunRequest(BaseModel):
    code:str=Field(min_length=1,max_length=24000)
    language:str=Field(default='python',pattern='^(python|java)$')
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
    # Local, deterministic assistant for Phase 3 foundation.
    # Provider-backed AI can be plugged in later without exposing API keys to the browser.
    code=req.code.strip()
    lang=req.language
    if req.action=='explain':
        return {'ok':True,'title':'Code Explanation','answer':f'This {lang} program contains {len(code.splitlines()) if code else 0} lines. Use the execution timeline to inspect each event and variable change.'}
    if req.action=='debug':
        return {'ok':True,'title':'Debug Analysis','answer':('No runtime error supplied. Run the program first and send the actual error here.' if not req.error else f'Runtime error received: {req.error[:2000]}')}
    if req.action=='fix':
        return {'ok':True,'title':'Fix Suggestion','answer':('Paste code and the actual error to generate a targeted fix.' if not req.error else 'A provider-backed AI can now be connected here to return a safe, targeted patch using this code and runtime error.')}
    if req.action=='optimize':
        return {'ok':True,'title':'Optimization','answer':'Optimization should preserve behavior first; inspect the execution timeline, then reduce unnecessary loops, repeated work, or memory usage.'}
    if req.action=='tests':
        return {'ok':True,'title':'Test Cases','answer':'Add normal, boundary, empty-input, and invalid-input cases. The next AI provider layer will generate executable tests from the submitted code.'}
    if req.action=='hint':
        return {'ok':True,'title':'DSA Hint','answer':('Think about the data structure and invariant that must remain true after each step.' if not req.prompt else f'Hint for: {req.prompt[:1000]}')}
    if req.action=='generate':
        return {'ok':True,'title':'Code Generation','answer':f'Generation request received for {lang}. Connect an AI provider on the server to produce code without exposing credentials in the frontend.'}
    return {'ok':False,'error':'Unsupported AI action'}
