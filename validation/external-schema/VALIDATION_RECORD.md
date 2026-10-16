# Synthetic schema manifest validation

Contract: PR #129, merged at e0894ce.
Frozen tests: d8c6ffa and e825f73; draft PR #130.

Availability baseline:
1 failed, 1 passed, 19 skipped.
The nineteen behavioral cases did not execute.
This is not nineteen differential RED failures.

Initial implementation: first-execution.log, 21 passed.
Additional field-mapping test exposed ignored source_template.
Concrete RED checkpoint: 522325a.
field-mapping-red.log: 1 failed, 21 deselected.
This RED applies only to field mapping in that implementation.

After applying individual field mappings:
field-mapping-green.log: 22 passed, no skips.
green-regression.log: 67 passed, no skips.
This includes 22 schema checks and 45 existing regressions.

Executed synthetic cases cover reusable rules across decisions,
concrete escaping/renaming, deterministic expansion, decision
isolation, grouped missing roots, field findings, shared sources,
zero selections, inventory boundaries and partial execution errors.

Support is limited to the tested schema and identity mappings.
No arbitrary-schema, scale, institutional or source-authenticity
validation is established. Coverage assertions remain supplied
evidence. Existing historical fixtures and claims are unchanged.

CI now includes test_external_schema.py.
Remote decision-input CI: SUCCESS.
PR #131 head: e19830abea58e99bf58bf7512bfb760ffdae71e5.
Evidence: https://github.com/p19691221-web/phage-evidence-engine/actions/runs/38858240032/job/116834415112
All 12 PR checks were successful at this head.
