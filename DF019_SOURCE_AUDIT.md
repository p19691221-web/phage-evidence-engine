# DF-019 Source Audit

## Status

**SOURCE AUDIT ONLY — NOT A FIXTURE**

This document records the pre-fixture source audit for DF-019.

It does not establish a PHAGE substantive result.
It does not establish final fraud liability, internal-control liability,
final loss, or recovery amount.

Evidence collection remains open for primary-source revalidation.

---

## Candidate case

**DF-019 — Declared Repayment vs. Actual Settlement**

Subject:

IBK Industrial Bank of Korea's China subsidiary and an outsourced
online-lending / repayment chain in which electronic repayment records,
actual settlement of funds, and claimed reconciliation controls may
represent distinct evidentiary states.

Candidate structural distinction:

`RECORDED_REPAYMENT_STATE != INDEPENDENTLY_ESTABLISHED_SETTLEMENT_STATE`

This is a candidate analytical architecture only.

It is not yet a fixture invariant or PHAGE taxonomy value.

---

## S1 — IBK / FSS incident disclosure

**Status: VERIFIED — SECONDARY-SOURCE CROSS-CONFIRMED**

Multiple independent reports consistently state that:

- IBK formally disclosed the financial incident on 2026-07-15.
- The initially disclosed scale was approximately KRW 83.376 billion.
- As of the 2026-08-24 reporting based on material obtained by
  National Assembly member Shin Dong-wook, the actual incident amount,
  recovered amount, and expected final loss had not yet been finally
  determined.

### Supports

- existence of the disclosed incident;
- existence of the KRW 83.376 billion preliminary figure;
- continuing uncertainty concerning final loss and recovery.

### Does not establish

- KRW 83.376 billion as final realized loss;
- final fraud liability;
- final internal-control liability;
- final regulatory findings;
- final judicial findings.

### Primary-source gap

The underlying IBK disclosure and original FSS / National Assembly
materials have not yet been frozen as primary evidence in this audit.

`PRIMARY_DISCLOSURE_STATUS: OPEN`

---

## S2 — Repayment and settlement architecture

**Status: VERIFIED — SECONDARY-SOURCE CROSS-CONFIRMED**

Reported transaction architecture:

1. IBK China subsidiary participated in the lending arrangement.
2. A non-bank financial institution acted as an intermediary.
3. An online lending platform participated in borrower recruitment
   and repayment collection.
4. Borrower principal and interest were routed through an account
   controlled or designated within that platform-mediated structure.
5. Settlement to IBK occurred separately from the electronic repayment
   status represented within the lending / platform system.

This architecture creates an evidentiary distinction between:

- a repayment record;
- the underlying movement of money;
- settlement into an account controlled by IBK.

### Supports

- existence of a multi-party repayment chain;
- analytical separation between recorded repayment and actual settlement;
- need for independent settlement evidence before treating a repayment
  status as proof of receipt by the bank.

### Does not establish

- that every repayment record was false;
- the precise amount diverted;
- criminal intent;
- final fraud liability;
- final loss.

---

## S2A — Platform identity

The platform has been identified in secondary reporting as:

**桔子數科**

Additional secondary reporting describes the company as a Chinese
financial-technology / lending-intermediary platform.

**Status: SECONDARY_SOURCE_IDENTIFIED**

This identity has not yet been frozen against a sufficiently direct
primary corporate, regulatory, judicial, or IBK source.

### Must not be phrased as

`PRIMARY_IDENTITY_VERIFIED`

until primary-source revalidation is completed.

---

## S2B — Comparator architecture

Secondary reporting states that comparable lending arrangements used
by two other Korean banks operating in China did not employ the same
additional platform layer for management of lending records and
repayment information.

Those banks reportedly performed lending and maintained the relevant
loan / repayment records themselves.

**Status: SECONDARY_COMPARATOR**

### Supports

- existence of a potentially relevant architectural comparator;
- investigation of whether additional intermediary layers affected
  reconciliation observability.

### Does not establish

- that the IBK architecture was unlawful;
- that use of an intermediary itself caused the incident;
- that the comparator banks' systems were effective;
- that IBK had a legal duty to adopt the comparator architecture.

---

## S3 — Daily reconciliation claim

**Status: CLAIM_EXISTENCE_VERIFIED**

IBK has been reported as maintaining that loan principal / interest
repayment records and actual incoming amounts were compared daily.

The incident was nevertheless reportedly detected only on or around
2026-06-24 after settlement funds failed to arrive and borrower
complaints increased.

The verified fact at this stage is the **existence of the daily
reconciliation claim**.

It is not yet independently established that the claimed control was
performed every day in the manner described.

### Supports

`DAILY_RECONCILIATION_CLAIM_EXISTENCE = VERIFIED`

### Does not establish

