"""Frozen decision-input contract; absence is not differential execution."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent / "fixtures" / "decision-input-v2"
CASES = sorted(ROOT.glob("*.json"))


def entry_point():
    if importlib.util.find_spec("decision_input_traceability") is None:
        return None
    module = importlib.import_module("decision_input_traceability")
    return getattr(module, "inspect_adoption", None)


def test_production_entry_point_exists():
    assert callable(entry_point()), "Production inspect_adoption is absent"


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_frozen_relationship_contract(path):
    inspect_adoption = entry_point()
    if not callable(inspect_adoption):
        pytest.skip("Entry point absent; differential case NOT EXECUTED")
    fixture = json.loads(path.read_text())
    inputs = copy.deepcopy(fixture["input"])
    before = copy.deepcopy(inputs)
    with patch("gate.run_gate",
               side_effect=AssertionError("Assessment gate forbidden")):
        actual = inspect_adoption(**inputs)
    assert inputs == before, "Checker mutated input records"
    assert actual == fixture["expected"]
