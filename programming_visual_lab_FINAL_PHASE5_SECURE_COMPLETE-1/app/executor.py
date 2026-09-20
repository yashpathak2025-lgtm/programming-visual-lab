"""Safe-ish local execution and event tracing for Programming Visual Lab.

This is an educational sandbox, not a production multi-tenant sandbox. It disables
imports and dangerous Python builtins and applies process limits where supported.
Java execution is compiled in a temporary directory and run with conservative JVM
memory/stack/time limits. Both runners emit events from code that actually executes.
"""
import ast, builtins, contextlib, io, json, os, re, resource, shutil, subprocess, sys, tempfile, textwrap, traceback
from pathlib import Path

MAX_EVENTS = 3500
MAX_OUTPUT = 16000
MAX_CODE = 24000
BLOCKED = {
    '__import__','open','exec','eval','compile','breakpoint','globals','locals','vars','dir','help','quit','exit',
    'memoryview','getattr','setattr','delattr'
}

PY_RUNNER = r'''import ast,builtins,io,json,sys,traceback,contextlib
SOURCE=__SOURCE__; MAX_EVENTS=__MAX_EVENTS__; MAX_OUTPUT=__MAX_OUTPUT__; events=[]; out=io.StringIO()
BLOCKED=__BLOCKED__; SAFE={k:v for k,v in builtins.__dict__.items() if k not in BLOCKED}; SAFE['__build_class__']=builtins.__build_class__
def clean(v,depth=0):
 if depth>5:return '<object>'
 if isinstance(v,(str,int,float,bool,type(None))):return v
 if isinstance(v,(list,tuple,set)):return [clean(x,depth+1) for x in list(v)[:200]]
 if isinstance(v,dict):return {str(k):clean(x,depth+1) for k,x in list(v.items())[:200]}
 return repr(v)[:500]
def snap(frame): return {k:clean(v) for k,v in frame.f_locals.items() if not k.startswith('__')}
def emit(event,line,details=None,frame=None):
 if len(events)<MAX_EVENTS: events.append({'line':int(line or 1),'event':event,'variables':snap(frame) if frame else {},'details':details or {}})
def visualize(label,data=None,kind='CUSTOM'):
 f=sys._getframe(1)
 d={'label':str(label),'data':clean(data),'kind':str(kind)}
 # Preserve common DSA pointer metadata when the caller passes a dict.
 if isinstance(data,dict):
  for k in ('i','j','k','mid','lo','hi','top','front','rear','index','next','min','left','right'):
   if k in data: d[k]=clean(data[k])
 emit('VISUAL',f.f_lineno,d,f)

def pvl_dsa_snapshot(frame):
 d={}
 for k,v in frame.f_locals.items():
  if k in ('i','j','k','mid','lo','hi','top','front','rear','index','next','min','left','right') and isinstance(v,(int,float)):
   d[k]=v
 for name,val in frame.f_locals.items():
  if isinstance(val,list) and len(val)<=100 and all(isinstance(x,(int,float,str,bool,type(None))) for x in val):
   d.setdefault('array',clean(val)); d.setdefault('array_name',name); break
 return d

def pvl_trace_compare(line,left_src,right_src,op,result):
 f=sys._getframe(1)
 try:left=eval(left_src,{'__builtins__':SAFE,'visualize':visualize},f.f_locals)
 except:left=left_src
 try:right=eval(right_src,{'__builtins__':SAFE,'visualize':visualize},f.f_locals)
 except:right=right_src
 emit('COMPARE',line,{'left':clean(left),'right':clean(right),'operator':op,'result':bool(result),'left_src':left_src,'right_src':right_src},f); return result
def pvl_emit_stmt(kind,line,details=None):
 f=sys._getframe(1); d=dict(details or {})
 d.update({k:v for k,v in pvl_dsa_snapshot(f).items() if k not in d})
 emit(kind,line,d,f)
def tracer(frame,event,arg):
 if frame.f_code.co_filename!='user_code.py': return tracer
 if event=='call': emit('CALL',frame.f_lineno,{'function':frame.f_code.co_name},frame)
 elif event=='line': emit('LINE',frame.f_lineno,{},frame)
 elif event=='return': emit('RETURN',frame.f_lineno,{'value':clean(arg)},frame)
 return tracer
class Guard(ast.NodeTransformer):
 def visit_Import(self,node): raise ValueError('imports are disabled in the Python sandbox')
 def visit_ImportFrom(self,node): raise ValueError('imports are disabled in the Python sandbox')
 def visit_Attribute(self,node):
  if node.attr.startswith('__'): raise ValueError('dunder attributes are disabled')
  return self.generic_visit(node)
 def visit_Name(self,node):
  if node.id.startswith('__'): raise ValueError('dunder names are disabled')
  return node
 def visit_Call(self,node):
  if isinstance(node.func,ast.Name) and node.func.id in BLOCKED: raise ValueError(f'call to {node.func.id} is disabled')
  return self.generic_visit(node)
 def visit_Compare(self,node):
  node=self.generic_visit(node)
  if len(node.ops)==1 and len(node.comparators)==1:
   op=type(node.ops[0]).__name__; left=ast.unparse(node.left); right=ast.unparse(node.comparators[0])
   c=ast.Call(func=ast.Name(id='pvl_trace_compare',ctx=ast.Load()),args=[ast.Constant(node.lineno),ast.Constant(left),ast.Constant(right),ast.Constant(op),node],keywords=[])
   return ast.copy_location(c,node)
  return node
 def visit_Assign(self,node):
  node=self.generic_visit(node); event='SWAP' if node.targets and isinstance(node.targets[0],ast.Tuple) and len(node.targets[0].elts)==2 else 'ASSIGN'
  details={}
  if event=='SWAP' and isinstance(node.targets[0],ast.Tuple):
   subs=[x for x in node.targets[0].elts if isinstance(x,ast.Subscript)]
   if len(subs)==2:
    details={'label':'swap','left_src':ast.unparse(subs[0]),'right_src':ast.unparse(subs[1])}
  mark=ast.Expr(ast.Call(func=ast.Name(id='pvl_emit_stmt',ctx=ast.Load()),args=[ast.Constant(event),ast.Constant(node.lineno),ast.Constant(details)],keywords=[]))
  return [node,ast.copy_location(mark,node)]
 def visit_AnnAssign(self,node):
  node=self.generic_visit(node); mark=ast.Expr(ast.Call(func=ast.Name(id='pvl_emit_stmt',ctx=ast.Load()),args=[ast.Constant('ASSIGN'),ast.Constant(node.lineno)],keywords=[])); return [node,ast.copy_location(mark,node)]
 def visit_AugAssign(self,node):
  node=self.generic_visit(node); mark=ast.Expr(ast.Call(func=ast.Name(id='pvl_emit_stmt',ctx=ast.Load()),args=[ast.Constant('ASSIGN'),ast.Constant(node.lineno)],keywords=[])); return [node,ast.copy_location(mark,node)]
try:
 tree=Guard().visit(ast.parse(SOURCE,'user_code.py')); ast.fix_missing_locations(tree); code=compile(tree,'user_code.py','exec')
 env={'__builtins__':SAFE,'pvl_emit_stmt':pvl_emit_stmt,'pvl_trace_compare':pvl_trace_compare,'visualize':visualize}
 sys.settrace(tracer)
 with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out): exec(code,env,env)
 sys.settrace(None); print(json.dumps({'ok':True,'events':events,'stdout':out.getvalue()[:MAX_OUTPUT]}))
except BaseException as e:
 sys.settrace(None); print(json.dumps({'ok':False,'events':events,'stdout':out.getvalue()[:MAX_OUTPUT],'error':type(e).__name__+': '+str(e),'traceback':traceback.format_exc(limit=12)}))
'''

