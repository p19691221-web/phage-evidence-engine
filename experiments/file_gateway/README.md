# 實際檔案操作安全閘道：可執行原型

這是一個會真的讀檔、建立檔案及移動檔案的 Linux/POSIX 程式，不是純展示頁。它是獨立原型，沒有修改 PHAGE 核心、CLAIMS_STATUS.md 或 DF 編號；不宣稱 PHAGE 已取得生產級授權能力。

## 實際可執行的動作

- `read`：只讀取允許目錄內、最多 64 KiB 的 UTF-8 一般檔案。
- `create`：建立新檔，不覆寫既有檔案。
- `request-delete`：建立一個 5 分鐘有效的待核准項目，綁定路徑、檔案 SHA-256、device/inode。
- `approve-delete`：須使用獨立的管理者憑證，並明確提供人工查核過的路徑與 SHA-256。
- `quarantine-delete`：代理取得有效核准後，才會把同一檔案移至控制目錄的隔離區。沒有永久刪除功能。

每次呼叫需有憑證、操作及唯一 request_id。用相同 ID 重送時回傳既有結果，不重複執行；相同 ID 不同內容拒絕。若程式在副作用前後中斷，回傳 OUTCOME_UNKNOWN，不自動重試。

路徑檢查使用 descriptor-relative 開啟與 O_NOFOLLOW，拒絕 `..`、絕對路徑、符號連結、硬連結與特殊檔案。控制目錄與工作目錄必須分離。

## 立即執行

Python 3.10+，Linux/POSIX，不需要模型、網路或 API 金鑰。

```bash
python -m unittest discover -s experiments/file_gateway -p 'test_*.py' -v
python experiments/file_gateway/demo.py
```

demo 只在新建暫存目錄執行真實檔案操作，結束時清除該測試目錄。demo 的管理者核准由腳本模擬，不能拿它當作已整合真實人員核准的證據。

## 建立自己的測試範圍

```bash
python experiments/file_gateway/gateway.py --control /tmp/guard-operator init --root /tmp/guard-allowed
```

此命令建立兩份不同的憑證檔（權限 0600）：

- `/tmp/guard-operator/agent.credential.json`
- `/tmp/guard-operator/admin.credential.json`

憑證不會顯示於終端。不要提交或分享這些檔案。實際使用時，請選擇可信任、非共用的私有路徑；上述 /tmp 路徑只供本機示範，初始化拒絕覆蓋既有控制目錄。

建立 request.json：

```json
{"operation":"create","request_id":"unique-create-001","path":"note.txt","content":"合成測試內容"}
```

執行：

```bash
python experiments/file_gateway/gateway.py --control /tmp/guard-operator call --credential /tmp/guard-operator/agent.credential.json --request request.json
```

可查看目錄確認檔案真的建立。其他操作與核准欄位見 demo.py；管理者必須獨立核對實際檔案與雜湊，不能無條件照抄代理的核准請求。

## 尚未完成的安全邊界

**本程式不能限制擁有相同作業系統帳號權限的惡意代理。** 若代理能讀取管理者憑證、修改資料庫，或直接存取工作目錄，就能繞過程式。正式接管前，必須把代理放在隔離帳號／容器內，讓代理只能呼叫受控服務，而不能讀取控制目錄、管理者憑證或直接寫入宿主檔案系統。此套件尚未提供該服務、容器部署或網路 API。

此外：

- 未部署到 Codespaces，未接上現有 agent/MCP 工具入口。
- 未實作正式管理者登入、多租戶、遠端人工核准 UI、憑證撤銷或輪替。
- 本機系統時間並非可信任時間源；不防主機管理員或控制目錄持有者。
- SQLite 與檔案系統不是共同原子交易；崩潰後可能出現已完成副作用但結果不明。必須人工查核，不能換 ID 盲目重試。
- 惡意主機程序並行替換路徑或修改內容，仍超出部署保證。移動後會再核對 inode 與內容；不一致時保留隔離檔並回報 OUTCOME_UNKNOWN，不表示原動作沒有發生。
- 其他失敗也可能已有部分檔案副作用；DENIED_OR_FAILED 不能當成「保證零變動」，需查核再處理。
- 稽核資料庫及隔離檔是本機資料，不具防竄改或外部備援保證。讀檔回應會進入本機重送結果快取，控制目錄須妥善保護。
- 不掃毒、不分析檔案是否惡意、不攔截網路、採購或付款。
- 未與 action_budget_guard 組成單一原子授權／執行流程。

## 已執行的驗證

15 個 unittest 通過。包括真實建立／讀取／隔離移動、未核准拒絕、過期核准、內容變更、路徑穿越、符號連結、硬連結、特殊檔案、角色與憑證拒絕、既有檔案保護、重送及同機並行重送。

這些測試只證明所列本機案例，不代表正式環境安全驗證或完整產品。
