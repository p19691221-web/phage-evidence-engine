import copy
import importlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from decision_input_traceability import inspect_adoption

ROOT = Path("fixtures/external-schema")

def load(name):
    return json.loads((ROOT / name).read_text())

def entry_point():
    if importlib.util.find_spec("external_schema_validation") is None:
        return None
    return getattr(
        importlib.import_module("external_schema_validation"),
        "run_schema_validation", None,
    )

def require_entry():
    run = entry_point()
    if not callable(run):
        pytest.skip("Schema entry absent; behavioral case NOT EXECUTED")
    return run

def test_schema_entry_point_exists():
    assert callable(entry_point()), "Schema validation entry point absent"

def arguments():
    return {
        "source_snapshot": load("multi_decision_snapshot.json"),
        "schema": load("schema.json"),
        "inventory": load("inventory.json"),
        "coverage_evidence": load("coverage_evidence.json"),
    }

def expected_batch():
    frozen = load("expected.json")
    decisions = []
    for entry in load("inventory.json")["entries"]:
        identifier = entry["decision_id"]
        invoked = frozen["checker_calls_by_decision"][identifier] == 1
        decisions.append({
            "decision_id": identifier,
            "status": "evaluated" if invoked else "blocked",
            "checker_invoked": invoked,
            "checker_result": frozen["checker_results"].get(identifier),
        })
    return {
        "schema_revision": load("schema.json")["schema_revision"],
        "source_snapshot_id": load("inventory.json")["source_snapshot_id"],
        "inventory_revision": load("inventory.json")["inventory_revision"],
        "inventory_coverage": {
            "coverage": "export_only",
            "exclusions": ["Decisions omitted from the supplied export"],
            "evidence_refs": [],
        },
        "expansion": load("expected_expansion.json"),
        "selections": load("expected_selections.json"),
        "findings": load("expected_findings.json"),
        "decisions": decisions,
    }

def execute(run, kwargs):
    before = copy.deepcopy(kwargs)
    checker = Mock(side_effect=inspect_adoption)
    failures = []
    try:
        result = run(**kwargs, checker=checker,
                     failure_sink=failures.append)
    finally:
        assert kwargs == before, "Schema execution mutated inputs"
    assert failures == []
    return result, checker

def assert_decision_calls(checker, inventory):
    expected = load("expected.json")["checker_calls_by_decision"]
    actual = [
        call.kwargs["adoption_id"] for call in checker.call_args_list
    ]
    assert checker.call_count == sum(expected.values())
    for entry in inventory["entries"]:
        assert actual.count(entry["adoption_id"]) == expected[entry["decision_id"]]

def test_multi_decision_batch():
    run = require_entry()
    kwargs = arguments()
    result, checker = execute(run, kwargs)
    assert result == expected_batch()
    assert_decision_calls(checker, kwargs["inventory"])

def test_registry_order_does_not_change_batch():
    run = require_entry()
    kwargs = arguments()
    registry = kwargs["source_snapshot"]["payload"]["registry"]
    kwargs["source_snapshot"]["payload"]["registry"] = dict(
        reversed(list(registry.items()))
    )
    result, checker = execute(run, kwargs)
    assert result == expected_batch()
    assert_decision_calls(checker, kwargs["inventory"])

def test_frozen_fixture_inventory():
    kwargs = arguments()
    assert len(kwargs["schema"]["rules"]) == 38
    assert len(kwargs["inventory"]["entries"]) == 3
    assert len(load("expected_expansion.json")) == 84
    assert len(load("expected_selections.json")) == 15
    assert len(load("expected_findings.json")) == 1

