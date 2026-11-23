"""Real file operations inside a temporary demo directory only.
The administrator step is scripted for demonstration, NOT a real human approval.
"""
import json
import tempfile
from pathlib import Path
from gateway import Gateway, initialize

with tempfile.TemporaryDirectory() as directory:
    base=Path(directory);root=base/'allowed';control=base/'operator'
    initialize(control,root)
    agent=json.loads((control/'agent.credential.json').read_text())['token']
    admin=json.loads((control/'admin.credential.json').read_text())['token']
    g=Gateway(control)
    def show(label,result):print(json.dumps({'step':label,**result},ensure_ascii=False))
    show('實際建立檔案',g.call(agent,'create','create',path='demo.txt',content='合成測試內容'))
    show('實際讀取檔案',g.call(agent,'read','read',path='demo.txt'))
    show('阻擋越界路徑',g.call(agent,'create','escape',path='../outside.txt',content='must not be written'))
    show('阻擋未核准隔離',g.call(agent,'quarantine-delete','no-approval',path='demo.txt',approval_id='missing'))
    review=g.call(agent,'request-delete','request',path='demo.txt')
    show('建立待人工審查項目',review)
    show('示範用腳本模擬管理者核准（非真實人工審核）',g.call(admin,'approve-delete','approve',path=review['path'],content=review['sha256'],approval_id=review['approval_id']))
    result=g.call(agent,'quarantine-delete','move',path='demo.txt',approval_id=review['approval_id'])
    show('實際移到隔離區',result)
    assert not (root/'demo.txt').exists()
    assert (control/'quarantine'/result['quarantine_name']).read_text()=='合成測試內容'
    assert not (base/'outside.txt').exists()
    print('實際檔案效果已核對；示範結束，清除整個暫存測試目錄。')
