"""Linux Unix-socket gateway: roles come from kernel peer credentials, never request JSON."""
import argparse
import json
import os
import socket
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'file_gateway'))
from gateway import Gateway
MAX_REQUEST = 100000

def handle(connection, gateway, agent_uid, admin_uid):
    peer_pid, peer_uid, peer_gid = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if peer_uid not in (agent_uid, admin_uid):
        return {'status': 'DENIED', 'reason': 'PEER_NOT_ALLOWED'}
    connection.settimeout(3)
    data = bytearray()
    while b'\n' not in data:
        chunk = connection.recv(min(4096, MAX_REQUEST + 1 - len(data)))
        if not chunk:
            raise ValueError('newline-terminated JSON required')
        data.extend(chunk)
        if len(data) > MAX_REQUEST:
            raise ValueError('request too large')
    line, tail = data.split(b'\n', 1)
    if tail:
        raise ValueError('one request per connection')
    request = json.loads(line)
    if not isinstance(request, dict) or set(request) - {'operation','request_id','path','content','approval_id'}:
        raise ValueError('unexpected fields; roles and credentials cannot be supplied')
    role = 'admin' if peer_uid == admin_uid else 'agent'
    token = json.loads((gateway.control / (role + '.credential.json')).read_text())['token']
    return gateway.call(token, **request)

def serve(control, address, agent_uid, admin_uid):
    if agent_uid == admin_uid or agent_uid == os.getuid() or admin_uid == os.getuid():
        raise ValueError('gateway, agent and admin must have different UIDs')
    gateway = Gateway(control)
    os.umask(0o117)  # socket 0660; directory is created by trusted launcher
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(address)  # refuse an existing path; never unlink arbitrary files
        os.chmod(address, 0o660)
        listener.listen(16)
        while True:
            connection, _ = listener.accept()
            with connection:
                try:
                    result = handle(connection, gateway, agent_uid, admin_uid)
                except (ValueError, TypeError, OSError, KeyError) as error:
                    result = {'status':'DENIED_OR_FAILED', 'reason':str(error)}
                connection.sendall((json.dumps(result, ensure_ascii=False)+'\n').encode())

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',required=True);p.add_argument('--socket',required=True)
    p.add_argument('--agent-uid',required=True,type=int);p.add_argument('--admin-uid',required=True,type=int)
    a=p.parse_args();serve(a.control,a.socket,a.agent_uid,a.admin_uid)