JAVA_SUPPORT = r'''final class VisualLab {
  static final java.util.ArrayList<String> events = new java.util.ArrayList<>();
  static final int MAX = 3500;
  static { Runtime.getRuntime().addShutdownHook(new Thread(() -> finish())); }
  static String clean(Object v){ return String.valueOf(v).replace("\\", "\\\\").replace("\"", "\\\"").replace("\n","\\n"); }
  public static void emit(int line, String event, String details){
    if(events.size()<MAX) events.add("{\"line\":"+line+",\"event\":\""+clean(event)+"\",\"variables\":{},\"details\":\""+clean(details)+"\"}");
  }
  public static void visualize(int line,String label,Object data,String kind){ emit(line,"VISUAL",label+"|"+clean(data)+"|"+kind); }
  public static void finish(){ System.err.println("PVL_EVENTS:["+String.join(",",events)+"]"); }
}'''

def validate_python(code):
    if len(code) > MAX_CODE: raise ValueError(f'code exceeds {MAX_CODE} characters')
    tree=ast.parse(code,'user_code.py')
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)): raise ValueError('imports are disabled in the Python sandbox')
        if isinstance(n,ast.Attribute) and n.attr.startswith('__'): raise ValueError('dunder attributes are disabled')
        if isinstance(n,ast.Name) and n.id.startswith('__'): raise ValueError('dunder names are disabled')
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in BLOCKED: raise ValueError(f'call to {n.func.id} is disabled')

