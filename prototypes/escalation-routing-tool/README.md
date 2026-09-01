# Escalation Routing Check

Bilingual research prototype for structural-gap detection and escalation routing.

Traditional Chinese / English.

## Purpose

This prototype explores a narrow governance question:

> When existing case records reveal a structural gap, who should be asked to review it?

The tool does **not** decide the final case outcome.

Instead, it identifies selected structural conditions that may require escalation or additional review.

## Current prototype rules

The current demonstration includes four routing rules:

### R1 — SCOPE_DESIGN_GAP

An involved actor type is not covered by the current assessment categories.

Review target:

- risk-assessment schema owner
- supervisor
- policy layer

### R2 — ACCUMULATION_NOT_ESCALATED

Repeated visits / contacts and repeated expressed wishes have accumulated without a corresponding escalation review.

Review target:

- supervisor
- unit lead

### R3 — PREFERENCE_DIMENSION_COLLAPSE

A child expressing a wish to be placed and refusing one specific placement type are treated as if they were the same preference.

Review target:

- case conference
- review of alternative placement options

### R4 — AUTHORITY_THRESHOLD_UNDEFINED

The relevant judicial / protective threshold remains unconfirmed.

Review target:

- legal counsel
- responsible legal or regulatory authority

## Governance boundary

The prototype follows a strict separation:

```text
Assessment ≠ Authorization ≠ Execution
```

This tool may identify a structural gap.

It does **not** establish that:

- placement is warranted
- an incident occurred
- a legal threshold has been met
- a person is responsible
- a final disposition should be taken

A triggered rule is **not a conclusion**.

No triggered rule does **not** mean the case is safe, complete, or properly handled.

All outputs require review by an accountable human authority.

## Why this distinction matters
Governance tooling should not silently convert:

```text
evidence
→ assessment
→ authority
→ action
```

into one automatic step.

This prototype deliberately stops at:

```text
existing record
→ structural-gap detection
→ review target
```

The accountable authority remains outside the tool.

## Status

```text
RESEARCH PROTOTYPE

Production readiness: NOT ESTABLISHED
Decision authority: NONE
Legal authority: NONE
Case-level disposition authority: NONE
```

This repository component is intended for research, demonstration, and architecture discussion.

It is not a production child-protection decision system.

## Data boundary
Use synthetic, public, de-identified, or otherwise appropriately authorized data only.

Do not place private case records, child-identifying information, confidential documents, or protected personal data in this demonstration repository.

## Implementation

Main component:

```text
EscalationRoutingTool.jsx
```

The current prototype is implemented as a bilingual React component.

## PHAGE context

This prototype explores a routing layer adjacent to PHAGE.

PHAGE research separates:

```text
Assessment
Authorization
Execution
```

Structural-gap detection answers:

> Is something missing, inconsistent, or in need of review?

Escalation routing asks:

> Who should review it?

Authority remains a separate governance problem.

## Non-claims

This prototype does not claim:

```text
case truth
legal admissibility
legal responsibility
professional judgment
placement necessity
institutional compliance
production safety
```

The prototype demonstrates a governance pattern, not an automated final-decision system.
