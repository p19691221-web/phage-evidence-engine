"""
Executable regression harness for PHAGE Applicable Evidence Reuse G6 v0.1.

Phase 1 freezes only:
- module loader behavior;
- public entry-point name;
- reuse-result shape;
- allowed reuse status vocabulary;
- the meaningful RED baseline.

The G6A-G6H3 executable fixtures are added only after this harness
surface is reviewed. No reuse enforcement implementation belongs here.
"""

import importlib

MODULE = "phage_applicable_evidence_reuse_v0_1"
ENTRY_POINT = "evaluate_applicable_evidence_reuse"

REUSE_ALLOWED = "REUSE_ALLOWED"
REUSE_UNRESOLVED = "REUSE_UNRESOLVED"
REUSE_INVALIDATED = "REUSE_INVALIDATED"

ALLOWED_REUSE_STATUSES = {
    REUSE_ALLOWED,
    REUSE_UNRESOLVED,
    REUSE_INVALIDATED,
}

REQUIRED_RESULT_KEYS = {"reuse_status", "reason_code"}

FORBIDDEN_RESULT_KEYS = {
    "authorized",
    "authorization_status",
    "decision",
    "effect_path",
    "applicable",
}


def _load_module():
    try:
        return importlib.import_module(MODULE)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE:
            return None
        raise


def _assert_result_shape(result):
    assert isinstance(result, dict), (
        "G6 reuse evaluation must return a dict regression observation"
    )

    assert REQUIRED_RESULT_KEYS.issubset(result), (
        "G6 reuse result missing keys: "
        f"{REQUIRED_RESULT_KEYS - set(result)}"
    )

    forbidden_present = FORBIDDEN_RESULT_KEYS.intersection(result)
    assert not forbidden_present, (
        "G6 reuse result must not expose authorization/effect semantics: "
        f"{forbidden_present}"
    )

    assert result["reuse_status"] in ALLOWED_REUSE_STATUSES, (
        "G6 reuse_status must be one of "
        f"{sorted(ALLOWED_REUSE_STATUSES)}"
    )

    assert isinstance(result["reason_code"], str), (
        "G6 reason_code must use a canonical string representation"
    )

    assert result["reason_code"], (
        "G6 reason_code must not be empty"
    )


def run_contract_surface(module):
    assert module is not None, (
        "G6 contract RED: phage_applicable_evidence_reuse_v0_1 "
        "is not implemented"
    )

    entry_point = getattr(module, ENTRY_POINT, None)

    assert callable(entry_point), (
        "G6 contract RED: evaluate_applicable_evidence_reuse "
        "is not implemented"
    )


def run():
    module = _load_module()

    fixtures = (
        (
            "G6_CONTRACT_SURFACE",
            "loader_entrypoint_result_schema",
            lambda: run_contract_surface(module),
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
            "PHAGE Applicable Evidence Reuse G6 regression RED: "
            f"{len(failures)} / {len(fixtures)} failing"
        )

    print(
        "PHAGE Applicable Evidence Reuse G6 regression harness PASS: "
        f"{len(fixtures)} / {len(fixtures)}"
    )


if __name__ == "__main__":
    run()
