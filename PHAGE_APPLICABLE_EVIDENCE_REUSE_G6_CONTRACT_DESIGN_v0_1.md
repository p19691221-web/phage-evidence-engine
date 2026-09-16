# PHAGE Applicable Evidence Reuse — G6 Contract Design v0.1

STATUS: DESIGN IN PROGRESS — NOT YET FROZEN

## Standing State

APPLICABLE_EVIDENCE_REUSE_POLICY
→ DESIGN FROZEN

TRUSTED_CURRENT_TIME_BOUNDARY_FROZEN
≠
G6_READY

G6
→ CONTRACT DESIGN IN PROGRESS
→ NOT YET EXECUTABLE

No Python changes.
No G6 test fixture yet.
No reuse enforcement implementation yet.

---

## 1. PURPOSE

G6 freezes the externally observable contract for Applicable Evidence
Reuse before any Python enforcement implementation is written.

G6 MUST NOT redefine the frozen Applicable Evidence Reuse Policy.

Its job is to convert the frozen policy into executable observations.

G6 is a fixture family rather than a single happy-path fixture.

---

## 2. CONTRACT OUTPUT STATES

The reuse boundary exposes exactly these reuse outcomes:

- REUSE_ALLOWED
- REUSE_UNRESOLVED
- REUSE_INVALIDATED

REUSE_ALLOWED is admission of the exact prior evidence bundle into
the current deterministic evaluation.

REUSE_ALLOWED is NOT:

- authorization;
- continuation of the prior APPLICABLE result;
- a new APPLICABLE result;
- permission to execute an effect.

Only the current deterministic evaluation may produce the current
decision.

REUSE_UNRESOLVED means the system lacks sufficient trusted,
verified information to establish reuse safety.

REUSE_INVALIDATED means an authoritative verified check positively
established that the prior evidence bundle is not eligible for reuse.

---

## 3. G6 FIXTURE FAMILY

### G6A — Valid Exact-Bundle Reuse

Given:

- prior verified evaluation result = APPLICABLE;
- exact evidence bundle identity is recovered from that evaluation;
- original dependency closure is recovered, verified, and complete;
- canonical subject/action/target/scope are unchanged;
- original authority derivation remains valid and unchanged;
- evidence origin/integrity reverification succeeds;
- authoritative current policy/schedule/grant/dependency state is unchanged;
- trusted current time is acquired and verified;
- effective reuse deadline has not been reached.

Expected:

REUSE_ALLOWED

And:

- the evidence bundle may be admitted to the current deterministic evaluation;
- no authorization or effect is produced by the reuse gate itself.

---

### G6B — Evidence Bundle Substitution

Given:

- prior evaluation was APPLICABLE using evidence bundle A;
- caller presents independently valid evidence bundle B;
- B may contain equivalent values and may even be newer;
- all other required reuse conditions are affirmatively established;
- authoritative bundle identity verification establishes B != A.

Expected:

REUSE_INVALIDATED

The failure MUST be caused by evidence-bundle identity mismatch,
not by semantic value mismatch.

A substitute bundle MUST NOT inherit reuse eligibility from the
prior APPLICABLE evaluation.

If exact bundle identity cannot be established either way,
this fixture does not apply; the outcome is REUSE_UNRESOLVED,
not REUSE_INVALIDATED.

---

### G6C — Dependency Closure Cannot Be Proven Complete

Given:

- the original dependency record exists;
- exact bundle identity and all other independently required checks
  do not positively establish invalidity;
- the system cannot establish that the dependency record contains the
  complete decision-relevant dependency closure.

Expected:

REUSE_UNRESOLVED

An intact or correctly bound but unverified-incomplete dependency
set MUST NOT be treated as sufficient for reuse.

Unknown completeness MUST NOT be interpreted as unchanged state.

---

### G6D — Relevant Authoritative Dependency Changed

Given:

- exact original evidence bundle is recovered and verified;
- original dependency closure is complete and verified;
- all other required reuse conditions are affirmatively established;
- authoritative current-state acquisition positively establishes
  that a dependency participating in the original derivation changed,
  was replaced, revoked, expired, deleted, or superseded.

Expected:

REUSE_INVALIDATED

The failure MUST be caused by the verified relevant dependency change.

An unrelated change outside the verified dependency closure MUST NOT
by itself invalidate reuse.

If authoritative current state cannot be obtained or verified,
this fixture does not apply; the outcome is REUSE_UNRESOLVED.

---

### G6E — Authoritative Current State Unavailable

Given:

- exact original evidence bundle is recovered and verified;
- no positive invalidating condition has already been established;
- reuse requires current policy/schedule/authority/grant state;
- the authoritative trusted source cannot provide or verify that state.

Expected:

REUSE_UNRESOLVED

Must NOT:

- use caller-supplied state;
- use an unverified cached state;
- assume unchanged state.

Rule:

unknown → never assume unchanged

---

### G6F — Reuse Freshness Deadline Reached or Exceeded

Given:

- exact original evidence bundle is otherwise reusable;
- all other required reuse conditions are affirmatively established;
- trusted current time is acquired and verified;
- trusted current time >= effective_reuse_deadline.

Expected:

REUSE_INVALIDATED

The validity interval ends at effective_reuse_deadline.

Therefore:

trusted_current_time < effective_reuse_deadline
→ freshness condition may still pass

trusted_current_time >= effective_reuse_deadline
→ REUSE_INVALIDATED

Reuse MUST NOT reset, refresh, renew, or replace the original
observation time.

For multi-member evidence bundles, the earliest applicable member
deadline controls.

