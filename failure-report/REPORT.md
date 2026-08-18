# PHAGE Challenge Fixture Report

> **Notice:** Do not include production secrets, credentials, PII, classified information, or other sensitive data.
>
> Redact `fixture.redacted.yaml` before submission.
>
> Submitted challenges are classified as **Challenge Fixtures**. They must be independently reproduced before they can be promoted to **Validated Death Fixtures**.

---

## 1. Challenge Metadata

- **Submitter / Handle:**
- **Date:**
- **Assessed PHAGE Engine Version:** v0.1-research-preview

### Primary Classification Target

- [ ] FALSE_SATISFIED
- [ ] FALSE_GAP
- [ ] FALSE_UNRESOLVED
- [ ] MISSING_OPEN_DEPENDENCY
- [ ] WRONG_DEPENDENCY_ORDER
- [ ] EXPECTATION_PROVENANCE_FAILURE
- [ ] SCHEMA_CANNOT_REPRESENT
- [ ] NEW_FAILURE_SHAPE

---

## 2. Core Challenge Statement

**What did PHAGE say that you believe is structurally wrong?**

Example:

> PHAGE returned SATISFIED, but the supplied evidence structure was incomplete.

Describe the structural failure clearly:

[ Insert challenge statement here ]

---

## 3. Evidence of Structural Flaw

**Expected Engine State:**

[ SATISFIED | GAP_PRESENT | UNRESOLVED | OTHER ]

**Actual Engine State:**

[ SATISFIED | GAP_PRESENT | UNRESOLVED | OTHER ]

**Why is the current evaluation structurally incorrect for this workflow?**

[ Explain here ]

---

## 4. Reproduction Boundary

- Does reproduction require assumptions that are not represented in the submitted fixture?
  - [ ] No
  - [ ] Yes — explain below

- Can the failure shape be represented using synthetic or redacted data?
  - [ ] Yes
  - [ ] No — explain below

**External assumptions or dependencies:**

[ Describe here ]

A challenge that cannot be reproduced without undisclosed production context may remain a Challenge Fixture rather than becoming a Validated Death Fixture.

---

## 5. Redaction & Package Verification

Before submission:

- [ ] I reviewed `fixture.redacted.yaml`.
- [ ] I removed credentials, secrets, customer identifiers, and unnecessary personal data.
- [ ] I did not include classified or operationally sensitive information.
- [ ] I included the raw `engine-output.json`.
- [ ] I identified the PHAGE Engine version used.
- [ ] I understand that submission does not make this a Validated Death Fixture.
- [ ] I understand that maintainers must reproduce the structural failure before maturity status can change.

---

## 6. Non-Claims

A submitted Challenge Fixture does not by itself establish:

- that PHAGE contains a validated architectural defect;
- that an underlying real-world allegation is true;
- that any person or organization violated a duty;
- that PHAGE should authorize or deny an action;
- that a failure shape generalizes beyond the reproduced scope.

---

## Maturity Discipline

**Maturity follows demonstrated capability, not threat coverage by association.**

A fixture moves forward only through reproduction and evidence. Writing a fixture is not equivalent to validating a Death Fixture.
