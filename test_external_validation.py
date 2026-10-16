import copy
import importlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from decision_input_traceability import inspect_adoption

CASES = sorted(Path("fixtures/external-validation").glob("*.json"))

def entry_point():
    if importlib.util.find_spec("external_validation") is None:
        return None
    return getattr(
        importlib.import_module("external_validation"),
        "run_external_validation", None,
    )

def test_wrapper_entry_point_exists():
    assert callable(entry_point()), "External wrapper entry point absent"

def make_adapter(case):
    def adapt(source_snapshot, manifest):
        result = copy.deepcopy(source_snapshot["payload"]["export"])
        if case["adapter_mode"] == "invalid_registry_kind":
            result["registry"][result["adoption_id"]]["kind"] = "output"
        return result
    return Mock(side_effect=adapt)

def make_checker(case):
    if case["checker_mode"] == "raise_value_error":
        return Mock(side_effect=ValueError("Injected checker fault"))
    return Mock(side_effect=inspect_adoption)

@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_frozen_external_case(path):
    run = entry_point()
    if not callable(run):
        pytest.skip("Wrapper absent; differential case NOT EXECUTED")
    case = json.loads(path.read_text())
    snapshot = copy.deepcopy(case["source_snapshot"])
    manifest = copy.deepcopy(case["manifest"])
    before = copy.deepcopy((snapshot, manifest))
    adapter = make_adapter(case)
    checker = make_checker(case)
    failures = []
    kwargs = dict(
        source_snapshot=snapshot, manifest=manifest,
        adapter=adapter, checker=checker,
        failure_sink=failures.append,
    )
    try:
        if "expected_error" not in case:
            actual = run(**kwargs)
            actual["findings"] = sorted(
                actual["findings"], key=lambda item: item["target_path"]
            )
            assert actual == case["expected_record"]
            assert checker.call_count == case["expected_checker_calls"]
            assert failures == []
        else:
            module = importlib.import_module("external_validation")
            with pytest.raises(module.ExternalValidationError) as caught:
                run(**kwargs)
            error = caught.value
            expected = case["expected_error"]
            assert error.stage == expected["stage"]
            assert error.code == expected["code"]
            assert checker.call_count == expected["checker_calls"]
            assert isinstance(error.__cause__, Exception)
            if case["checker_mode"] == "raise_value_error":
                assert error.__cause__ is checker.side_effect
            record = error.failure_record
            assert failures == [record]
            assert record == {
                "manifest_revision": manifest["manifest_revision"],
                "source_snapshot_id": snapshot["snapshot_id"],
                "findings": case["expected_findings"],
                "checker_invoked": bool(expected["checker_calls"]),
                "checker_result": None,
                "stage": expected["stage"],
                "code": expected["code"],
                "cause_type": type(error.__cause__).__name__,
                "cause_message": str(error.__cause__),
            }
        assert adapter.call_count == case["expected_adapter_calls"]
    finally:
        assert (snapshot, manifest) == before

def test_frozen_case_inventory():
    assert len(CASES) == 9
    unknown = json.loads(CASES[4].read_text())
    absent = json.loads(CASES[5].read_text())
    assert unknown["source_snapshot"] == absent["source_snapshot"]
    assert unknown["expected_findings"] != absent["expected_findings"]

@pytest.mark.parametrize("fault", ["manifest", "adapter"])
def test_prechecker_execution_failure(fault):
    run = entry_point()
    if not callable(run):
        pytest.skip("Wrapper absent; boundary case NOT EXECUTED")
    module = importlib.import_module("external_validation")
    case = json.loads(CASES[0].read_text())
    snapshot = copy.deepcopy(case["source_snapshot"])
    manifest = copy.deepcopy(case["manifest"])
    adapter = make_adapter(case)
    checker = make_checker(case)
    if fault == "manifest":
        manifest["source_snapshot_id"] = "WRONG-SNAPSHOT"
        stage, code = "manifest_validation", "MANIFEST_INVALID"
    else:
        adapter.side_effect = RuntimeError("Injected adapter fault")
        stage, code = "adaptation", "ADAPTER_EXECUTION_ERROR"
    before = copy.deepcopy((snapshot, manifest))
    failures = []
    with pytest.raises(module.ExternalValidationError) as caught:
        run(source_snapshot=snapshot, manifest=manifest,
            adapter=adapter, checker=checker,
            failure_sink=failures.append)
    error = caught.value
    assert (error.stage, error.code) == (stage, code)
    assert isinstance(error.__cause__, Exception)
    if fault == "adapter":
        assert error.__cause__ is adapter.side_effect
    assert checker.call_count == 0
    assert adapter.call_count == int(fault == "adapter")
    assert failures == [error.failure_record]
    assert error.failure_record["checker_invoked"] is False
    assert error.failure_record["checker_result"] is None
    assert (snapshot, manifest) == before

