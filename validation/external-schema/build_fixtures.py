"""Build synthetic multi-decision inputs; no production imports."""

import copy
import json
from pathlib import Path

DESTINATION = Path("fixtures/external-schema")
control = json.loads(
    Path("fixtures/decision-input-v2/control.json").read_text()
)
original = control["input"]

def renamed(value, identities):
    if isinstance(value, dict):
        return {
            identities.get(key, key): renamed(child, identities)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [renamed(child, identities) for child in value]
    if isinstance(value, str):
        return identities.get(value, value)
    return value

registry = {}
decisions = []
expected_results = {}

for index, suffix in enumerate(("A", "B/~", "C"), start=1):
    identities = {
        identifier: identifier + "-" + suffix
        for identifier in original["registry"]
    }
    decision_id = f"DECISION-{index:02d}"
    identities["DECISION-01"] = decision_id
    copied = renamed(original, identities)
    adoption_id = copied["adoption_id"]
    _overlap = set(registry).intersection(copied["registry"])
    assert not _overlap
    registry.update(copied["registry"])
    decisions.append({
        "decision_id": decision_id,
        "adoption_id": adoption_id,
        "source_path": f"/decisions/{index - 1}/adoption_id",
    })
    if index < 3:
        expected_results[decision_id] = renamed(
            control["expected"], identities
        )
    else:
        del registry[adoption_id]

snapshot = {
    "snapshot_id": "SYNTHETIC-BATCH-01",
    "payload": {
        "decisions": copy.deepcopy(decisions),
        "registry": registry,
        "canonical_identities": copy.deepcopy(
            original["canonical_identities"]
        ),
    },
}
assert len(decisions) == 3
assert decisions[2]["adoption_id"] not in registry

schema = {
    "schema_revision": "SYNTHETIC-SCHEMA-01",
    "inventory": {
        "source_path": "/decisions",
        "decision_id_field": "decision_id",
        "adoption_ref_field": "adoption_id",
    },
    "registry_path": "/registry",
    "canonical_identities_path": "/canonical_identities",
    "selectors": {
        "adoption": {
            "from": "inventory", "reference": "adoption_id",
        },
        "output": {
            "from": "adoption", "reference": "/output_binding/output_id",
        },
        "presentation": {
            "from": "adoption", "reference": "/presentation_ref",
        },
        "source": {
            "from": "output", "reference": "/citations",
            "member_reference": "source_id",
        },
        "verification": {
            "from": "output", "reference": "/citations",
            "member_reference": "verification_ref",
        },
    },
    "rules": [],
}
inventory = {
    "inventory_revision": "SYNTHETIC-INVENTORY-01",
    "source_snapshot_id": snapshot["snapshot_id"],
    "entries": copy.deepcopy(decisions),
    "coverage": "export_only",
    "exclusions": ["Decisions omitted from the supplied export"],
    "evidence_refs": [],
}

fields_by_kind = {
    "adoption": {
        "id": "string", "kind": "string",
        "decision_maker": "string", "decision_context": "string",
        "output_binding": "object", "adopted_portions": "array",
        "presentation_ref": "string",
    },
    "output": {
        "id": "string", "kind": "string", "version": "version",
        "producer": "string", "content": "array", "citations": "array",
    },
    "presentation": {
        "id": "string", "kind": "string", "recorder": "string",
        "recipient": "string", "decision_context": "string",
        "output_binding": "object", "presented_portions": "array",
    },
    "source": {
        "id": "string", "kind": "string",
        "version": "version", "content": "string",
    },
    "verification": {
        "id": "string", "kind": "string", "recorder": "string",
        "output_binding": "object", "portion_id": "string",
        "portion_text": "string", "source_id": "string",
        "source_version": "version", "source_content": "string",
    },
}
# "version" permits a nonempty string or an integer, excluding bool.
# Binding objects and arrays also require checker-input validation.
# Optional references may be null; that means no asserted member.

for kind, fields in fields_by_kind.items():
    declarations = {"": "object", **fields}
    for field, target_type in declarations.items():
        suffix = "/" + field if field else ""
        optional_ref = (kind, field) == ("adoption", "presentation_ref")
        rule = {
            "rule_id": kind + "." + (field or "root"),
            "kind": kind,
            "selector": kind,
            "source_template": "/registry/{record_id}" + suffix,
            "target_template": "/registry/{record_id}" + suffix,
            "mapping_status": "MAPPABLE",
            "transformation": "identity",
            "target_type": target_type,
            "nullable": optional_ref,
            "required_for_checker": (
                kind in ("adoption", "output") and not optional_ref
            ),
            "absence_semantics": {
                "missing": "scoped_evidence",
                "null": "value" if optional_ref else "scoped_evidence",
                "empty": "value",
            },
        }
        schema["rules"].append(rule)

assert len({rule["rule_id"] for rule in schema["rules"]}) == len(schema["rules"])
assert all(
    "{record_id}" in rule["target_template"]
    for rule in schema["rules"]
)

expectations = {
    "checker_results": expected_results,
    "checker_calls_by_decision": {
        "DECISION-01": 1,
        "DECISION-02": 1,
        "DECISION-03": 0,
    },
    "blocked_decisions": ["DECISION-03"],
    "missing_root": {
        "decision_id": "DECISION-03",
        "rule_id": "adoption.root",
        "target_path": "/registry/ADOPT-01-C",
        "code": "SOURCE_COVERAGE_UNKNOWN",
        "evidence_refs": [],
    },
    "aggregate_pass_field_permitted": False,
}
artifacts = {
    "schema.json": schema,
    "multi_decision_snapshot.json": snapshot,
    "inventory.json": inventory,
    "expected.json": expectations,
    "coverage_evidence.json": [],
}
for filename, value in artifacts.items():
    (DESTINATION / filename).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    )
print(f"Wrote {len(artifacts)} artifacts; {len(schema['rules'])} schema rules.")
