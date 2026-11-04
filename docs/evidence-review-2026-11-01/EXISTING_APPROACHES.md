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