def limits():
    try:
        resource.setrlimit(resource.RLIMIT_CPU,(4,5)); resource.setrlimit(resource.RLIMIT_FSIZE,(3*1024*1024,3*1024*1024)); resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
    except Exception: pass

def execute_python(code,timeout_ms=4000,stdin_text=''):
    try: validate_python(code)
    except Exception as e: return {'ok':False,'language':'python','events':[],'stdout':'','error':'ValidationError: '+str(e),'source_lines':code.splitlines()}
    runner=PY_RUNNER.replace('__SOURCE__',repr(code)).replace('__MAX_EVENTS__',str(MAX_EVENTS)).replace('__MAX_OUTPUT__',str(MAX_OUTPUT)).replace('__BLOCKED__',repr(BLOCKED))
    with tempfile.TemporaryDirectory(prefix='pvl_py_') as td:
        p=Path(td)/'runner.py'; p.write_text(runner,encoding='utf8')
        env={'PYTHONIOENCODING':'utf-8','PATH':os.environ.get('PATH','')}
        try: r=subprocess.run([sys.executable,str(p)],cwd=td,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,input=stdin_text[:8000],timeout=timeout_ms/1000,env=env,preexec_fn=limits if os.name!='nt' else None)
        except subprocess.TimeoutExpired: return {'ok':False,'language':'python','events':[],'stdout':'','error':'Timeout: execution exceeded the limit.','source_lines':code.splitlines()}
        lines=r.stdout.strip().splitlines()
        if not lines:return {'ok':False,'language':'python','events':[],'stdout':r.stderr[-MAX_OUTPUT:],'error':'Runner produced no result.','source_lines':code.splitlines()}
        try: result=json.loads(lines[-1])
        except Exception:return {'ok':False,'language':'python','events':[],'stdout':r.stdout[-MAX_OUTPUT:],'error':'Runner protocol error.','runner_stderr':r.stderr[-3000:],'source_lines':code.splitlines()}
        result.update({'language':'python','source_lines':code.splitlines()}); return result

def _java_instrument(code):
    """Insert real VisualLab events after Java statements outside parentheses."""
    if len(code)>MAX_CODE: raise ValueError(f'code exceeds {MAX_CODE} characters')
    if re.search(r'\b(package|import)\s+',code): raise ValueError('package/import statements are disabled in the Java sandbox')
    if re.search(r'\b(Runtime|ProcessBuilder|System\.exit|Files|File|Socket|ServerSocket|URLClassLoader|Class\.forName)\b',code): raise ValueError('restricted Java API detected')
    lines=code.splitlines(); out=[]
    for i,line in enumerate(lines,1):
        s=line.strip()
        if (not s or s.startswith('//') or s.startswith('/*') or s.startswith('*') or s.startswith('@')
            or ('class ' in s and not s.startswith('public class')) or s.startswith('if ') or s.startswith('if(')
            or s.startswith('for ') or s.startswith('for(') or s.startswith('while ') or s.startswith('while(')
            or ' else ' in (' '+s+' ') or 'break;' in s or 'return ' in s or 'return;' in s
            or re.match(r'^(String|int|long|double|float|boolean|char)\s+[A-Za-z_]\w*\s*;', s)):
            out.append(line); continue
        # Rename the first public class so the generated file is always Main.java.
        line2=re.sub(r'\bpublic\s+class\s+([A-Za-z_][A-Za-z0-9_]*)', 'public class Main', line, count=1)
        buf=[]; par=0; quote=None; escaped=False; inserted=0
        for ch in line2:
            buf.append(ch)
            if quote:
                if escaped: escaped=False
                elif ch=='\\': escaped=True
                elif ch==quote: quote=None
                continue
            if ch in ('"',"'"): quote=ch; continue
            if ch=='(': par+=1
            elif ch==')': par=max(0,par-1)
            elif ch==';' and par==0:
                buf.append(f' VisualLab.emit({i}, "LINE", "executed");')
                inserted+=1
        # If this is a simple statement that did not end with ;, a line event is still useful.
        if inserted==0 and s.endswith('}') and not re.match(r'.*\b(class|if|else|for|while|switch|try|catch|finally|do)\b.*\{?$',s):
            pass
        out.append(''.join(buf))
    src='\n'.join(out)
    return src+'\n\n'+JAVA_SUPPORT

