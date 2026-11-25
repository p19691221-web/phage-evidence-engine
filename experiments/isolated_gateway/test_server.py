import os,socket,tempfile,threading,unittest
from pathlib import Path
from server import handle
from gateway import Gateway,initialize
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();p=Path(self.t.name);initialize(p/'c',p/'r');self.g=Gateway(p/'c')
 def tearDown(self):self.t.cleanup()
 def req(self,data,allowed=True):
  a,b=socket.socketpair();out=[]
  def work():
   with b:
    try:out.append(handle(b,self.g,os.getuid() if allowed else os.getuid()+2,os.getuid()+1))
    except (ValueError,TypeError,PermissionError) as e:out.append(type(e).__name__)
  t=threading.Thread(target=work);t.start()
  with a:
   try:a.sendall(data);a.shutdown(socket.SHUT_WR)
   except BrokenPipeError:pass
  t.join(5);self.assertFalse(t.is_alive());return out[0]
 def test_create_read(self):
  self.assertEqual(self.req(b'{"operation":"create","request_id":"a","path":"x","content":"hello"}\n')['status'],'CREATED')
  self.assertEqual(self.req(b'{"operation":"read","request_id":"b","path":"x"}\n')['text'],'hello')
 def test_spoof(self):self.assertEqual(self.req(b'{"role":"admin"}\n'),'ValueError')
 def test_approve_role(self):self.assertEqual(self.req(b'{"operation":"approve-delete","request_id":"a"}\n'),'PermissionError')
 def test_peer(self):self.assertEqual(self.req(b'{}\n',False)['reason'],'PEER_NOT_ALLOWED')
 def test_frames(self):self.assertEqual(self.req(b'{}\n{}\n'),'ValueError')
 def test_oversize(self):self.assertEqual(self.req(b'x'*100001+b'\n'),'ValueError')
if __name__=='__main__':unittest.main()
