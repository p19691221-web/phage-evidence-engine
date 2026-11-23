"""Linux local file gateway. Real filesystem effects; no model or external API."""
import argparse
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import stat
import time
import uuid
from pathlib import Path

MAX_BYTES = 65536


def dump(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def initialize(control, root):
    control, root = Path(control).resolve(), Path(root).resolve()
    if control == root or root in control.parents or control in root.parents:
        raise ValueError('control and allowed root must be disjoint directories')
    if control.exists():
        raise ValueError('control directory already exists; refusing to reset credentials')
    root.mkdir(parents=True, exist_ok=True)
    control.mkdir(mode=0o700, parents=True)
    (control/'quarantine').mkdir(mode=0o700)
    tokens = {role: secrets.token_urlsafe(32) for role in ('agent', 'admin')}
    config = {'root': str(root), 'tokens': {k: token_hash(v) for k,v in tokens.items()}}
    for name, data in [('config.json', config)] + [(k+'.credential.json', {'token':v}) for k,v in tokens.items()]:
        fd = os.open(control/name, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd,'w') as f:
            f.write(dump(data))
    c = sqlite3.connect(control/'state.sqlite')
    c.executescript('''
    CREATE TABLE requests(id TEXT PRIMARY KEY, digest TEXT NOT NULL, result TEXT NOT NULL);
    CREATE TABLE approvals(id TEXT PRIMARY KEY, path TEXT NOT NULL, sha256 TEXT NOT NULL,
      dev INTEGER NOT NULL, inode INTEGER NOT NULL, expires INTEGER NOT NULL,
      state TEXT NOT NULL);
    CREATE TABLE audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL,
      role TEXT NOT NULL, operation TEXT NOT NULL, path TEXT NOT NULL,
      outcome TEXT NOT NULL, request_id TEXT NOT NULL);
    ''')
    c.close()
    os.chmod(control/'state.sqlite', 0o600)
    return {'control': str(control), 'root': str(root), 'credentials_created': True}


class Gateway:
    def __init__(self, control, clock=time.time):
        if os.name != 'posix' or not hasattr(os,'O_NOFOLLOW'):
            raise RuntimeError('requires Linux/POSIX descriptor-relative file operations')
        self.control = Path(control).resolve()
        self.config = json.loads((self.control/'config.json').read_text())
        self.clock = clock

    def db(self):
        return sqlite3.connect(self.control/'state.sqlite', timeout=10, isolation_level=None)

    def role(self, token):
        if type(token) is not str:
            raise PermissionError('missing credential')
        candidate = token_hash(token)
        for role, expected in self.config['tokens'].items():
            if hmac.compare_digest(candidate, expected):
                return role
        raise PermissionError('invalid credential')

    def parent(self, path):
        if type(path) is not str or not path or len(path)>500 or '\\' in path or '\0' in path:
            raise PermissionError('invalid relative path')
        parts = path.split('/')
        if any(p in ('', '.', '..') for p in parts):
            raise PermissionError('absolute/traversal paths are denied')
        fd = os.open(self.config['root'], os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                nxt = os.open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = nxt
            return fd, parts[-1]
        except Exception:
            os.close(fd)
            raise

    def snapshot(self, path):
        parent, name = self.parent(path)
        try:
            fd = os.open(name, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK, dir_fd=parent)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_BYTES:
                    raise PermissionError('only regular single-link files up to 64 KiB are supported')
                with os.fdopen(fd, 'rb', closefd=False) as f:
                    data = f.read(MAX_BYTES+1)
                if len(data)>MAX_BYTES:
                    raise PermissionError('file too large')
                return info, data
            finally:
                os.close(fd)
        finally:
            os.close(parent)

    def call(self, token, operation, request_id, path='', content='', approval_id=''):
        role = self.role(token)
        if type(request_id) is not str or not 1<=len(request_id)<=100:
            raise ValueError('request_id required, max 100 characters')
        if operation not in ('read','create','request-delete','approve-delete','quarantine-delete'):
            raise PermissionError('operation not supported')
        if (operation=='approve-delete' and role!='admin') or (operation!='approve-delete' and role!='agent'):
            raise PermissionError('credential role cannot perform this operation')
        if any(type(v) is not str for v in (path,content,approval_id)):
            raise ValueError('request fields must be strings')
        if len(content.encode())>MAX_BYTES or len(approval_id)>100:
            raise ValueError('request exceeds size limit')
        digest = hashlib.sha256(dump([role,operation,path,content,approval_id]).encode()).hexdigest()
        c = self.db()
        try:
            c.execute('BEGIN IMMEDIATE')
            prior = c.execute('SELECT digest,result FROM requests WHERE id=?',(request_id,)).fetchone()
            if prior:
                c.rollback()
                if prior[0]!=digest:
                    return {'status':'DENIED','reason':'REQUEST_ID_CONFLICT'}
                return {**json.loads(prior[1]),'replayed':True}
            # Persist before the filesystem effect. An interrupted action is never automatically repeated.
            c.execute('INSERT INTO requests VALUES (?,?,?)',(request_id,digest,dump({'status':'OUTCOME_UNKNOWN','reason':'interrupted request; inspect filesystem before any new request'})))
            c.commit()
            try:
                result = self.execute(c, operation, path, content, approval_id)
            except (OSError,PermissionError,ValueError,UnicodeError) as error:
                c.rollback()
                result = {'status':'DENIED_OR_FAILED','reason':str(error)}
            c.execute('BEGIN IMMEDIATE')
            c.execute('UPDATE requests SET result=? WHERE id=?',(dump(result),request_id))
            c.execute('INSERT INTO audit(at,role,operation,path,outcome,request_id) VALUES (?,?,?,?,?,?)',
                      (int(self.clock()),role,operation,path,result['status'],request_id))
            c.commit()
            return result
        finally:
            c.close()

    def execute(self,c,operation,path,content,approval_id):
        if operation=='read':
            _,data=self.snapshot(path)
            return {'status':'READ','text':data.decode('utf-8'),'sha256':hashlib.sha256(data).hexdigest()}
        if operation=='create':
            parent,name=self.parent(path)
            try:
                fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
                try:
                    with os.fdopen(fd,'wb',closefd=False) as f:
                        f.write(content.encode());f.flush();os.fsync(f.fileno())
                finally:
                    os.close(fd)
                return {'status':'CREATED','bytes':len(content.encode())}
            finally:
                os.close(parent)
        if operation=='request-delete':
            info,data=self.snapshot(path)
            aid=str(uuid.uuid4());sha=hashlib.sha256(data).hexdigest()
            c.execute('INSERT INTO approvals VALUES (?,?,?,?,?,?,?)',(aid,path,sha,info.st_dev,info.st_ino,int(self.clock())+300,'pending'))
            return {'status':'PENDING_HUMAN_APPROVAL','approval_id':aid,'path':path,'sha256':sha,'expires_in_seconds':300}
        if operation=='approve-delete':
            # The human must explicitly supply the reviewed path AND digest, not just an approval ID.
            with c:
                c.execute('BEGIN IMMEDIATE')
                r=c.execute('SELECT path,sha256,expires,state FROM approvals WHERE id=?',(approval_id,)).fetchone()
                if not r or r[2]<=int(self.clock()) or r[3]!='pending' or r[0]!=path or r[1]!=content:
                    c.rollback();return {'status':'DENIED','reason':'approval missing, expired, used or review binding mismatch'}
                c.execute("UPDATE approvals SET state='approved' WHERE id=?",(approval_id,));c.commit()
            return {'status':'APPROVED_FOR_QUARANTINE','approval_id':approval_id}
        c.execute('BEGIN IMMEDIATE')
        r=c.execute('SELECT path,sha256,dev,inode,expires,state FROM approvals WHERE id=?',(approval_id,)).fetchone()
        if not r or r[0]!=path or r[4]<=int(self.clock()) or r[5]!='approved':
            c.rollback();return {'status':'DENIED','reason':'missing, expired, consumed or mismatched human approval'}
        info,data=self.snapshot(path)
        if (info.st_dev,info.st_ino,hashlib.sha256(data).hexdigest())!=(r[2],r[3],r[1]):
            c.execute("UPDATE approvals SET state='invalidated' WHERE id=?",(approval_id,));c.commit()
            return {'status':'DENIED','reason':'file changed since human review'}
        c.execute("UPDATE approvals SET state='consumed' WHERE id=?",(approval_id,));c.commit()
        parent,name=self.parent(path)
        qfd=os.open(self.control/'quarantine',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        destination=approval_id+'.quarantined'
        try:
            os.rename(name,destination,src_dir_fd=parent,dst_dir_fd=qfd)
            moved=os.stat(destination,dir_fd=qfd,follow_symlinks=False)
            if (moved.st_dev,moved.st_ino)!=(info.st_dev,info.st_ino):
                return {'status':'OUTCOME_UNKNOWN','reason':'file changed during move; preserved in quarantine; manual inspection required','quarantine_name':destination}
            fd=os.open(destination,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=qfd)
            try:
                with os.fdopen(fd,'rb',closefd=False) as f:
                    after=f.read(MAX_BYTES+1)
                if hashlib.sha256(after).hexdigest()!=r[1]:
                    return {'status':'OUTCOME_UNKNOWN','reason':'content changed during move; preserved for manual inspection','quarantine_name':destination}
            finally:
                os.close(fd)
            return {'status':'QUARANTINED','quarantine_name':destination,'permanently_deleted':False}
        finally:
            os.close(parent);os.close(qfd)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control',required=True)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('init').add_argument('--root',required=True)
    c=sub.add_parser('call');c.add_argument('--credential',required=True);c.add_argument('--request',required=True)
    args=p.parse_args()
    try:
        if args.command=='init':result=initialize(args.control,args.root)
        else:
            if Path(args.request).stat().st_size>100000:raise ValueError('request file too large')
            request=json.loads(Path(args.request).read_text())
            token=json.loads(Path(args.credential).read_text())['token']
            result=Gateway(args.control).call(token,**request)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,PermissionError,OSError,sqlite3.Error) as error:
        print(json.dumps({'status':'ERROR_NO_PERMISSION_GRANTED','reason':str(error)},ensure_ascii=False));raise SystemExit(2)


if __name__=='__main__':main()
