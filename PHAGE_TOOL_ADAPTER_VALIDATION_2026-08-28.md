# PHAGE Tool Adapter Validation Record — 2026-08-28

## Status

VALIDATED — SANDBOX TOOL-ADAPTER EFFECT BOUNDARY

This record freezes the observed validation result of the PHAGE sandbox tool-adapter boundary.

It records only behavior directly exercised by the regression workflow.

It does not establish production readiness, universal tool safety, or complete PHAGE governance coverage.

---

## Validation target

Branch:

`phage-tool-adapter`

Components under validation:

- `phage_gateway.py`
- `phage_executor.py`
- `phage_tool_adapter.py`
- `test_phage_gateway.py`
- `test_phage_executor.py`
- `test_phage_tool_adapter.py`
- `.github/workflows/phage-gateway.yml`
---

## Core effect-boundary invariant

```text
ALLOW => ADAPTER_INVOKED => EFFECT_OBSERVED
BLOCK => ADAPTER_NOT_INVOKED => NO_EFFECT
```

An action may reach the sandbox tool adapter only after the PHAGE Gateway returns an explicit `ALLOW` decision.

A `BLOCK` decision must prevent adapter invocation and therefore prevent the adapter's observable sandbox effect.

---

## Validated cases

### ALLOW

A trusted instruction with valid delegated scope produced:
```text
ALLOW
=> adapter invoked
=> observable adapter effect
```

Observed regression result:

```text
PASS: ALLOW produces observable adapter effect
```

### Unverified instruction provenance

A principal-attribution mismatch produced a provenance failure and prevented adapter invocation.

Observed regression result:

```text
PASS: provenance BLOCK produces no adapter effect
```

The validated failure condition is:

`UNVERIFIED_INSTRUCTION_PROVENANCE`
### Authority scope mismatch

A valid instruction principal requesting a target outside delegated scope was blocked before adapter invocation.

Observed regression result:

```text
PASS: scope BLOCK produces no adapter effect
```

The validated failure condition is:

`AUTHORITY_SCOPE_MISMATCH`

These two BLOCK conditions remain semantically distinct even though both prevent downstream effects.

---

## GitHub Actions validation

Workflow:

`PHAGE Gateway`

Observed tool-adapter regression output:
```text
PASS: ALLOW produces observable adapter effect
PASS: provenance BLOCK produces no adapter effect
PASS: scope BLOCK produces no adapter effect
PHAGE tool-adapter regression PASS: 3 / 3.
```

Result:

`PASS — 3 / 3`

---

## What this validation establishes

Within the tested MVP implementation, this validation establishes that:

1. an allowed action reaches the sandbox adapter;
2. adapter invocation creates an independently observable effect;
3. a provenance BLOCK prevents adapter invocation;
4. an authority-scope BLOCK prevents adapter invocation;
5. the two governance failure conditions remain separately classified;
6. the execution decision and downstream effect boundary are independently observable.

The validation therefore tests actual adapter invocation state rather than relying only on the Gateway's declared decision.
---

## Important provenance limitation

The current provenance check establishes principal attribution by comparing:

`instruction_principal`

and:

`principal`

The `instruction_source` field is carried by the action envelope but is not independently authenticated or validated by this test.

Therefore this validation does not establish trusted source-channel provenance.

---

## What this validation does not establish

This validation does not establish:

- production readiness;
- cryptographic instruction provenance;
- identity-provider integration;
- authenticated source-channel provenance;
- durable authorization storage;
- MCP enforcement;
- arbitrary third-party tool safety;
- resistance to all prompt-injection attacks;
- distributed or multi-agent authorization propagation;
- persistence, replay protection, or revocation semantics;
- complete PHAGE governance coverage.

No broader claim should be inferred from this validation record.
---

## Validation disposition

```text
PHAGE_TOOL_ADAPTER_EFFECT_BOUNDARY = VALIDATED
TOOL_ADAPTER_REGRESSION = PASS_3_OF_3

ALLOW => ADAPTER_INVOKED => EFFECT_OBSERVED
BLOCK => ADAPTER_NOT_INVOKED => NO_EFFECT

UNVERIFIED_INSTRUCTION_PROVENANCE
!=
AUTHORITY_SCOPE_MISMATCH
```

This record freezes the validated sandbox tool-adapter boundary.

Further capabilities should be introduced through separate tests and validation records rather than by broadening the meaning of this result.
