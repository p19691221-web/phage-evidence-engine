import json
import os
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from gateway import Gateway, initialize


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.base=Path(self.t.name);self.root=self.base/'allowed';self.control=self.base/'control'
        initialize(self.control,self.root)
        self.agent=json.loads((self.control/'agent.credential.json').read_text())['token']
        self.admin=json.loads((self.control/'admin.credential.json').read_text())['token']
        self.g=Gateway(self.control,clock=lambda:100)

    def call(self,op,rid='r',**kw):
        return self.g.call(self.agent,op,rid,**kw)

    def create(self):
        self.assertEqual(self.call('create','create',path='note.txt',content='original')['status'],'CREATED')

    def approve(self):
        r=self.call('request-delete','request',path='note.txt')
        a=self.g.call(self.admin,'approve-delete','approve',path=r['path'],content=r['sha256'],approval_id=r['approval_id'])
        self.assertEqual(a['status'],'APPROVED_FOR_QUARANTINE')
        return r['approval_id']

    def test_real_write_and_read(self):
        self.create();self.assertEqual((self.root/'note.txt').read_text(),'original')
        self.assertEqual(self.call('read',path='note.txt')['text'],'original')

    def test_authentication_and_role(self):
        with self.assertRaises(PermissionError):self.g.call('invalid','read','bad',path='note.txt')
        with self.assertRaises(PermissionError):self.call('approve-delete')
        with self.assertRaises(PermissionError):self.g.call(self.admin,'create','bad',path='note.txt')

    def test_traversal_and_absolute(self):
        for n,path in enumerate(['../outside.txt','/etc/passwd','a/../x','a//b','./x','a\\b']):
            self.assertEqual(self.call('create',str(n),path=path,content='bad')['status'],'DENIED_OR_FAILED')
        self.assertFalse((self.base/'outside.txt').exists())

    def test_symlink(self):
        outside=self.base/'outside';outside.write_text('secret')
        (self.root/'link').symlink_to(outside)
        self.assertEqual(self.call('read',path='link')['status'],'DENIED_OR_FAILED')
        (self.root/'dir').symlink_to(self.base,target_is_directory=True)
        self.assertEqual(self.call('create','other',path='dir/out',content='bad')['status'],'DENIED_OR_FAILED')
        self.assertFalse((self.base/'out').exists())

    def test_hardlink(self):
        outside=self.base/'outside';outside.write_text('secret');os.link(outside,self.root/'link')
        self.assertEqual(self.call('read',path='link')['status'],'DENIED_OR_FAILED')

    def test_create_never_overwrites(self):
        self.create()
        self.assertEqual(self.call('create','second',path='note.txt',content='bad')['status'],'DENIED_OR_FAILED')
        self.assertEqual((self.root/'note.txt').read_text(),'original')

    def test_delete_requires_approval(self):
        self.create()
        self.assertEqual(self.call('quarantine-delete',path='note.txt',approval_id='missing')['status'],'DENIED')
        self.assertTrue((self.root/'note.txt').exists())

    def test_real_quarantine_and_one_use(self):
        self.create();aid=self.approve()
        result=self.call('quarantine-delete','move',path='note.txt',approval_id=aid)
        self.assertEqual(result['status'],'QUARANTINED');self.assertFalse((self.root/'note.txt').exists())
        self.assertEqual((self.control/'quarantine'/result['quarantine_name']).read_text(),'original')
        self.assertEqual(self.call('quarantine-delete','again',path='note.txt',approval_id=aid)['status'],'DENIED')

    def test_expiry(self):
        self.create();aid=self.approve();self.g.clock=lambda:401
        self.assertEqual(self.call('quarantine-delete','late',path='note.txt',approval_id=aid)['status'],'DENIED')
        self.assertTrue((self.root/'note.txt').exists())

    def test_changed_file_invalidates_approval(self):
        self.create();aid=self.approve();(self.root/'note.txt').write_text('changed')
        r=self.call('quarantine-delete','move',path='note.txt',approval_id=aid)
        self.assertEqual(r['status'],'DENIED');self.assertTrue((self.root/'note.txt').exists())

    def test_approval_binds_reviewed_content(self):
        self.create();r=self.call('request-delete','request',path='note.txt')
        a=self.g.call(self.admin,'approve-delete','wrong',path='other.txt',content=r['sha256'],approval_id=r['approval_id'])
        self.assertEqual(a['status'],'DENIED')

    def test_idempotence_and_conflict(self):
        self.create();r=self.call('create','create',path='note.txt',content='original')
        self.assertTrue(r['replayed']);self.assertEqual(r['status'],'CREATED')
        self.assertEqual(self.call('create','create',path='other.txt',content='bad')['reason'],'REQUEST_ID_CONFLICT')
        self.assertFalse((self.root/'other.txt').exists())

    def test_duplicate_concurrency_one_creation(self):
        def run(_):return Gateway(self.control).call(self.agent,'create','same',path='one.txt',content='one')
        with ThreadPoolExecutor(max_workers=5) as p:results=list(p.map(run,range(5)))
        self.assertEqual(sum(not r.get('replayed') for r in results),1)
        self.assertEqual((self.root/'one.txt').read_text(),'one')

    def test_special_and_large_files(self):
        os.mkfifo(self.root/'pipe')
        self.assertEqual(self.call('read','pipe',path='pipe')['status'],'DENIED_OR_FAILED')
        (self.root/'big').write_bytes(b'x'*65537)
        self.assertEqual(self.call('read','big',path='big')['status'],'DENIED_OR_FAILED')

    def test_control_must_be_outside_root(self):
        with self.assertRaises(ValueError):initialize(self.root/'nested-control',self.root)


if __name__=='__main__':unittest.main()
