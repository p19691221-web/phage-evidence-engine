import copy
import json
from pathlib import Path

destination = Path("fixtures/external-validation")
control = json.loads(
    Path("fixtures/decision-input-v2/control.json").read_text()
)
inputs = copy.deepcopy(control["input"])

snapshot = {
    "snapshot_id": "SYNTHETIC-EXPORT-01",
    "payload": {
        "export": copy.deepcopy(inputs),
    },
}
manifest = {
    "manifest_revision": "SYNTHETIC-MANIFEST-01",
    "source_snapshot_id": snapshot["snapshot_id"],
    "reviewed_by": "synthetic-test-author",
    "reviewed_at": "2026-10-16T00:00:00Z",
    "evidence": [],
    "mappings": [],
}
cases = []

def pointer_part(value):
    return str(value).replace("~", "~0").replace("/", "~1")

adoption_id = inputs["adoption_id"]
output_id = inputs["registry"][adoption_id]["output_binding"]["output_id"]
required_roots = {
    "/adoption_id", "/canonical_identities",
    f"/registry/{pointer_part(adoption_id)}",
    f"/registry/{pointer_part(output_id)}",
}

def add_mappings(value, path=""):
    required = any(
        path == root or path.startswith(root + "/")
        for root in required_roots
    )
    target_type = (
        "object" if isinstance(value, dict) else
        "array" if isinstance(value, list) else
        "string" if isinstance(value, str) else
        "integer" if isinstance(value, int) else "null"
    )
    if path and (path in required_roots or not isinstance(value, dict)):
        manifest["mappings"].append({
            "target_path": path, "required_for_checker": required,
            "source_path": "/export" + path,
            "mapping_status": "MAPPABLE",
            "transformation": "identity", "target_type": target_type,
            "absence_semantics": {
                "missing": "unknown", "null": "unknown", "empty": "value"
            },
            "coverage_scope": path, "exclusions": [],
            "coverage_evidence_refs": [],
        })
    if isinstance(value, dict):
        for key, child in value.items():
            add_mappings(child, path + "/" + pointer_part(key))

add_mappings(inputs)

def new_case(name):
    case = {
        "name": name,
        "source_snapshot": copy.deepcopy(snapshot),
        "manifest": copy.deepcopy(manifest),
        "adapter_mode": "identity",
        "checker_mode": "real",
        "expected_findings": [],
    }
    cases.append(case)
    return case

def declare_absence(case, root):
    evidence_id = "SYNTHETIC-ABSENCE-" + str(len(case["manifest"]["evidence"]))
    case["manifest"]["evidence"].append({
        "evidence_id": evidence_id,
        "reference": "synthetic://scoped-source-observation",
        "asserted_by": "synthetic-source-custodian",
        "asserted_at": "2026-10-16T00:00:00Z",
        "coverage_scope": root,
        "includes_descendants": True,
        "assertion": "source_record_absent",
        "synthetic": True,
    })
    for mapping in case["manifest"]["mappings"]:
        path = mapping["target_path"]
        if path == root or path.startswith(root + "/"):
            mapping["absence_semantics"]["missing"] = "source_absent"
            mapping["coverage_evidence_refs"] = [evidence_id]

adoption_path = "/registry/" + pointer_part(adoption_id)
output_path = "/registry/" + pointer_part(output_id)
version_path = output_path + "/version"
new_case("01_control")

case = new_case("02_absent_adoption")
del case["source_snapshot"]["payload"]["export"]["registry"][adoption_id]
declare_absence(case, adoption_path)

case = new_case("03_absent_output")
del case["source_snapshot"]["payload"]["export"]["registry"][output_id]
declare_absence(case, output_path)

case = new_case("04_unmappable_version")
del case["source_snapshot"]["payload"]["export"]["registry"][output_id]["version"]
for mapping in case["manifest"]["mappings"]:
    if mapping["target_path"] == version_path:
        mapping.update({
            "mapping_status": "UNMAPPABLE",
            "source_path": None,
            "transformation": None,
            "reason": "Synthetic export has no source version identity",
        })

