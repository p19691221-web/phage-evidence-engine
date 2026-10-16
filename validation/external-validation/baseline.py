import copy
import json
import subprocess
from pathlib import Path
from unittest.mock import patch
import decision_input_traceability as checker

fixture = json.loads(
    Path("fixtures/decision-input-v2/control.json").read_text()
)
original = fixture["input"]
revision = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], text=True
).strip()
observations = []

for case in ("missing_adoption", "missing_output", "checker_fault"):
    inputs = copy.deepcopy(original)
    if case == "missing_adoption":
        del inputs["registry"][inputs["adoption_id"]]
    elif case == "missing_output":
        adoption = inputs["registry"][inputs["adoption_id"]]
        del inputs["registry"][adoption["output_binding"]["output_id"]]
    before = copy.deepcopy(inputs)
    try:
        if case == "checker_fault":
            with patch.object(checker, "_record",
                              side_effect=ValueError("Injected checker fault")):
                checker.inspect_adoption(**inputs)
        else:
            checker.inspect_adoption(**inputs)
    except Exception as exc:
        observations.append({
            "case": case, "type": type(exc).__name__,
            "message": str(exc), "input": before,
            "input_unchanged": inputs == before,
        })
    else:
        raise AssertionError(f"{case}: expected exception")

control = copy.deepcopy(original)
assert checker.inspect_adoption(**control) == fixture["expected"]
assert control == original
assert [item["type"] for item in observations] == ["ValueError"] * 3
assert [item["message"] for item in observations] == [
    "Adoption record missing",
    "Output record missing",
    "Injected checker fault",
]
assert all(item["input_unchanged"] for item in observations)

report = {
    "revision": revision,
    "control_matches_expected": True,
    "observations": observations,
    "scope": "Exception-type baseline, not wrapper differential RED",
}
Path("validation/external-validation/baseline.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n"
)
for item in observations:
    print(f'{item["case"]}: {item["type"]}: {item["message"]}')
print("Control matched; all three inputs unchanged.")
