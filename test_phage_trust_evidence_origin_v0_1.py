"""
Executable regression contract for PHAGE Trust Evidence Origin v0.1.

G1 — Forged Evidence Origin
G2 — Evidence Verifier Internal Failure

Specification closure does not imply enforcement closure.
"""

import importlib


MODULE = "phage_trust_evidence_origin_v0_1"

EVIDENCE_ORIGIN_UNVERIFIED = "EVIDENCE_ORIGIN_UNVERIFIED"
EVIDENCE_VERIFICATION_ERROR = "EVIDENCE_VERIFICATION_ERROR"
BLOCKED = "BLOCKED"



def _load_module():
    try:
        return importlib.import_module(MODULE)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE:
            return None
        raise


def _forged_evidence():
    # Valid-looking contents, but NOT produced by the trusted producer path.
    return {
        "value": "SCHEDULE_NO_MATCH",
        "source": "schedule_engine",
        "schedule_ref": "schedule-OR-7",
        "policy_version": "v17",
        "observed_at": "2026-09-09T00:00:00Z",
    }


def _assert_result_shape(result):
    assert isinstance(result, dict), (
        "evidence-origin evaluation must return a dict"
    )

    required = {
        "origin_status",
        "effect_path",
    }

    assert required.issubset(result), (
        f"evidence-origin result missing keys: "
        f"{required - set(result)}"
    )


def run_fixture_g1(module):
    assert module is not None, (
        "G1 contract RED: phage_trust_evidence_origin_v0_1 "
        "is not implemented"
    )

    evaluate = getattr(module, "evaluate_evidence_origin", None)

    assert callable(evaluate), (
        "G1 contract RED: evaluate_evidence_origin is not implemented"
    )

    result = evaluate(
        candidate=_forged_evidence(),
    )

    _assert_result_shape(result)

    assert result["origin_status"] == EVIDENCE_ORIGIN_UNVERIFIED
    assert result["effect_path"] == BLOCKED


class _BrokenVerifier:
    def __call__(self, candidate):
        raise RuntimeError("synthetic verifier failure")


def run_fixture_g2(module):
    assert module is not None, (
        "G2 contract RED: phage_trust_evidence_origin_v0_1 "
        "is not implemented"
    )

    evaluate_with_verifier = getattr(
        module,
        "_evaluate_evidence_origin_with_verifier",
        None,
    )

    assert callable(evaluate_with_verifier), (
        "G2 contract RED: verifier enforcement seam is not implemented"
    )

    result = evaluate_with_verifier(
        candidate=_forged_evidence(),
        verifier=_BrokenVerifier(),
    )

    _assert_result_shape(result)

    assert result["origin_status"] == EVIDENCE_VERIFICATION_ERROR
    assert result["effect_path"] == BLOCKED


def run():
    module = _load_module()

    fixtures = (
        (
            "G1",
            "forged_evidence_origin",
            lambda: run_fixture_g1(module),
        ),
        (
            "G2",
            "verifier_internal_failure",
            lambda: run_fixture_g2(module),
        ),
    )

    failures = []

    for fixture_id, name, fixture in fixtures:
        try:
            fixture()
        except Exception as exc:
            failures.append((fixture_id, name, exc))
            print(
                f"FAIL: fixture_{fixture_id}_{name}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            print(f"PASS: fixture_{fixture_id}_{name}")

    if failures:
        raise AssertionError(
            f"PHAGE Trust Evidence Origin regression RED: "
            f"{len(failures)} / {len(fixtures)} failing"
        )

    print(
        "PHAGE Trust Evidence Origin regression PASS: "
        f"{len(fixtures)} / {len(fixtures)}"
    )


if __name__ == "__main__":
    run()
