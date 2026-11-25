"""Root-only, disposable Linux integration environment. Does not create OS accounts."""
import argparse
import json
import os
from pathlib import Path
import pwd
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from client import call

GATEWAY_UID,AGENT_UID,GROUP=62001,62002,62002
HERE=Path(__file__).resolve().parent

def identity(uid):
    def drop():
        os.setgroups([]);os.setgid(GROUP);os.setuid(uid)
    return drop

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    if os.geteuid()!=0:
        raise SystemExit('Requires sudo/root for real UID isolation. No isolation test has run.')
    for uid in (GATEWAY_UID,AGENT_UID):
        try:pwd.getpwuid(uid)
        except KeyError:pass
        else:raise SystemExit('Reserved test UID already exists; refusing to use it.')
    for proc in Path('/proc').glob('[0-9]*/status'):
        try:
            uidline=next(x for x in proc.read_text().splitlines() if x.startswith('Uid:'))
            if set(map(int,uidline.split()[1:])) & {GATEWAY_UID,AGENT_UID}:
                raise SystemExit('Reserved UID already has a process; refusing shared identity.')
        except (OSError,StopIteration):pass
    with tempfile.TemporaryDirectory(prefix='phage-isolated-',dir='/tmp') as tmp:
        base=Path(tmp);os.chmod(base,0o755)
        code=base/'code';code.mkdir(mode=0o755);os.chmod(code,0o755)
        for directory in ('file_gateway','isolated_gateway'):
            shutil.copytree(HERE.parent/directory,code/directory,ignore=shutil.ignore_patterns('__pycache__'))
        for path in code.rglob('*'):os.chmod(path,0o755 if path.is_dir() else 0o644)
        control=base/'control';root=base/'files';ipc=base/'ipc';ipc.mkdir(mode=0o750);os.chmod(ipc,0o750);os.chown(ipc,GATEWAY_UID,GROUP)
        sys.path.insert(0,str(code/'file_gateway'))
        from gateway import initialize
        initialize(control,root)
        for top in (control,root):
            os.chown(top,GATEWAY_UID,GROUP);os.chmod(top,0o700)
            for path in top.rglob('*'):os.chown(path,GATEWAY_UID,GROUP)
        address=str(ipc/'gateway.sock')
        proc=subprocess.Popen([sys.executable,'-B',str(code/'isolated_gateway/server.py'),'--control',str(control),'--socket',address,'--agent-uid',str(AGENT_UID),'--admin-uid','0'],preexec_fn=identity(GATEWAY_UID))
        def agent(request):
            result=subprocess.run([sys.executable,'-B',str(code/'isolated_gateway/client.py'),'--socket',address],input=json.dumps(request),text=True,capture_output=True,preexec_fn=identity(AGENT_UID),timeout=20)
            if result.returncode:raise RuntimeError(result.stderr)
            return json.loads(result.stdout)
        def expect(result,status):
            if result.get('status')!=status:raise AssertionError(result)
            print(json.dumps({'check':status,'result':result},ensure_ascii=False))
        try:
            for _ in range(100):
                if Path(address).exists():break
                if proc.poll() is not None:raise RuntimeError('gateway failed to start')
                time.sleep(.05)
            else:raise RuntimeError('gateway startup timeout')
            import stat
            for item in (Path('/tmp'), base, ipc, Path(address)):
                st = item.stat()
                print('PERMISSION:', item, stat.filemode(st.st_mode),
                      'uid=', st.st_uid, 'gid=', st.st_gid, flush=True)
            expect(agent({'operation':'create','request_id':'create','path':'sample.txt','content':'protected sample'}),'CREATED')
            expect(agent({'operation':'read','request_id':'read','path':'sample.txt'}),'READ')
            # Actual child processes attempt direct access with the unprivileged agent UID.
            checks=[('direct-read',root/'sample.txt','read'),('direct-write',root/'bypass.txt','write'),('admin-secret',control/'admin.credential.json','read'),('audit-tamper',control/'state.sqlite','write'),('code-tamper',code/'isolated_gateway/server.py','write')]
            probe="import pathlib,sys\np=pathlib.Path(sys.argv[1])\ntry:\n p.read_bytes() if sys.argv[2]=='read' else p.write_bytes(b'bypass')\nexcept PermissionError:\n print('OS_PERMISSION_DENIED');sys.exit(0)\nraise SystemExit('BYPASS SUCCEEDED')"
            for name,path,mode in checks:
                r=subprocess.run([sys.executable,'-c',probe,str(path),mode],capture_output=True,text=True,preexec_fn=identity(AGENT_UID),timeout=5)
                if r.returncode or 'OS_PERMISSION_DENIED' not in r.stdout:raise AssertionError((name,r.stdout,r.stderr))
                print(name+': OS_PERMISSION_DENIED')
            expect(agent({'operation':'quarantine-delete','request_id':'unapproved','path':'sample.txt'}),'DENIED')
            rejected=agent({'operation':'approve-delete','request_id':'forged','path':'sample.txt'})
            expect(rejected,'DENIED_OR_FAILED')
            pending=agent({'operation':'request-delete','request_id':'request','path':'sample.txt'})
            expect(pending,'PENDING_HUMAN_APPROVAL')
            if args.self_test:
                print('SELF-TEST: approval is scripted, not human review.')
            else:
                print('Review the file and SHA above. Type APPROVE to allow quarantine, anything else exits.')
                if input().strip()!='APPROVE':print('Not approved; no quarantine action.');return
            expect(call(address,{'operation':'approve-delete','request_id':'human-approval','path':pending['path'],'content':pending['sha256'],'approval_id':pending['approval_id']}),'APPROVED_FOR_QUARANTINE')
            req={'operation':'quarantine-delete','request_id':'move','path':'sample.txt','approval_id':pending['approval_id']}
            moved=agent(req);expect(moved,'QUARANTINED')
            assert not (root/'sample.txt').exists()
            assert (control/'quarantine'/moved['quarantine_name']).read_text()=='protected sample'
            assert agent(req).get('replayed') is True
            expect(agent({**req,'request_id':'second-move'}),'DENIED')
            print('PASS: real UID separation and filesystem effects verified. Temporary environment will be removed.')
        finally:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()

if __name__=='__main__':main()
