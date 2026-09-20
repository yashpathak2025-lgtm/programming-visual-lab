import sys, os, shutil
os.environ['PVL_EXECUTION_MODE']='local'
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.executor import execute

py='''arr=[5,2,4]\nfor i in range(len(arr)):\n    for j in range(len(arr)-i-1):\n        visualize("compare", {"array":arr,"j":j}, "BUBBLE")\n        if arr[j]>arr[j+1]: arr[j],arr[j+1]=arr[j+1],arr[j]\nprint(arr)'''
r=execute(py,'python',5000)
assert r['ok'] and '[2, 4, 5]' in r['stdout'] and len(r['events'])>5
r=execute('''def f(n):\n    if n<=1:return 1\n    return n*f(n-1)\nprint(f(5))''','python',5000)
assert r['ok'] and r['stdout'].strip()=='120' and any(e['event']=='CALL' for e in r['events'])
if shutil.which('javac'):
 java='''public class Main { public static void main(String[] args) { int x=7; for(int i=0;i<3;i++){ x+=i; System.out.println(x); } } }'''
 r=execute(java,'java',8000)
 assert r['ok'] and '7' in r['stdout'] and len(r['events'])>0
else:
 print('JAVA SMOKE TEST NOT RUN: javac unavailable')
print('SMOKE PASS: python trace and recursion; Java checked when javac is available')
