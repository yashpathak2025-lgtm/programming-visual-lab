import os, sys, time, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['PVL_EXECUTION_MODE']='local'
from app.executor import execute


def assert_error(code, language='python', contains='ValidationError'):
    r=execute(code, language, 2000)
    assert not r['ok'], r
    assert contains in r.get('error',''), r

# Python dangerous operations are blocked before execution.
for code in [
    "open('/tmp/pvl_escape','w').write('x')",
    "eval('1+1')",
    "exec('x=1')",
    "__import__('os')",
    "print((1).__class__.__mro__)",
]:
    assert_error(code)

# Imports are disabled; this also prevents direct socket/subprocess access.
assert_error("import socket\ns=socket.socket()")

# Code timeout is enforced by the local development runner.
r=execute("while True:\n    pass", 'python', 300)
assert not r['ok'] and 'Timeout' in r.get('error',''), r

# Java escape-oriented APIs are rejected before compilation.
for code in [
    'public class Main { public static void main(String[] a) { Runtime.getRuntime(); } }',
    'public class Main { public static void main(String[] a) { new java.io.File("x"); } }',
    'public class Main { public static void main(String[] a) { System.exit(0); } }',
]:
    assert_error(code, 'java')

# Java normal execution works when javac is available.
if shutil.which('javac'):
 r=execute('public class Main { public static void main(String[] a) { int x=2; x+=3; System.out.println(x); } }','java',5000)
 assert r['ok'] and r['stdout'].strip()=='5' and r['events'], r
else:
 print('JAVA SECURITY TEST NOT RUN: javac unavailable')

print('SECURITY PASS: local validator restrictions, timeout, Java API blocks, Java normal execution checked when javac is available')