unknown = new_case("05_export_omission_unknown")
del unknown["source_snapshot"]["payload"]["export"]["registry"][adoption_id]

confirmed = new_case("06_same_export_confirmed_absent")
confirmed["source_snapshot"] = copy.deepcopy(unknown["source_snapshot"])
declare_absence(confirmed, adoption_path)

assert unknown["source_snapshot"] == confirmed["source_snapshot"]

case = new_case("07_invalid_adapter_output")
case["adapter_mode"] = "invalid_registry_kind"
case["expected_error"] = {
    "stage": "input_validation",
    "code": "ADAPTED_INPUT_INVALID",
    "checker_calls": 0,
}

case = new_case("08_checker_execution_fault")
case["checker_mode"] = "raise_value_error"
case["expected_error"] = {
    "stage": "checker_execution",
    "code": "CHECKER_EXECUTION_ERROR",
    "checker_calls": 1,
}

case = new_case("09_coexisting_findings")
del case["source_snapshot"]["payload"]["export"]["registry"][adoption_id]
declare_absence(case, adoption_path)
exported_output = case["source_snapshot"]["payload"]["export"]["registry"][output_id]
del exported_output["version"]
del exported_output["producer"]

for mapping in case["manifest"]["mappings"]:
    if mapping["target_path"] == version_path:
        mapping.update({
            "mapping_status": "UNMAPPABLE",
            "source_path": None,
            "transformation": None,
            "reason": "Synthetic export has no source version identity",
        })

explanations = {
    "EXTERNAL_RECORD_ABSENT": "Scoped evidence establishes source absence.",
    "ADAPTER_UNMAPPABLE": "Frozen mapping declares no faithful representation.",
    "SOURCE_COVERAGE_UNKNOWN": "Source absence is not established.",
}

def expect(case, code, root, descendants=False):
    for mapping in case["manifest"]["mappings"]:
        path = mapping["target_path"]
        if path == root or (descendants and path.startswith(root + "/")):
            case["expected_findings"].append({
                "code": code,
                "target_path": path,
                "source_snapshot_id": case["source_snapshot"]["snapshot_id"],
                "manifest_revision": case["manifest"]["manifest_revision"],
                "evidence_refs": list(mapping["coverage_evidence_refs"]),
                "explanation": explanations[code],
            })

expect(cases[1], "EXTERNAL_RECORD_ABSENT", adoption_path, True)
expect(cases[2], "EXTERNAL_RECORD_ABSENT", output_path, True)
expect(cases[3], "ADAPTER_UNMAPPABLE", version_path)
expect(cases[4], "SOURCE_COVERAGE_UNKNOWN", adoption_path, True)
expect(cases[5], "EXTERNAL_RECORD_ABSENT", adoption_path, True)
expect(cases[8], "EXTERNAL_RECORD_ABSENT", adoption_path, True)
expect(cases[8], "ADAPTER_UNMAPPABLE", version_path)
expect(cases[8], "SOURCE_COVERAGE_UNKNOWN", output_path + "/producer")

for case in cases:
    case["expected_findings"].sort(key=lambda item: item["target_path"])

for index, case in enumerate(cases):
    if "expected_error" in case:
        case["expected_adapter_calls"] = 1
    else:
        invoked = index == 0
        case["expected_adapter_calls"] = int(invoked)
        case["expected_checker_calls"] = int(invoked)
        case["expected_record"] = {
            "manifest_revision": case["manifest"]["manifest_revision"],
            "source_snapshot_id": case["source_snapshot"]["snapshot_id"],
            "findings": copy.deepcopy(case["expected_findings"]),
            "checker_invoked": invoked,
            "checker_result": copy.deepcopy(control["expected"]) if invoked else None,
        }
    path = destination / (case["name"] + ".json")
    path.write_text(json.dumps(case, indent=2, ensure_ascii=False) + "\n")

assert len(cases) == 9
assert cases[4]["source_snapshot"] == cases[5]["source_snapshot"]
assert cases[4]["expected_findings"] != cases[5]["expected_findings"]
print("Wrote 9 synthetic cases; cases 5/6 have identical snapshots.")
