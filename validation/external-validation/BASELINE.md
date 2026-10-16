# External validation exception baseline

Implementation revision: 2340d34.
Command:
PYTHONPATH=. python validation/external-validation/baseline.py

The v2 control matched its complete expected result.
Removing adoption raised ValueError: Adoption record missing.
Removing output raised ValueError: Output record missing.
With valid control input, an injected _record fault raised
ValueError: Injected checker fault.
All three exceptional inputs remained unchanged.

baseline.json preserves the full revision, inputs and observations.
baseline.py reproduces the experiment from the repository root.

The exception type alone does not distinguish record absence
from an execution fault. Messages differ; causes are not identical.
No classification is inferred from those messages.

This is a checker exception baseline, not differential RED
for the proposed wrapper or support for the nine external cases.
No institutional data or claim change is involved.