If trusted current time cannot be acquired or verified,
the outcome is REUSE_UNRESOLVED, not REUSE_INVALIDATED.

---

### G6G — Authority Status Equal but Derivation Replaced

Given:

- exact original evidence bundle is recovered and verified;
- all other required reuse conditions are affirmatively established.

Original evaluation:

authority derivation A
→ CLEAN

Reuse time:

authority derivation B
→ CLEAN

And authoritative lineage verification establishes A != B.

Expected:

REUSE_INVALIDATED

CLEAN == CLEAN
does NOT establish
same authority derivation.

If the system cannot establish whether the current authority
derivation is the same as the original derivation,
the outcome is REUSE_UNRESOLVED, not REUSE_INVALIDATED.

---

### G6H1 — Fresh-Evaluation Isolation

Given:

- reuse returns REUSE_UNRESOLVED or REUSE_INVALIDATED;
- trusted workflow/policy permits a fresh evaluation.

Expected:

- fresh evaluation does not inherit the prior APPLICABLE result;
- the failed reuse candidate is not automatically re-admitted as
  fresh evidence;
- fresh evidence must independently satisfy ordinary acquisition,
  origin, integrity, completeness, binding, and freshness rules;
- the fresh evaluation's own result controls.

Fresh evaluation
≠
retry reuse under a different function name.

---

### G6H2 — Fresh Evaluation Not Permitted

Given:

- reuse returns REUSE_UNRESOLVED or REUSE_INVALIDATED;
- trusted workflow/policy does NOT permit a fresh evaluation.

Expected:

- no prior APPLICABLE result may authorize an effect;
- no fresh evaluation is entered;
- the workflow fails closed;
- no effect proceeds.

---

### G6H3 — Fallback Cycle Attempt

Given:

- a fallback fresh evaluation was entered after failed reuse;
- processing attempts to re-enter reuse evaluation for the same
  prior evaluation/evidence candidate.

Expected:

- the cycle is rejected;
- processing terminates;
- the workflow fails closed;
- no effect proceeds.

Fallback handling MUST have a terminating, monotonic control path.

---

## 4. CLASSIFICATION RULE

G6 freezes the distinction:

```text
positive authoritative proof of invalidity
→ REUSE_INVALIDATED

insufficient trusted proof either way
→ REUSE_UNRESOLVED

all required reuse conditions affirmatively established
→ REUSE_ALLOWED
```

### OUTCOME PRECEDENCE

Outcome classification MUST follow this precedence:

1. REUSE_INVALIDATED
   if any authoritative verified check positively establishes
   an invalidating condition.

2. REUSE_UNRESOLVED
   only if no invalidating condition has been positively established,
   but one or more required reuse facts cannot be affirmatively
   established.

3. REUSE_ALLOWED
   only if every required reuse condition has been affirmatively
   established and no invalidating condition exists.

Therefore:

```text
positive invalidity + unresolved secondary fact
→ REUSE_INVALIDATED

unresolved fact + no positive invalidity
→ REUSE_UNRESOLVED

all facts established + no invalidity
→ REUSE_ALLOWED
```

Never:

```text
unknown
→ assume unchanged
```

Never:

```text
prior APPLICABLE
→ assume reusable
```

Never:

```text
REUSE_ALLOWED
→ authorize effect
```

---

## 5. TRUSTED INPUT REQUIREMENTS

The G6 implementation MUST NOT accept caller assertions as substitutes
for authoritative reuse inputs.

The following must originate from their frozen trusted boundaries:

- evidence bundle identity;
- evidence origin/integrity verification;
- original evaluation record;
- canonical context bindings;
- original dependency closure;
- dependency-completeness assurance;
- authority derivation and lineage;
- current policy/schedule/grant/authority state;
- trusted current time;
- governed MAX_EVIDENCE_REUSE_WINDOW.

Caller-supplied values may request reuse but MUST NOT establish that
reuse is safe.

---

## 6. OUT OF SCOPE FOR THIS CONTRACT

G6 does NOT yet define:

- Python implementation structure;
- class/dataclass representation;
- persistence schema;
- cache implementation;
- API transport;
- model/AI integration;
- final authorization semantics;
- execution behavior after the current deterministic evaluation.

Those belong to later enforcement work.

---

## 7. RED-FIRST REQUIREMENT

The executable G6 regression MUST be introduced before reuse
enforcement implementation.

Expected sequence:

```text
frozen G6 contract
        ↓
executable G6 fixtures
        ↓
meaningful RED
        ↓
minimal reuse enforcement
        ↓
GREEN
```

A RED run is meaningful only when failure is caused by missing reuse
enforcement behavior, not by syntax, import, fixture-construction, or
CI wiring errors.

---

## Freeze Status

Applicable Evidence Reuse Policy v0.1
→ DESIGN FROZEN

G6A
→ FREEZE READY

G6B
→ FREEZE READY

G6C
→ FREEZE READY

G6D
→ FREEZE READY

G6E
→ FREEZE READY

G6F
→ FREEZE READY

G6G
→ FREEZE READY

G6H1–G6H3
→ FREEZE READY

Classification Rule / Outcome Precedence
→ FREEZE READY

G6 Contract Scope
→ DESIGN IN PROGRESS
→ NOT YET FROZEN

G6 Executable Fixtures
→ NOT CREATED

G6 CI
→ NOT WIRED

Python Reuse Enforcement
→ NOT STARTED

TRUSTED_CURRENT_TIME_BOUNDARY_FROZEN
≠
G6_READY
