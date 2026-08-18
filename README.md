# PHAGE Evidence Engine — Research Preview

> **Break PHAGE.**  
> Run your workflow. Find a case where PHAGE says `SATISFIED` but you know the structure is incomplete. Send us the fixture.

**Status:** Research prototype. Not an authorization system.

PHAGE currently evaluates structural discrepancies between externally declared expected observations (E) and supplied observations (O). It does **not** determine truth, establish authority, validate context correctness, or authorize execution.

## Research boundaries

- `SATISFIED` does not mean safe, true, authorized, or trustworthy.
- `UNRESOLVED` is a first-class state and must never silently collapse to `SATISFIED`.
- The engine does not originate Expected Observations.
- Authority, Context correctness, Expectation Capture resistance, meta-governance, production reliability, and scale remain under research.

See [`CLAIMS_STATUS.md`](CLAIMS_STATUS.md) before using or describing PHAGE.

## Repository layout

- `phage/` — reference implementation (placeholder for Research Preview code)
- `fixtures/death/` — validated death fixtures only
- `fixtures/candidate/` — hypotheses awaiting differential execution
- `fixtures/challenge/` — community challenge guidance
- `failure-report/` — redacted challenge package template
- `docs/` — protocol and architecture notes
- `examples/` — synthetic/redacted examples only

## Falsification workflow

1. Run supplied fixtures.
2. Model your workflow using synthetic or redacted data.
3. If PHAGE produces a structurally wrong result, prepare a Challenge Fixture.
4. Review and redact the package locally.
5. Submit the reproducible challenge for review.
6. A Challenge Fixture becomes a Validated Death Fixture only after reproduction and classification.

**UserSubmittedFixture != ValidatedDeathFixture**

## Intended CLI surface

```bash
phage validate-fixture fixture.yaml
phage assess fixture.yaml
phage explain <finding-id>
phage report-failure fixture.yaml
```

These commands describe the intended Research Preview interface; do not treat unimplemented commands as shipped functionality.

## Local-first principle

PHAGE Research Preview is intended to operate locally. Do not submit production secrets, PII, credentials, classified information, customer data, or sensitive operational logs to public issues.

## Distribution

Initial distribution target:

1. Public GitHub repository
2. Versioned GitHub Release (`v0.1.0-research-preview`)
3. PyPI only after the CLI/package interface has been externally tested and stabilized

## Core discipline

> **Ambition may lead evidence; claims may not.**

> **Maturity follows demonstrated capability, not threat coverage by association.**
