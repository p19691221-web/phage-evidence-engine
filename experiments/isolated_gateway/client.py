"""Send one JSON request on stdin to the local protected gateway socket."""
import argparse
import json
import socket
import sys

def call(address, request):
    wire=(json.dumps(request, ensure_ascii=False)+'\n').encode()
    if len(wire)>100000:raise ValueError('request too large')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(15);s.connect(address);s.sendall(wire)
        with s.makefile('rb') as f:
            response=f.readline(200000)
        return json.loads(response)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--socket',required=True);a=p.parse_args()
    print(json.dumps(call(a.socket,json.loads(sys.stdin.buffer.read(100001))),ensure_ascii=False,indent=2))
