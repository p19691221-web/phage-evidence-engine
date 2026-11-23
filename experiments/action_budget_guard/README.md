# 動作預算守門器：獨立本機實驗

狀態：**本機預算保留模型，不是正式資安產品，也不是 PHAGE 授權引擎。**

本次由使用者要求新增獨立程式實驗。既有 PHAGE 核心、研究暫停紀錄、CLAIMS_STATUS.md 與 DF 編號均未修改。本目錄的測試結果不能提升 PHAGE 既有能力的證據等級。

## 用途

驗證一個狹窄問題：同一授權期間內，多個代理的個別小額請求，是否可能被同一個累計預算約束。

- 精確比對動作、對象、代理識別文字、幣別與固定時間窗。
- 單筆上限與共用累計上限，以整數最小單位計算，不做匯率換算。
- 同一個 SQLite 寫入交易內檢查總額及保留額度。
- 相同請求識別碼與內容重送，不重複保留額度；內容不同則拒絕。
- 超過人工覆核門檻回傳 REVIEW_REQUIRED，不會接受呼叫端的一個 approved=true 就繼續。
- 留下決策理由與請求摘要雜湊，不執行採購、付款、API 或系統操作。

`RESERVED` 只表示本機資料庫已保留預算，**不表示合法授權、真實身分已驗證或外部動作已執行**。重送結果帶有 `reused=true`，不可據此再次執行外部動作。

## 在 Codespaces 執行

僅需 Python 3.10 以上與標準函式庫，無需付費 API 金鑰。

```bash
python -m unittest discover -s experiments/action_budget_guard -p 'test_*.py' -v
python experiments/action_budget_guard/demo.py
```

示範會用暫存資料庫模擬兩個代理共用 100 單位預算，每次 20 單位；前五次保留成功，第六次因累計超標拒絕。結束時清除示範資料庫。

手動使用：

```bash
python experiments/action_budget_guard/guard.py --db guard.sqlite init
python experiments/action_budget_guard/guard.py --db guard.sqlite add-policy policy.json
python experiments/action_budget_guard/guard.py --db guard.sqlite reserve request.json
python experiments/action_budget_guard/guard.py --db guard.sqlite ledger
```

政策欄位：id、agents、actions、targets、currency、start、end、per_action、total、review_above。start/end 使用 UTC Unix 秒，起點包含、終點不包含。完整範例請見 demo.py。

政策由可信任的本機操作者建立，同一 ID 不可改寫。請求者不可自行新增政策或建立另一份預算繞過限制。

## 明確尚未完成的事

- 無身分驗證、政策簽署、撤銷、人工核准驗證或可信任時間源。agent 等欄位只是輸入文字，不能當成認證。
- 無真實工具轉接器；若代理能繞過此程式直接呼叫工具，本程式無法阻止。
- SQLite 檔案與日誌可被有檔案權限者修改，雜湊不是不可竄改證明。
- 不處理多台主機、分散式資料庫、匯率、多政策重疊、退費、釋放額度或滾動時間窗。
- 為保守計算，已保留的額度不因外部失敗而自動歸還；目前沒有外部執行狀態可驗證。
- 沒有把外部執行與額度保留做成原子交易；不保證外部 exactly-once。
- 預算歸屬、根授權的正當性與完整性必須由外部制度確立。
- 一般系統/資料庫例外不會產生 RESERVED；呼叫方必須將例外視為停止，不能自行放行。

請只使用合成資料，不要把金鑰、個資或真實供應商機密放進此實驗。

## 驗證記錄

執行標準函式庫 unittest：12 個測試通過，涵蓋單筆/累計、跨代理共用、固定時間窗、重送、請求衝突、覆核停止、非法金額、資料庫錯誤，以及同機多連線競爭。

兩個多執行緒測試僅支持「同一台機器、同一 SQLite 檔案」的被測情況，不等於生產或分散式安全驗證。
