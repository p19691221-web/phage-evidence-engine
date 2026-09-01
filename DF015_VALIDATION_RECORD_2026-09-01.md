# DF-015 A/B/C 因果約束驗證記錄 — 2026-09-01

> 本記錄凍結 DF-015 A/B/C regression 的實際執行結果。
>
> 本驗證針對一般因果表述結構：
> over-linking、under-linking 與 multi-parent causal restraint。
>
> 本記錄不擴充 taxonomy，不修改 fixture，也不據此對真實案件作因果判決。

---

## 1. 驗證識別

- 驗證 ID：DF015-ABC-2026-09-01
- 驗證名稱：DF-015 A/B/C causal restraint regression
- 驗證日期：2026-09-01
- 驗證性質：Regression evidence freeze
- Fixture basis：CASE_SHAPED_SYNTHETIC
- Record branch：`df015-abc-regression`

---

## 2. 凍結驗證目標

- Repository：`p19691221-web/phage-evidence-engine`
- Workflow：`DF-015 causal restraint`
- Workflow file：`.github/workflows/python-app.yml`
- Workflow run：`#21`
- Event：`pull_request / synchronize`
- Source PR：`#14`
- Source branch：`phage-v6-revocation-enforcement`
- Head commit reference：`4dc8c27`
- Runner：`ubuntu-latest`
- Python：`3.11`
- Regression command：

```text
python test_df015_causal_compression.py
```

> 注意：GitHub Actions 的 pull_request workflow 可能執行 PR merge ref。
> `4dc8c27` 在此記錄為 source branch 的 head commit reference，
> 不宣稱為唯一精確的 workflow execution SHA。

---

## 3. 修訂前驗證

- [x] 已確認執行的是既有 DF-015 A/B/C regression。
- [x] 已確認實際執行前未修改 `causal_validator.py`。
- [x] 已確認未修改 A/B/C fixture 以配合結果。
- [x] 已確認未新增或擴充 diagnostic taxonomy。
- [x] 已先凍結預期結果，再檢視實際 CI 輸出。

---

## 4. 實際 Regression 結果

GitHub Actions 實際輸出：

```text
PASS: DF-015-A over-linking detected
PASS: DF-015-B under-linking detected
PASS: DF-015-C multi-parent restraint preserved

3/3 DF-015 tests PASSED
```

總體結果：

```text
DF015_ABC_REGRESSION = PASS_3_OF_3
```

---

## 5. DF-015-A — Over-linking

實際狀態：

```text
STATE = UNRESOLVED
DIAGNOSTIC = CAUSAL_OVERLINK
CLASSIFICATION = EXPECTED_DETECTION
```

實際 diagnostics 包含：

```text
edge: workforce_software -> unstable_schedule
Representation upgrades ATTRIBUTED evidence to ESTABLISHED causation.
refs: TECHTARGET-2015, KRONOS-RESPONSE
```

以及：

```text
edge: workforce_software -> unstable_schedule
Representation marks this edge as a sole cause while other plausible causal
parents remain in the case:
management_policy(SUPPORTED),
store_implementation(SUPPORTED)
refs: CNN-2015, CBS-2014, SEATTLE-TIMES-2016
```

Disposition：

```text
RESULT = EXPECTED PASS
FIXTURE_INVALID = NO
IMPLEMENTATION_GAP = NO
```

---

## 6. DF-015-B — Under-linking

實際狀態：

```text
STATE = UNRESOLVED
DIAGNOSTIC = CAUSAL_UNDERLINK
CLASSIFICATION = EXPECTED_DETECTION
```

實際 diagnostic：

```text
edge: short_notice_schedule -> planning_constraint
Case establishes this causal relation, but the representation omits the edge.
refs: EMPLOYEE-TESTIMONY, SURVEY-RESULT
```

Disposition：

```text
RESULT = EXPECTED PASS
FIXTURE_INVALID = NO
IMPLEMENTATION_GAP = NO
```

---

## 7. DF-015-C — Multi-parent restraint control

實際狀態：

```text
STATE = CLEAN
DIAGNOSTICS = NONE
CLASSIFICATION = CONTROL_PRESERVED
```

控制組要求保留多父因與各自 evidence status，而不壓縮成單一原因：

```text
workforce_software -> unstable_schedule
STATUS = ATTRIBUTED

management_policy -> unstable_schedule
STATUS = SUPPORTED

store_implementation -> unstable_schedule
STATUS = SUPPORTED

unstable_schedule -> employee_hardship
STATUS = ESTABLISHED
```

實際輸出：

```text
PASS: DF-015-C multi-parent restraint preserved
```

Disposition：

```text
RESULT = EXPECTED PASS
FIXTURE_INVALID = NO
IMPLEMENTATION_GAP = NO
```

---

## 8. Freeze Classification

本輪 A/B/C regression 未發現需要修正 implementation、fixture 或 taxonomy 的情況。

```text
FIXTURE_INVALID = NO
IMPLEMENTATION_GAP = NO
EVIDENCE_DEPENDENCY_UNRESOLVED = NO
TAXONOMY_CHANGE_REQUIRED = NO
```

本輪未出現需要提前決定 `FACT_UNRESOLVED` 或其他新 taxonomy member 的情況。

---

## 9. Explicit Non-Claims

本次 CI 實際輸出明確保留下列 non-claims：

```text
DF-015 does NOT claim AIID #10 is false.
DF-015 does NOT establish or refute Kronos-specific causation.
DF-015 tests only the general representation shape:
over-linking, under-linking, and multi-parent causal restraint.
```

因此本記錄不得被解讀為：

- 對 AIID #10 真實事件作事實判決；
- 建立或否定 Kronos-specific causation；
- 證明任一真實世界行為人為唯一原因；
- 將 `UNRESOLVED` 解讀為 false；
- 將 regression PASS 解讀為真實世界因果真實性已被證明。

---

## 10. Validation Disposition

```text
DF015_A = EXPECTED_DETECTION
DF015_B = EXPECTED_DETECTION
DF015_C = CONTROL_PRESERVED

DF015_ABC_REGRESSION = PASS_3_OF_3

FIXTURE_INVALID = NO
IMPLEMENTATION_GAP = NO
EVIDENCE_DEPENDENCY_UNRESOLVED = NO
TAXONOMY_CHANGE_REQUIRED = NO

DF015_PENDING_ACTION_REAL_REGRESSION_OUTPUT = CLOSED
```

本記錄凍結目前 DF-015 A/B/C regression 的實際 CI 證據。

後續 specification、fixture 或 implementation 的擴充，應透過新的驗證記錄處理，而不回溯擴張本次結果的含義。
