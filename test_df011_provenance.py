"""DF-011 boundary tests; baseline execution is not a provenance gate."""
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import gate
from lineage import Evidence, ResolvedAvailability, AvailabilityStatus

FIXTURES = Path(__file__).parent / "fixtures" / "df011"
SENTINEL = "DF011_EVALUATOR_REACHED_V1"


def load_case(name):
    return json.loads((FIXTURES / (name + ".json")).read_text())


def gate_inputs(case):
    bundle = case["lineage_bundle"]
    store = {}
    for key, raw in bundle["evidence_store"].items():
        item = dict(raw)
        for field in ("observed_at", "available_at"):
            item[field] = datetime.fromisoformat(item[field])
        for field in ("derived_from", "source_refs"):
            item[field] = tuple(item[field])
        store[key] = Evidence(**item)
    availability = {}
    for key, raw in bundle["availability_view"].items():
        item = dict(raw)
        item["status"] = AvailabilityStatus(item["status"])
        item["resolved_available_at"] = datetime.fromisoformat(
            item["resolved_available_at"])
        item["supporting_claim_refs"] = tuple(
            item["supporting_claim_refs"])
        availability[key] = ResolvedAvailability(**item)
    return {
        "evidence_id": bundle["evidence_id"],
        "epistemic_cutoff": datetime.fromisoformat(
            bundle["epistemic_cutoff"]),
        "evidence_store": store,
        "availability_view": availability,
    }


class RecordingEvaluator:
    def __init__(self):
        self.outputs = []
        self.evaluate = Mock(side_effect=self._evaluate)

    def _evaluate(self, **kwargs):
        self.outputs.append(SENTINEL)
        return SENTINEL


CASES = [
    "self_proposed",
    "third_party_unsupported",
    "self_approved",
    "supported_control",
]


def execute_baseline(case, run_gate_spy, evaluator):
    """Baseline only: existing API has no provenance input."""
    return run_gate_spy(
        **gate_inputs(case), downstream_evaluator=evaluator)


@pytest.mark.parametrize("name", CASES)
def test_df011_required_boundary(name):
    case = load_case(name)
    inputs = gate_inputs(case)

    # Independently establish the fixed CLEAN lineage prerequisite.
    prerequisite = gate.run_gate(**inputs)
    assert prerequisite.state is gate.GateState.CLEAN

    evaluator = RecordingEvaluator()
    run_gate_spy = Mock(wraps=gate.run_gate)
    result = execute_baseline(case, run_gate_spy, evaluator)
    expected = case["expected"]
    actual = {
        "state": result.state.value,
        "run_gate_calls": run_gate_spy.call_count,
        "evaluator_calls": evaluator.evaluate.call_count,
        "outputs": evaluator.outputs,
    }
    print(name, json.dumps(actual, sort_keys=True))

    errors = []
    for field in ("state", "run_gate_calls", "evaluator_calls"):
        if actual[field] != expected[field]:
            errors.append(
                f"{field}: {actual[field]!r} != {expected[field]!r}")
    if expected["dependency"] is not None:
        dependencies = repr(result.open_dependencies)
        for token in (expected["dependency"], "ES-PUBLIC-001"):
            if token not in dependencies:
                errors.append(f"missing dependency token: {token}")
        if result.evaluation_started:
            errors.append("evaluation_started must be False")
        if evaluator.outputs:
            errors.append("unresolved case produced evaluator output")
    else:
        assert result.evaluation_started is True
        run_gate_spy.assert_called_once_with(
            **inputs, downstream_evaluator=evaluator)
        evaluator.evaluate.assert_called_once()
        received = evaluator.evaluate.call_args.kwargs
        assert set(received) == {"evidence_id", "lineage_result"}
        assert received["evidence_id"] == inputs["evidence_id"]
        assert received["lineage_result"].state.value == "CLEAN"
        assert evaluator.outputs == [expected["sentinel"]]
    assert not errors, "\n".join(errors)
