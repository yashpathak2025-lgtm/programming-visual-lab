"""End-to-end Docker boundary checks.

This suite is intentionally separate because it requires a working Docker Engine.
It exits 2 when Docker is unavailable so CI can distinguish "not run" from "passed".
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IMAGE=os.environ.get('PVL_SANDBOX_IMAGE','programming-visual-lab-sandbox:test')
if not shutil.which('docker'):
    print('DOCKER SECURITY NOT RUN: docker CLI not installed')
    raise SystemExit(2)
try:
    subprocess.run(['docker','info'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
except Exception as e:
    print(f'DOCKER SECURITY NOT RUN: Docker Engine unavailable: {e}')
    raise SystemExit(2)

subprocess.run(['docker','build','-f','Dockerfile.sandbox','-t',IMAGE,'.'],cwd=ROOT,check=True)

BASE=['docker','run','--rm','-i','--network','none','--read-only',
      '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m','--cap-drop','ALL',
      '--security-opt','no-new-privileges:true','--pids-limit','64','--memory','256m',
      '--memory-swap','256m','--cpus','0.50','--ulimit','nofile=64:64',
      '--ulimit','fsize=3145728:3145728','--ulimit','nproc=64:64','--user','10001:10001',
      IMAGE]

def run(req, timeout=15):
    p=subprocess.run(BASE,input=json.dumps(req),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    assert p.returncode==0, p.stderr
    return json.loads(p.stdout)

r=run({'code':'arr=[3,1,2]\narr.sort()\nprint(arr)','language':'python','timeout_ms':2000})
assert r['ok'] and '[1, 2, 3]' in r['stdout'] and r['events']

r=run({'code':'public class Main { public static void main(String[] a) { int x=4; x*=2; System.out.println(x); } }','language':'java','timeout_ms':3000})
assert r['ok'] and r['stdout'].strip()=='8' and r['events']

RAW=BASE[:-1]+['--entrypoint','python',IMAGE]

# Container has no network. This is a raw container-level check, not the language validator.
p=subprocess.run(RAW+['-c','import socket; s=socket.socket(); s.settimeout(1); s.connect(("1.1.1.1",80))'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert p.returncode != 0, 'network unexpectedly reachable'

# Root filesystem is read-only; /tmp is the intended writable area.
p=subprocess.run(RAW+['-c','open("/pvl_should_fail","w").write("x")'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert p.returncode != 0, 'root filesystem unexpectedly writable'
p=subprocess.run(RAW+['-c','open("/tmp/pvl_ok","w").write("x")'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert p.returncode == 0, p.stderr

# Container identity must be non-root.
p=subprocess.run(RAW+['-c','import os; print(os.getuid())'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert p.stdout.strip()=='10001', p.stdout

# Infinite user code must be stopped by the inner runner + outer deadline.
try:
    p=subprocess.run(BASE,input=json.dumps({'code':'while True:\n    pass','language':'python','timeout_ms':500}),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=6)
except subprocess.TimeoutExpired:
    raise AssertionError('host deadline failed to stop sandbox')
r=json.loads(p.stdout)
assert not r['ok'] and 'Timeout' in r.get('error',''), r

print('DOCKER SECURITY PASS: Python + Java, no network, read-only rootfs, /tmp only, non-root, timeout')