def _parse_java_events(stderr):
    m=re.search(r'PVL_EVENTS:(\[.*\])',stderr,re.S)
    if not m:return []
    try:
        return json.loads(m.group(1))
    except Exception:return []

def execute_java(code,timeout_ms=5000,stdin_text=''):
    try: instrumented=_java_instrument(code)
    except Exception as e:return {'ok':False,'language':'java','events':[],'stdout':'','error':'ValidationError: '+str(e),'source_lines':code.splitlines()}
    with tempfile.TemporaryDirectory(prefix='pvl_java_') as td:
        main=Path(td)/'Main.java'; main.write_text(instrumented,encoding='utf8')
        env={'PATH':os.environ.get('PATH','')}
        try:
            c=subprocess.run(['javac','-encoding','UTF-8','-J-Xmx256m',str(main)],cwd=td,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=max(3,timeout_ms/1000))
        except subprocess.TimeoutExpired:return {'ok':False,'language':'java','events':[],'stdout':'','error':'Java compile timeout','source_lines':code.splitlines()}
        if c.returncode!=0:return {'ok':False,'language':'java','events':[],'stdout':c.stdout,'error':'JavaCompileError: '+c.stderr[-6000:],'source_lines':code.splitlines()}
        try:
            r=subprocess.run(['java','-Xmx128m','-Xss512k','-Djava.awt.headless=true','Main'],cwd=td,input=stdin_text[:8000],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout_ms/1000,env=env)
        except subprocess.TimeoutExpired:return {'ok':False,'language':'java','events':[],'stdout':'','error':'Timeout: Java execution exceeded the limit.','source_lines':code.splitlines()}
        events=_parse_java_events(r.stderr)
        stdout=r.stdout[:MAX_OUTPUT]
        if r.returncode!=0:
            return {'ok':False,'language':'java','events':events,'stdout':stdout,'error':'JavaRuntimeError: '+r.stderr.split('PVL_EVENTS:')[0][-5000:],'source_lines':code.splitlines()}
        return {'ok':True,'language':'java','events':events,'stdout':stdout,'source_lines':code.splitlines()}

\ndef _parse_line_markers(stderr):
    events=[]
    for line in stderr.splitlines():
        m=re.fullmatch(r'PVL_ARRAY_ITEM:(\d+):(\w+):(\d+):(-?\d+)',line.strip())
        if m:
            ln,name,idx,val=int(m.group(1)),m.group(2),int(m.group(3)),int(m.group(4))
            target=next((x for x in reversed(events) if x.get('line')==ln),None)
            if target:
                d=target.setdefault('details',{})
                arr=d.setdefault('array',[])
                while len(arr)<=idx: arr.append(None)
                arr[idx]=val
                d['array_name']=name
            continue
        m=re.fullmatch(r'PVL_EVENT:(\d+):([A-Z_]+):(.*)',line.strip())
        if m and len(events)<MAX_EVENTS:
            ln,kind,detail=int(m.group(1)),m.group(2),m.group(3)
            events.append({'line':ln,'event':kind if kind in ('COMPARE','ASSIGN','LOOP') else 'LINE',
                           'variables':{},'details':{'label':detail[:240],'source':detail[:240]}})
            continue
        m=re.fullmatch(r'PVL_LINE:(\d+)',line.strip())
        if m and len(events)<MAX_EVENTS:
            events.append({'line':int(m.group(1)),'event':'LINE','variables':{},'details':{}})
    return events