- reconciliation actually occurred every day;
- reconciliation used independent settlement evidence;
- reconciliation was operationally effective;
- discrepancies did not exist before 2026-06-24;
- all relevant accounts were reconciled;
- internal-control adequacy;
- internal-control legal liability.

### Attribution boundary

Descriptions such as:

`허술한 내부통제`

("loose" or "inadequate" internal controls)

appearing in media reporting are external characterization.

They must not be transformed into an admission by IBK unless an
independent IBK source establishes such an admission.

---

## S4 — External warning availability

**Status: VERIFIED — MULTIPLE SECONDARY SOURCES**

Multiple reports state that five Chinese financial institutions had
removed or excluded the relevant platform from cooperation during
approximately March–April 2026.

IBK was reported as not having identified that risk signal in time.

The Korean formulation reported in this context includes:

`제때 파악하지 못했다`

which describes failure to identify or grasp the information in time.

### Supports

- existence of an earlier external risk signal;
- potential availability of relevant warning information before
  discovery of the IBK incident;
- investigation of the warning-to-control-response chain.

### Does not establish

- IBK actually knew of the warning at the time;
- deliberate disregard;
- intentional concealment;
- legal negligence;
- causation of the entire loss;
- final internal-control liability.

The distinction between:

`warning existed`

and

`IBK knowingly ignored warning`

must remain explicit.

---

## S5 — Final loss, recovery, investigation and liability

**Status: OPEN**

At the current audit cutoff, the following remain unresolved:

- actual final incident amount;
- amount successfully recovered;
- final realized loss;
- final regulatory findings;
- final fraud determination;
- final internal-control liability;
- final responsibility of specific persons or entities.

S5 is intentionally not closed using secondary reporting.

Missing S5 evidence must not be replaced by accumulation of otherwise
verified S1–S4 evidence.

---

## Candidate claim architecture

The current evidence supports retaining three analytically distinct
candidate layers:

### CLAIM_A — REPAYMENT_RECORD_STATUS

What repayment status was represented in the relevant electronic
records?

### CLAIM_B — ACTUAL_FUNDS_SETTLEMENT

Were the corresponding funds actually received and settled into the
relevant IBK-controlled account?

### CLAIM_C — FINAL_FRAUD_OR_INTERNAL_CONTROL_LIABILITY

What final fraud, regulatory, civil, criminal, or internal-control
responsibility is established by competent authorities?

These layers must not be collapsed.

In particular:

`REPAYMENT_RECORD_STATUS = REPAID`

does not by itself establish:

`ACTUAL_FUNDS_SETTLEMENT = SETTLED`

and neither state by itself establishes:

`FINAL_FRAUD_OR_INTERNAL_CONTROL_LIABILITY`

---

## Candidate fixture-level failure condition

**Candidate only — not locked**

`DECLARED_RECONCILIATION_AS_VERIFIED_SETTLEMENT`

Candidate failure concept:

A system treats the existence of a declared reconciliation procedure,
or an internally recorded repayment state, as sufficient proof that
the corresponding funds were independently verified as received.

Candidate control concept:

The declared control procedure and recorded repayment state remain
separate from independently sourced settlement evidence.

This name is intentionally fixture-level.

No PHAGE diagnostic taxonomy mapping is asserted at this stage.

---

## Provenance discipline

The following distinctions must remain explicit during any later
fixture construction:

- media characterization != actor admission;
- repayment record != actual settlement;
- declared control != verified execution of control;
- warning availability != demonstrated contemporaneous knowledge;
- preliminary incident amount != final loss;
- incident disclosure != final fraud determination;
- multiple secondary reports != primary evidence.

Cross-source agreement increases confidence in the existence of the
reported facts but does not convert secondary reporting into a primary
source.

---

## Open primary-source targets

Priority targets for any subsequent provenance pass:

1. IBK's original 2026-07-15 financial-incident disclosure.
2. FSS material concerning the incident.
3. Original material supplied to or obtained by the National Assembly.
4. Primary evidence identifying the platform and relevant contractual
   entities.
5. Primary records describing the reconciliation mechanism.
6. Subsequent regulatory, investigative, recovery, or judicial records.

Until those sources are obtained, unresolved nodes remain unresolved.

---

## Audit disposition

**DF-019 SOURCE AUDIT: OPEN / PRE-FIXTURE**

S1: VERIFIED from cross-confirmed secondary reporting  
S2: VERIFIED from cross-confirmed secondary reporting  
S2A platform identity: SECONDARY_SOURCE_IDENTIFIED  
S2B comparator architecture: SECONDARY_COMPARATOR  
S3 claim existence: VERIFIED  
S4 warning availability: VERIFIED from multiple secondary sources  
S5: OPEN  
PRIMARY_DISCLOSURE_STATUS: OPEN

No DF-019 fixture has been created.

No validator has been created.

No substantive PHAGE conclusion has been produced.