def replace_exact(value, replacements):
    if isinstance(value, dict):
        return {
            replacements.get(key, key): replace_exact(child, replacements)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [replace_exact(child, replacements) for child in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value

def test_add_decision_without_schema_changes():
    run = require_entry()
    kwargs = arguments()
    frozen_schema = copy.deepcopy(kwargs["schema"])
    payload = kwargs["source_snapshot"]["payload"]
    identifiers = [
        "ADOPT-01-A", "OUT-01-A", "PRESENT-01-A",
        "SOURCE-01-A", "VERIFY-01-A",
    ]
    replacements = {item: item[:-1] + "D" for item in identifiers}
    replacements["DECISION-01"] = "DECISION-04"
    records = {item: payload["registry"][item] for item in identifiers}
    payload["registry"].update(replace_exact(records, replacements))
    entry = {
        "decision_id": "DECISION-04",
        "adoption_id": "ADOPT-01-D",
        "source_path": "/decisions/3/adoption_id",
    }
    payload["decisions"].append(copy.deepcopy(entry))
    kwargs["inventory"]["entries"].append(copy.deepcopy(entry))
    expected = expected_batch()
    path_replacements = dict(replacements)
    for old, new in replacements.items():
        if old.startswith("DECISION-"):
            continue
        for rule in frozen_schema["rules"]:
            old_path = rule["target_template"].replace("{record_id}", old)
            new_path = rule["target_template"].replace("{record_id}", new)
            path_replacements[old_path] = new_path
    for field in ("expansion", "selections", "decisions"):
        first = [
            row for row in expected[field]
            if row["decision_id"] == "DECISION-01"
        ]
        expected[field].extend(replace_exact(first, path_replacements))
    expected["expansion"].sort(key=lambda row: (
        row["decision_id"], row["rule_id"], row["target_path"]
    ))
    expected["selections"].sort(key=lambda row: (
        row["decision_id"], row["selector"]
    ))
    expected["decisions"].sort(key=lambda row: row["decision_id"])
    result, checker = execute(run, kwargs)
    assert result == expected
    assert kwargs["schema"] == frozen_schema
    assert checker.call_count == 3
    called = [call.kwargs["adoption_id"] for call in checker.call_args_list]
    assert called == ["ADOPT-01-A", "ADOPT-01-B/~", "ADOPT-01-D"]

def test_same_export_with_scoped_absence_evidence():
    run = require_entry()
    kwargs = arguments()
    frozen_snapshot = copy.deepcopy(kwargs["source_snapshot"])
    evidence = {
        "evidence_id": "SYNTHETIC-ABSENCE-C",
        "reference": "synthetic://custodian/absent-adoption",
        "asserted_by": "synthetic-source-custodian",
        "asserted_at": "2026-10-16T00:00:00Z",
        "source_snapshot_id": frozen_snapshot["snapshot_id"],
        "decision_id": "DECISION-03",
        "coverage_scope": "/registry/ADOPT-01-C",
        "includes_descendants": True,
        "assertion": "source_record_absent",
        "synthetic": True,
    }
    kwargs["coverage_evidence"] = [evidence]
    expected = expected_batch()
    finding = expected["findings"][0]
    finding["code"] = "EXTERNAL_RECORD_ABSENT"
    finding["evidence_refs"] = [evidence["evidence_id"]]
    finding["explanation"] = "Scoped evidence establishes source absence."
    result, checker = execute(run, kwargs)
    assert result == expected
    assert kwargs["source_snapshot"] == frozen_snapshot
    assert_decision_calls(checker, kwargs["inventory"])

@pytest.mark.parametrize("fault", [
    "unknown_variable", "partial_variable",
    "bad_pointer_escape", "duplicate_target",
])
def test_invalid_schema_fails_before_checker(fault):
    run = require_entry()
    kwargs = arguments()
    rule = kwargs["schema"]["rules"][0]
    if fault == "unknown_variable":
        rule["target_template"] = "/registry/{unknown}/id"
    elif fault == "partial_variable":
        rule["target_template"] = "/registry/prefix-{record_id}/id"
    elif fault == "bad_pointer_escape":
        rule["target_template"] = "/registry/{record_id}/bad~2field"
    else:
        duplicate = copy.deepcopy(rule)
        duplicate["rule_id"] = "duplicate.rule"
        kwargs["schema"]["rules"].append(duplicate)
    before = copy.deepcopy(kwargs)
    checker = Mock(side_effect=inspect_adoption)
    failures = []
    module = importlib.import_module("external_schema_validation")
    with pytest.raises(module.SchemaValidationError) as caught:
        run(**kwargs, checker=checker, failure_sink=failures.append)
    error = caught.value
    assert error.stage == "schema_validation"
    assert error.code == "SCHEMA_INVALID"
    assert isinstance(error.__cause__, Exception)
    assert checker.call_count == 0
    assert failures == [error.failure_record]
    assert kwargs == before

@pytest.mark.parametrize("record_id", ["ADOPT-01-A", "OUT-01-A"])
def test_wrong_kind_root_is_execution_failure(record_id):
    run = require_entry()
    kwargs = arguments()
    registry = kwargs["source_snapshot"]["payload"]["registry"]
    registry[record_id]["kind"] = "source"
    before = copy.deepcopy(kwargs)
    checker = Mock(side_effect=inspect_adoption)
    failures = []
    module = importlib.import_module("external_schema_validation")
    with pytest.raises(module.SchemaValidationError) as caught:
        run(**kwargs, checker=checker, failure_sink=failures.append)
    error = caught.value
    assert error.stage == "input_validation"
    assert error.code == "ADAPTED_INPUT_INVALID"
    assert isinstance(error.__cause__, Exception)
    assert checker.call_count == 0
    assert failures == [error.failure_record]
    assert error.failure_record["failed_decision_id"] == "DECISION-01"
    assert kwargs == before

def test_valid_empty_inventory():
    run = require_entry()
    kwargs = arguments()
    kwargs["source_snapshot"]["payload"]["decisions"] = []
    kwargs["inventory"]["entries"] = []
    expected = expected_batch()
    for field in ("expansion", "selections", "findings", "decisions"):
        expected[field] = []
    result, checker = execute(run, kwargs)
    assert result == expected
    assert checker.call_count == 0

def test_unavailable_inventory_is_not_empty_success():
    run = require_entry()
    kwargs = arguments()
    del kwargs["source_snapshot"]["payload"]["decisions"]
    kwargs["inventory"] = None
    result, checker = execute(run, kwargs)
    assert checker.call_count == 0
    assert result["decisions"] == []
    assert result["expansion"] == []
    assert result["selections"] == []
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["code"] == "SOURCE_COVERAGE_UNKNOWN"
    assert finding["target_path"] == "/decisions"
    assert finding["decision_id"] is None
    assert finding["evidence_refs"] == []
    assert "PASS" not in result and "pass" not in result

def test_later_checker_failure_preserves_partial_batch():
    run = require_entry()
    kwargs = arguments()
    before = copy.deepcopy(kwargs)
    fault = ValueError("Injected second-decision checker fault")
    def check(**inputs):
        if inputs["adoption_id"] == "ADOPT-01-B/~":
            raise fault
        return inspect_adoption(**inputs)
    checker = Mock(side_effect=check)
    failures = []
    module = importlib.import_module("external_schema_validation")
    with pytest.raises(module.SchemaValidationError) as caught:
        run(**kwargs, checker=checker, failure_sink=failures.append)
    error = caught.value
    assert error.stage == "checker_execution"
    assert error.code == "CHECKER_EXECUTION_ERROR"
    assert error.__cause__ is fault
    assert failures == [error.failure_record]
    record = error.failure_record
    assert record["failed_decision_id"] == "DECISION-02"
    expected = expected_batch()["decisions"]
    expected[1].update(status="execution_error", checker_result=None)
    expected[2].update(status="not_executed", checker_invoked=False,
                       checker_result=None)
    assert record["decisions"] == expected
    assert checker.call_count == 2
    assert [
        call.kwargs["adoption_id"] for call in checker.call_args_list
    ] == ["ADOPT-01-A", "ADOPT-01-B/~"]
    assert isinstance(record["expansion"], list)
    assert record["expansion"]
    assert kwargs == before

def test_optional_presentation_has_zero_members():
    run = require_entry()
    kwargs = arguments()
    registry = kwargs["source_snapshot"]["payload"]["registry"]
    registry["ADOPT-01-A"]["presentation_ref"] = None
    expected = expected_batch()
    expected["expansion"] = [
        row for row in expected["expansion"]
        if not (row["decision_id"] == "DECISION-01"
                and row["rule_id"].startswith("presentation."))
    ]
    for row in expected["selections"]:
        if row["decision_id"] == "DECISION-01" and row["selector"] == "presentation":
            row["selection_count"] = 0
    missing = json.loads(
        Path("fixtures/decision-input-v2/missing_presentation.json").read_text()
    )["expected"]
    replacements = {
        "ADOPT-01": "ADOPT-01-A", "OUT-01": "OUT-01-A",
        "PRESENT-01": "PRESENT-01-A", "SOURCE-01": "SOURCE-01-A",
        "VERIFY-01": "VERIFY-01-A", "DECISION-01": "DECISION-01",
    }
    expected["decisions"][0]["checker_result"] = replace_exact(
        missing, replacements
    )
    result, checker = execute(run, kwargs)
    assert result == expected
    assert_decision_calls(checker, kwargs["inventory"])

def test_shared_source_keeps_decision_associations():
    run = require_entry()
    kwargs = arguments()
    registry = kwargs["source_snapshot"]["payload"]["registry"]
    registry["OUT-01-B/~"]["citations"][0]["source_id"] = "SOURCE-01-A"
    registry["VERIFY-01-B/~"]["source_id"] = "SOURCE-01-A"
    del registry["SOURCE-01-B/~"]
    expected = expected_batch()
    for row in expected["expansion"]:
        if row["decision_id"] != "DECISION-02":
            continue
        if row["rule_id"].startswith("source."):
            row["record_id"] = "SOURCE-01-A"
            for field in ("source_path", "target_path"):
                row[field] = row[field].replace(
                    "SOURCE-01-B~1~0", "SOURCE-01-A"
                )
    result, checker = execute(run, kwargs)
    assert result == expected
    assert_decision_calls(checker, kwargs["inventory"])
    associations = {
        row["decision_id"] for row in result["expansion"]
        if row["record_id"] == "SOURCE-01-A"
    }
    assert associations == {"DECISION-01", "DECISION-02"}

def test_missing_version_remains_field_finding():
    run = require_entry()
    kwargs = arguments()
    del kwargs["source_snapshot"]["payload"]["registry"]["OUT-01-A"]["version"]
    result, checker = execute(run, kwargs)
    findings = [
        row for row in result["findings"]
        if row["decision_id"] == "DECISION-01"
    ]
    assert findings == [{
        "code": "SOURCE_COVERAGE_UNKNOWN",
        "decision_id": "DECISION-01",
        "rule_id": "output.version",
        "target_path": "/registry/OUT-01-A/version",
        "source_snapshot_id": "SYNTHETIC-BATCH-01",
        "schema_revision": "SYNTHETIC-SCHEMA-01",
        "inventory_revision": "SYNTHETIC-INVENTORY-01",
        "evidence_refs": [],
        "explanation": "Source absence is not established.",
        "affected_targets": [],
    }]
    expected = expected_batch()["decisions"]
    expected[0].update(status="blocked", checker_invoked=False,
                       checker_result=None)
    assert result["decisions"] == expected
    assert checker.call_count == 1
    assert checker.call_args.kwargs["adoption_id"] == "ADOPT-01-B/~"
    assert [
        row for row in result["findings"]
        if row["decision_id"] == "DECISION-03"
    ] == load("expected_findings.json")

def test_missing_output_groups_descendants():
    run = require_entry()
    kwargs = arguments()
    del kwargs["source_snapshot"]["payload"]["registry"]["OUT-01-A"]
    result, checker = execute(run, kwargs)
    findings = [
        row for row in result["findings"]
        if row["decision_id"] == "DECISION-01"
    ]
    affected = [
        {
            "rule_id": rule["rule_id"],
            "target_path": rule["target_template"].replace(
                "{record_id}", "OUT-01-A"
            ),
            "required_for_checker": rule["required_for_checker"],
        }
        for rule in sorted(kwargs["schema"]["rules"],
                           key=lambda item: item["rule_id"])
        if rule["kind"] == "output" and rule["rule_id"] != "output.root"
    ]
    assert findings == [{
        "code": "SOURCE_COVERAGE_UNKNOWN",
        "decision_id": "DECISION-01", "rule_id": "output.root",
        "target_path": "/registry/OUT-01-A",
        "source_snapshot_id": "SYNTHETIC-BATCH-01",
        "schema_revision": "SYNTHETIC-SCHEMA-01",
        "inventory_revision": "SYNTHETIC-INVENTORY-01",
        "evidence_refs": [],
        "explanation": "Source absence is not established.",
        "affected_targets": affected,
    }]
    expected = expected_batch()["decisions"]
    expected[0].update(status="blocked", checker_invoked=False,
                       checker_result=None)
    assert result["decisions"] == expected
    assert checker.call_count == 1
    assert checker.call_args.kwargs["adoption_id"] == "ADOPT-01-B/~"

def test_record_renaming_preserves_complete_batch():
    run = require_entry()
    kwargs = arguments()
    frozen_schema = copy.deepcopy(kwargs["schema"])
    identifiers = set(kwargs["source_snapshot"]["payload"]["registry"])
    identifiers.add("ADOPT-01-C")
    replacements = {
        identifier: "RENAMED/~/" + identifier
        for identifier in identifiers
    }
    kwargs["source_snapshot"] = replace_exact(
        kwargs["source_snapshot"], replacements
    )
    kwargs["inventory"] = replace_exact(kwargs["inventory"], replacements)
    expected = expected_batch()
    expected_replacements = dict(replacements)
    def escaped(value):
        return value.replace("~", "~0").replace("/", "~1")
    for identifier, replacement in replacements.items():
        old_root = "/registry/" + escaped(identifier)
        new_root = "/registry/" + escaped(replacement)
        expected_replacements[old_root] = new_root
        for rule in frozen_schema["rules"]:
            for field in ("source_template", "target_template"):
                template = rule[field]
                expected_replacements[
                    template.replace("{record_id}", escaped(identifier))
                ] = template.replace("{record_id}", escaped(replacement))
    expected = replace_exact(expected, expected_replacements)
    result, checker = execute(run, kwargs)
    assert result == expected
    assert kwargs["schema"] == frozen_schema
    assert checker.call_count == 2
    assert [
        call.kwargs["adoption_id"] for call in checker.call_args_list
    ] == [replacements["ADOPT-01-A"], replacements["ADOPT-01-B/~"]]

def test_unmappable_version_blocks_affected_decisions():
    run = require_entry()
    kwargs = arguments()
    rule = next(
        item for item in kwargs["schema"]["rules"]
        if item["rule_id"] == "output.version"
    )
    rule.update({
        "mapping_status": "UNMAPPABLE",
        "source_template": None,
        "transformation": None,
        "reason": "Synthetic representation has no version identity",
    })
    result, checker = execute(run, kwargs)
    assert checker.call_count == 0
    assert all(
        row["status"] == "blocked" and not row["checker_invoked"]
        and row["checker_result"] is None
        for row in result["decisions"]
    )
    expected_findings = copy.deepcopy(load("expected_findings.json"))
    for decision_id, record_id in [
        ("DECISION-01", "OUT-01-A"),
        ("DECISION-02", "OUT-01-B~1~0"),
    ]:
        expected_findings.append({
            "code": "ADAPTER_UNMAPPABLE",
            "decision_id": decision_id, "rule_id": "output.version",
            "target_path": "/registry/" + record_id + "/version",
            "source_snapshot_id": "SYNTHETIC-BATCH-01",
            "schema_revision": "SYNTHETIC-SCHEMA-01",
            "inventory_revision": "SYNTHETIC-INVENTORY-01",
            "evidence_refs": [],
            "explanation": "Frozen mapping declares no faithful representation.",
            "affected_targets": [],
        })
    assert sorted(result["findings"], key=lambda row: row["decision_id"]) == sorted(
        expected_findings, key=lambda row: row["decision_id"]
    )