def execute_c(code,timeout_ms=5000,stdin_text=''):
    try: src=_instrument_c_family(code,'c')
    except Exception as e:return {'ok':False,'language':'c','events':[],'stdout':'','error':'ValidationError: '+str(e),'source_lines':code.splitlines()}
    with tempfile.TemporaryDirectory(prefix='pvl_c_') as td:
        srcp=Path(td)/'main.c'; binp=Path(td)/'main'
        srcp.write_text(src,encoding='utf8')
        try:
            c=subprocess.run(['gcc','-O0','-std=c11','-fno-stack-protector',str(srcp),'-o',str(binp)],cwd=td,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
        except FileNotFoundError:return {'ok':False,'language':'c','events':[],'stdout':'','error':'CompilerUnavailable: gcc is not installed.','source_lines':code.splitlines()}
        except subprocess.TimeoutExpired:return {'ok':False,'language':'c','events':[],'stdout':'','error':'C compile timeout','source_lines':code.splitlines()}
        if c.returncode!=0:return {'ok':False,'language':'c','events':[],'stdout':c.stdout,'error':'CCompileError: '+c.stderr[-6000:],'source_lines':code.splitlines()}
        try:r=subprocess.run([str(binp)],cwd=td,input=stdin_text[:8000],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout_ms/1000)
        except subprocess.TimeoutExpired:return {'ok':False,'language':'c','events':[],'stdout':'','error':'Timeout: C execution exceeded the limit.','source_lines':code.splitlines()}
        events=_parse_line_markers(r.stderr)
        return {'ok':r.returncode==0,'language':'c','events':events,'stdout':r.stdout[:MAX_OUTPUT],
                'error':('CRuntimeError: '+r.stderr[-5000:] if r.returncode!=0 else ''),'source_lines':code.splitlines()}

def execute_cpp(code,timeout_ms=5000,stdin_text=''):
    try: src=_instrument_c_family(code,'cpp')
    except Exception as e:return {'ok':False,'language':'cpp','events':[],'stdout':'','error':'ValidationError: '+str(e),'source_lines':code.splitlines()}
    with tempfile.TemporaryDirectory(prefix='pvl_cpp_') as td:
        srcp=Path(td)/'main.cpp'; binp=Path(td)/'main'
        srcp.write_text(src,encoding='utf8')
        try:c=subprocess.run(['g++','-O0','-std=c++17',str(srcp),'-o',str(binp)],cwd=td,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
        except FileNotFoundError:return {'ok':False,'language':'cpp','events':[],'stdout':'','error':'CompilerUnavailable: g++ is not installed.','source_lines':code.splitlines()}
        except subprocess.TimeoutExpired:return {'ok':False,'language':'cpp','events':[],'stdout':'','error':'C++ compile timeout','source_lines':code.splitlines()}
        if c.returncode!=0:return {'ok':False,'language':'cpp','events':[],'stdout':c.stdout,'error':'CppCompileError: '+c.stderr[-6000:],'source_lines':code.splitlines()}
        try:r=subprocess.run([str(binp)],cwd=td,input=stdin_text[:8000],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout_ms/1000)
        except subprocess.TimeoutExpired:return {'ok':False,'language':'cpp','events':[],'stdout':'','error':'Timeout: C++ execution exceeded the limit.','source_lines':code.splitlines()}
        events=_parse_line_markers(r.stderr)
        return {'ok':r.returncode==0,'language':'cpp','events':events,'stdout':r.stdout[:MAX_OUTPUT],
                'error':('CppRuntimeError: '+r.stderr[-5000:] if r.returncode!=0 else ''),'source_lines':code.splitlines()}

def _instrument_js(code):
    if len(code)>MAX_CODE: raise ValueError(f'code exceeds {MAX_CODE} characters')
    if re.search(r'\b(require|process\.|child_process|fs\.|net\.|dgram\.|http\.|https\.)',code):
        raise ValueError('restricted Node.js API detected')
    lines=code.splitlines()
    out=[]
    for i,line in enumerate(lines,1):
        out.append(f'console.error("PVL_LINE:{i}"); {line}')
    return '\n'.join(out)

def execute_javascript(code,timeout_ms=5000,stdin_text=''):
    try:src=_instrument_js(code)
    except Exception as e:return {'ok':False,'language':'javascript','events':[],'stdout':'','error':'ValidationError: '+str(e),'source_lines':code.splitlines()}
    with tempfile.TemporaryDirectory(prefix='pvl_js_') as td:
        srcp=Path(td)/'main.js';srcp.write_text(src,encoding='utf8')
        try:r=subprocess.run(['node','--no-addons','--max-old-space-size=128',str(srcp)],cwd=td,input=stdin_text[:8000],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout_ms/1000)
        except FileNotFoundError:return {'ok':False,'language':'javascript','events':[],'stdout':'','error':'RuntimeUnavailable: Node.js is not installed.','source_lines':code.splitlines()}
        except subprocess.TimeoutExpired:return {'ok':False,'language':'javascript','events':[],'stdout':'','error':'Timeout: JavaScript execution exceeded the limit.','source_lines':code.splitlines()}
        events=_parse_line_markers(r.stderr)
        runtime_err='\n'.join(x for x in r.stderr.splitlines() if not x.startswith('PVL_LINE:'))
        return {'ok':r.returncode==0,'language':'javascript','events':events,'stdout':r.stdout[:MAX_OUTPUT],
                'error':('JavaScriptRuntimeError: '+runtime_err[-5000:] if r.returncode!=0 else ''),'source_lines':code.splitlines()}

def execute_local(code,language='python',timeout_ms=4000,stdin_text=''):
    """Execute inside the sandbox container. C/C++/JS use compiler/runtime binaries installed in the image."""
    language=language.lower().strip()
    if language=='python': return execute_python(code,timeout_ms,stdin_text)
    if language=='java': return execute_java(code,timeout_ms,stdin_text)
    if language=='c': return execute_c(code,timeout_ms,stdin_text)
    if language in ('cpp','c++'): return execute_cpp(code,timeout_ms,stdin_text)
    if language in ('javascript','js'): return execute_javascript(code,timeout_ms,stdin_text)
    return {'ok':False,'language':language,'events':[],'stdout':'','error':'Unsupported language','source_lines':code.splitlines()}

def _docker_execute(code, language, timeout_ms, stdin_text=''):
    """Fail-closed Docker execution manager for untrusted code.

    The host never executes user code when Docker mode is active. Code is sent over
    stdin to an ephemeral, network-disabled, non-root container with read-only rootfs,
    dropped capabilities, cgroup CPU/memory/PID limits and a small tmpfs.
    """
    image=os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:latest')
    docker=os.environ.get('PVL_DOCKER_BIN','docker')
    if not shutil.which(docker):
        return {'ok':False,'language':language,'events':[],'stdout':'','error':'SandboxUnavailable: Docker is required in secure mode. Start Docker Desktop/Engine and build the sandbox image, or explicitly use PVL_EXECUTION_MODE=local for trusted local development.','source_lines':code.splitlines()}
    request=json.dumps({'code':code,'language':language,'timeout_ms':timeout_ms,'stdin':stdin_text[:8000]},ensure_ascii=False)
    # All hardening flags are intentionally explicit here. No host filesystem or
    # Docker socket is mounted into the container.
    cmd=[docker,'run','--rm','-i',
         '--network','none',
         '--read-only',
         '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m',
         '--cap-drop','ALL',
         '--security-opt','no-new-privileges:true',
         '--pids-limit','64',
         '--memory','256m',
         '--memory-swap','256m',
         '--cpus','0.50',
         '--ulimit','nofile=64:64',
         '--ulimit','fsize=3145728:3145728',
         '--ulimit','nproc=64:64',
         '--user','10001:10001',
         image,'python','-m','app.sandbox_runner']
    try:
        r=subprocess.run(cmd,input=request,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         timeout=max(2,timeout_ms/1000+3))
    except subprocess.TimeoutExpired:
        return {'ok':False,'language':language,'events':[],'stdout':'','error':'SandboxTimeout: container did not finish within the host deadline.','source_lines':code.splitlines()}
    except OSError as e:
        return {'ok':False,'language':language,'events':[],'stdout':'','error':f'SandboxLaunchError: {e}','source_lines':code.splitlines()}
    out=r.stdout.strip()
    if not out:
        detail=r.stderr[-4000:].strip()
        return {'ok':False,'language':language,'events':[],'stdout':'','error':'SandboxProtocolError: container returned no result.' + (f' {detail}' if detail else ''),'source_lines':code.splitlines()}
    try:
        result=json.loads(out)
    except json.JSONDecodeError:
        return {'ok':False,'language':language,'events':[],'stdout':'','error':'SandboxProtocolError: invalid JSON from sandbox.','runner_stderr':r.stderr[-4000:],'source_lines':code.splitlines()}
    result.setdefault('language',language); result.setdefault('source_lines',code.splitlines())
    if r.returncode != 0 and result.get('ok'):
        result['ok']=False
        result['error']=f'SandboxProcessError: container exited with code {r.returncode}'
    return result


def execute(code,language='python',timeout_ms=4000,stdin_text=''):
    mode=os.environ.get('PVL_EXECUTION_MODE','docker').lower().strip()
    if os.environ.get('PVL_IN_SANDBOX')=='1' or mode=='local':
        return execute_local(code,language,timeout_ms,stdin_text)
    if mode=='docker':
        return _docker_execute(code,language,timeout_ms,stdin_text)
    return {'ok':False,'language':language,'events':[],'stdout':'','error':f'Invalid PVL_EXECUTION_MODE: {mode}. Use docker or local.','source_lines':code.splitlines()}
