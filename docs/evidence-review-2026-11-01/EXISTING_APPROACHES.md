# 既有方案對照

整理日期：2026-11-01
性質：研究線索，不是產品驗證或真實需求證據。

| 方案 | 目前線索 | 尚未建立 |
|---|---|---|
| Mary Technology | 使用者研究摘要指出既有證據與人工確認能力；原始引用待補 | 未參與第三方能否重建實際事件 |
| Black Duck | 使用者研究摘要指出既有授權、軌跡或覆核機制；原始引用待補 | 既有紀錄是否足夠、實際查核成本 |
| Endor Labs | 使用者研究摘要指出工具內建部分證據流程；原始引用待補 | 真實使用者遇到的查核缺口 |
| triAIge | 黑客松報導：來源原句、表單預填與人工確認 | 臨床上線、真實查核與外部驗證 |
| Blackout Ops | 同篇報導：工具白名單、人工關卡與動作驗證 | 正式維運與獨立重建結果 |
| ScanPilot | 同篇報導：動作政策檢查；移動、扭力、緊急停止由人控制 | 工業部署與事後紀錄完整性 |
| T-Agent | 同篇報導：影片時間區段、理由與疑似風險，交督導判斷 | 督導如何查證、回寫與保存版本 |

| Kihan Inktomi | 模型外授權，允許、拒絕或轉人工；受保護動作使用簽署許可，留存紀錄並可重算授權判定 | 正式採用、獨立複核實績，以及原始業務證據可追到多深 |

## 黑客松來源
AI 郵報，Hank，2026-10-28。
本次依據為使用者提供的報導截圖。
https://www.aiposthub.com/edge-ai-agent-hackathon-2026-nvidia/

四組來自同一篇報導，不是四份獨立市場研究。
機構背景不等於正式上線，原型能力不等於需求成立。

## 判讀限制
「沒有拍到二次煞停」不等於「沒有二次煞停」。
應查督導如何補證據、確認或推翻 AI，以及保存最後決定。

既有工具內建授權、軌跡與人工確認，
削弱這些能力本身構成 PHAGE 差異的主張。
但不能因此推定既有方案完全足夠，或剩餘缺口必然存在。

下一步以過去實際事件比較：
第三方能否只靠原紀錄重建？何處需要原人補述？
實際成本與後果是什麼？既有流程何時已經足夠？

不因本表新增功能、fixture、DF 或提升 CLAIMS_STATUS。

### CrowdStrike Falcon Guardian / Falcon Observe (2026-11-03)

CrowdStrike announced the AI Kill Switch in Falcon Guardian. The announcement describes authorized administrators triggering termination and the system recording each action in an audit trail. Termination was available at the AI gateway at announcement time, with endpoint termination described as forthcoming. Track Falcon Observe separately as a planned capability.

**Open comparison question.** Can a reviewer outside the original team use retained records to verify a specific pre-termination AI finding against the source material and versions available at the time, the applicable criterion, and any human intervention? The announcement establishes the scope of the advertised controls but does not establish what an independent reviewer can reconstruct in practice.

Sources: [AI Kill Switch announcement](https://crowdstrike.gcs-web.com/news-releases/news-release-details/crowdstrike-introduces-ai-kill-switch-ai-safety) and [enterprise AI security announcement](https://www.crowdstrike.com/en-us/press-releases/crowdstrike-delivers-ai-security-safety-for-the-enterprise/).

### Industry context: vulnerability remediation (2026-11-05)

The 2026 Verizon DBIR reports that the median time to fully remediate known exploited vulnerabilities in its reporting dataset increased from 32 to 43 days. The comparison does not establish that AI caused the increase.

SinoPac Bank's November 4 statement attributes the unauthorized transfers to an external attacker exploiting a supplier security setting in its new online banking transaction system. The statement does not identify AI use.

This is background on remediation and validation. The sources do not describe a reviewer independently reconstructing an AI-assisted decision from retained records.

Sources: [Verizon 2026 DBIR](https://www.verizon.com/business/resources/T343/reports/2026-dbir-data-breach-investigations-report.pdf) and [SinoPac Bank statement](https://bank.sinopac.com/sinopacBT/about/news-center/news/content/20261104.html).

## Kihan Inktomi 與 Constitutional Computing（2026-11-08 查證）

- **來源與階段。** Kihan 官方公告與 GamesBeat 原文發布於 2026-11-05，商傳媒於 11-06 轉述。Kihan 自述決策引擎已運作，正式環境的執行整合仍在開發。初步企業評估目標為 2026 年 12 月，實際開始日期、參與資格及正式採用待確認。
- **授權與紀錄。** 決策引擎在模型外，依簽署規則允許、拒絕或轉人工。受保護工具驗證與動作和參數綁定的單次許可。產品文件描述可用留存輸入與規則版本重算授權判定。
- **使用環境與名稱。** 設計為部署在客戶自有基礎設施，規劃支援 Anthropic、OpenAI、Google 模型，以及 Hermes Agent 與 MCP。Kihan 的 Constitutional Computing 用於執行時授權。Anthropic 的 Constitutional AI 是以原則引導模型訓練的方法。
- **與 PHAGE 的重疊。** 以同一筆歷史案例比較兩件事：未參與原案的人能否重算當時的授權判定，以及能否追到當時的原始資料、版本與準則，驗證 AI 參與的實質判斷。前者有公開機制說明。後者的範圍、實際複核結果與成本仍待確認。
- **CSA 與田野紀錄。** Zenity 委託的 CSA 調查中，53% 的受訪者表示代理人偶爾或有時超出預期權限，47% 表示過去一年遇過涉及代理人的安全事件。2026-11-07 高雄金融博覽會的五個攤位接觸未取得具體的歷史獨立複核案例。兩者的問題和樣本不同，不能直接比較發生率。
- **研究處置。** 維持暫停開發。待有可查證案例，再比較獨立複核的完整性、所需協助及成本。

資料來源：
- [Kihan 官方公告](https://kihan.ai/press/kihan-launches-constitutional-computing/)
- [Inktomi 產品說明](https://kihan.ai/product/)
- [GamesBeat 原文](https://gamesbeat.com/kihan-launches-constitutional-computing-to-bring-enforceable-authority-to-enterprise-ai-agents/)
- [CSA 原始調查](https://cloudsecurityalliance.org/artifacts/enterprise-ai-security-starts-with-ai-agents)
- [Anthropic Constitutional AI 研究](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
