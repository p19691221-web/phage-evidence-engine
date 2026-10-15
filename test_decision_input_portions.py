import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from decision_input_traceability import inspect_adoption

ROOT = Path(__file__).parent / "fixtures" / "decision-input-v2"
CASES = sorted(ROOT.glob("*.json"))


def load(name):
    return json.loads((ROOT / (name + ".json")).read_text())


def inspect(inputs):
    before = copy.deepcopy(inputs)
    with patch("gate.run_gate",
               side_effect=AssertionError("Assessment gate forbidden")):
        result = inspect_adoption(**inputs)
    assert inputs == before
    return result


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_v2_exact_findings(path):
    fixture = json.loads(path.read_text())
    assert inspect(fixture["input"]) == fixture["expected"]


def test_renamed_control_concrete_support_and_equivalence():
    control = inspect(load("control")["input"])
    renamed = inspect(load("renamed_control")["input"])
    assert renamed.get("output_support") == {
        "Q7": {"citation": "matched", "verification": "matched"},
        "R9": {
            "citation": "not_asserted",
            "verification": "not_asserted",
        },
    }
    assert renamed["adopted_support"] == {
        "Q7": {"citation": "matched", "verification": "matched"},
    }
    mapped = copy.deepcopy(control)
    rename = {"P1": "Q7", "P2": "R9"}
    for field in ("output_support", "adopted_support"):
        mapped[field] = {
            rename[key]: value for key, value in mapped[field].items()
        }
    assert renamed == mapped
