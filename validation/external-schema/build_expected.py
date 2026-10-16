"""Freeze test-owned expansion expectations without production imports."""

import json
from pathlib import Path

ROOT = Path("fixtures/external-schema")
schema = json.loads((ROOT / "schema.json").read_text())
snapshot = json.loads((ROOT / "multi_decision_snapshot.json").read_text())
inventory = json.loads((ROOT / "inventory.json").read_text())

def escape(identifier):
    return identifier.replace("~", "~0").replace("/", "~1")

subjects = {
    "DECISION-01": {
        "adoption": ["ADOPT-01-A"], "output": ["OUT-01-A"],
        "presentation": ["PRESENT-01-A"], "source": ["SOURCE-01-A"],
        "verification": ["VERIFY-01-A"],
    },
    "DECISION-02": {
        "adoption": ["ADOPT-01-B/~"], "output": ["OUT-01-B/~"],
        "presentation": ["PRESENT-01-B/~"], "source": ["SOURCE-01-B/~"],
        "verification": ["VERIFY-01-B/~"],
    },
    "DECISION-03": {
        "adoption": ["ADOPT-01-C"], "output": [],
        "presentation": [], "source": [], "verification": [],
    },
}
expansion = []
selections = []

for decision_id, selected in sorted(subjects.items()):
    for kind, record_ids in sorted(selected.items()):
        blocked = decision_id == "DECISION-03" and kind != "adoption"
        selections.append({
            "decision_id": decision_id,
            "selector": kind,
            "selection_count": len(record_ids),
            "status": "blocked_by_ancestor" if blocked else "resolved",
            "blocked_by": "/registry/ADOPT-01-C" if blocked else None,
        })
        for record_id in record_ids:
            root = "/registry/" + escape(record_id)
            missing_root = decision_id == "DECISION-03"
            for rule in schema["rules"]:
                if rule["kind"] != kind:
                    continue
                target = rule["target_template"].replace(
                    "{record_id}", escape(record_id)
                )
                expansion.append({
                    "schema_revision": schema["schema_revision"],
                    "source_snapshot_id": snapshot["snapshot_id"],
                    "inventory_revision": inventory["inventory_revision"],
                    "decision_id": decision_id,
                    "rule_id": rule["rule_id"],
                    "record_id": record_id,
                    "source_path": rule["source_template"].replace(
                        "{record_id}", escape(record_id)
                    ),
                    "target_path": target,
                    "status": (
                        "missing_root" if missing_root and target == root else
                        "blocked_by_ancestor" if missing_root else "resolved"
                    ),
                    "blocked_by": root if missing_root and target != root else None,
                })

expansion.sort(key=lambda row: (
    row["decision_id"], row["rule_id"], row["target_path"]
))
selections.sort(key=lambda row: (row["decision_id"], row["selector"]))
rules = {rule["rule_id"]: rule for rule in schema["rules"]}
affected = [
    {
        "rule_id": row["rule_id"],
        "target_path": row["target_path"],
        "required_for_checker": rules[row["rule_id"]]["required_for_checker"],
    }
    for row in expansion
    if row["decision_id"] == "DECISION-03"
    and row["status"] == "blocked_by_ancestor"
]
finding = {
    "code": "SOURCE_COVERAGE_UNKNOWN",
    "decision_id": "DECISION-03",
    "rule_id": "adoption.root",
    "target_path": "/registry/ADOPT-01-C",
    "source_snapshot_id": snapshot["snapshot_id"],
    "schema_revision": schema["schema_revision"],
    "inventory_revision": inventory["inventory_revision"],
    "evidence_refs": [],
    "explanation": "Source absence is not established.",
    "affected_targets": affected,
}
for filename, value in {
    "expected_expansion.json": expansion,
    "expected_selections.json": selections,
    "expected_findings.json": [finding],
}.items():
    (ROOT / filename).write_text(json.dumps(value, indent=2) + "\n")
print(f"Expected: {len(expansion)} expansions, {len(selections)} selections, 1 finding.")
