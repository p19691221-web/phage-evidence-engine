# Contributing to PHAGE Research Preview

The highest-value contribution is a reproducible case showing that PHAGE's structural assessment is wrong or incomplete.

## Preferred contributions

- False `SATISFIED`
- False Gap
- False `UNRESOLVED`
- Missing open dependency
- Wrong dependency ordering
- Expectation provenance failure
- Schema cannot represent a workflow
- New failure shape

## Challenge Fixture process

1. Reproduce locally.
2. Minimize the fixture.
3. Remove domain-specific details where possible.
4. Redact all sensitive information.
5. Complete `failure-report/REPORT.md`.
6. Include actual and expected engine outputs.
7. Submit as a **Challenge Fixture**.

A submitted challenge is not automatically a Death Fixture. Promotion requires reproduction, source/assumption review, and failure classification.

## Anti-overclaim rule

Do not describe a fixture as proving more than it tests. In particular, provenance failure does not prove malicious capture, and a missing observation does not prove suppression.
