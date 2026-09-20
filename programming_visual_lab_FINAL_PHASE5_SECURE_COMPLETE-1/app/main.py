from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
def run(req:RunRequest): return execute(req.code,req.language,req.timeout_ms,req.stdin)