def test_failure_sink_does_not_hide_checker_fault():
    run = entry_point()
    if not callable(run):
        pytest.skip("Wrapper absent; boundary case NOT EXECUTED")
    module = importlib.import_module("external_validation")
    case = json.loads(CASES[7].read_text())
    snapshot = copy.deepcopy(case["source_snapshot"])
    manifest = copy.deepcopy(case["manifest"])
    before = copy.deepcopy((snapshot, manifest))
    adapter = make_adapter(case)
    checker = make_checker(case)
    sink_fault = OSError("Injected persistence fault")
    sink = Mock(side_effect=sink_fault)
    with pytest.raises(module.ExternalValidationError) as caught:
        run(source_snapshot=snapshot, manifest=manifest,
            adapter=adapter, checker=checker, failure_sink=sink)
    error = caught.value
    assert error.stage == "checker_execution"
    assert error.code == "CHECKER_EXECUTION_ERROR"
    assert error.__cause__ is checker.side_effect
    assert error.persistence_error is sink_fault
    sink.assert_called_once_with(error.failure_record)
    assert adapter.call_count == 1
    assert checker.call_count == 1
    assert error.failure_record["checker_invoked"] is True
    assert error.failure_record["checker_result"] is None
    assert (snapshot, manifest) == before

def test_conflicting_coverage_is_unknown():
    run = entry_point()
    if not callable(run):
        pytest.skip("Wrapper absent; boundary case NOT EXECUTED")
    case = json.loads(CASES[5].read_text())
    snapshot = copy.deepcopy(case["source_snapshot"])
    manifest = copy.deepcopy(case["manifest"])
    contrary = copy.deepcopy(manifest["evidence"][0])
    contrary["evidence_id"] = "SYNTHETIC-CONTRARY"
    contrary["reference"] = "synthetic://conflicting-observation"
    contrary["assertion"] = "source_record_present"
    manifest["evidence"].append(contrary)
    for mapping in manifest["mappings"]:
        if mapping["coverage_evidence_refs"]:
            mapping["coverage_evidence_refs"].append(contrary["evidence_id"])
    before = copy.deepcopy((snapshot, manifest))
    expected = copy.deepcopy(case["expected_record"])
    for finding in expected["findings"]:
        finding["code"] = "SOURCE_COVERAGE_UNKNOWN"
        finding["evidence_refs"].append(contrary["evidence_id"])
        finding["explanation"] = "Source absence is not established."
    adapter, checker = make_adapter(case), make_checker(case)
    failures = []
    actual = run(source_snapshot=snapshot, manifest=manifest,
                 adapter=adapter, checker=checker,
                 failure_sink=failures.append)
    actual["findings"].sort(key=lambda item: item["target_path"])
    assert actual == expected
    assert adapter.call_count == checker.call_count == 0
    assert failures == []
    assert (snapshot, manifest) == before

def test_optional_presentation_omission():
    run = entry_point()
    if not callable(run):
        pytest.skip("Wrapper absent; boundary case NOT EXECUTED")
    case = json.loads(CASES[0].read_text())
    snapshot = copy.deepcopy(case["source_snapshot"])
    manifest = copy.deepcopy(case["manifest"])
    exported = snapshot["payload"]["export"]
    adoption = exported["registry"][exported["adoption_id"]]
    presentation_id = adoption["presentation_ref"]
    del exported["registry"][presentation_id]
    root = "/registry/" + presentation_id.replace("~", "~0").replace("/", "~1")
    findings = []
    for mapping in manifest["mappings"]:
        path = mapping["target_path"]
        if path == root or path.startswith(root + "/"):
            assert mapping["required_for_checker"] is False
            findings.append({
                "code": "SOURCE_COVERAGE_UNKNOWN",
                "target_path": path,
                "source_snapshot_id": snapshot["snapshot_id"],
                "manifest_revision": manifest["manifest_revision"],
                "evidence_refs": [],
                "explanation": "Source absence is not established.",
            })
    assert findings
    expected = copy.deepcopy(case["expected_record"])
    expected["findings"] = sorted(findings, key=lambda item: item["target_path"])
    missing = json.loads(
        Path("fixtures/decision-input-v2/missing_presentation.json").read_text()
    )
    expected["checker_result"] = missing["expected"]
    before = copy.deepcopy((snapshot, manifest))
    adapter, checker = make_adapter(case), make_checker(case)
    failures = []
    try:
        actual = run(source_snapshot=snapshot, manifest=manifest,
                     adapter=adapter, checker=checker,
                     failure_sink=failures.append)
        actual["findings"].sort(key=lambda item: item["target_path"])
        assert actual == expected
        assert adapter.call_count == 1
        assert checker.call_count == 1
        assert failures == []
    finally:
        assert (snapshot, manifest) == before
