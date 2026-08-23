#!/usr/bin/env python3
"""
DF-017 Independent Validator

Purpose
-------
Independently inspect the frozen DF-017 fixture and source manifest.

Important:
- This program does NOT assume PHAGE is correct.
- AIID is NOT treated as ground truth.
- External sources are inputs, not proof of a PHAGE result.
- PASS here means the DF-017 validation package satisfies the
  reproducibility/integrity preconditions checked by this script.
- It does NOT mean that a substantive PHAGE claim has been proven.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


FIXTURE_FILE = "DF017_AIID_74_FIXTURE.json"
SOURCES_FILE = "DF017_AIID_74_SOURCES.json"

EXPECTED_FIXTURE_ID = "DF017-AIID-74"
EXPECTED_VALIDATION_ID = "DF-017"
EXPECTED_INCIDENT_ID = 74

ALLOWED_RESULTS = {"PASS", "FAIL", "UNRESOLVED"}


class ValidationFailure(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationFailure(f"required file not found: {path.name}")

    try:
        with path.open("r", encoding="utf-8") as f:
            value = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValidationFailure(
            f"{path.name} is not valid JSON: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(value, dict):
        raise ValidationFailure(
            f"{path.name} top-level JSON value must be an object"
        )

    return value


def require_equal(
    checks: list[dict[str, Any]],
    name: str,
    observed: Any,
    expected: Any,
) -> None:
    passed = observed == expected
    checks.append(
        {
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "observed": observed,
            "expected": expected,
        }
    )

    if not passed:
        raise ValidationFailure(
            f"{name}: expected {expected!r}, observed {observed!r}"
        )


def require_true(
    checks: list[dict[str, Any]],
    name: str,
    condition: bool,
    detail: str,
) -> None:
    checks.append(
        {
            "check": name,
            "status": "PASS" if condition else "FAIL",
            "detail": detail,
        }
    )

    if not condition:
        raise ValidationFailure(f"{name}: {detail}")


def nested_get(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data

    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)

    return current


def validate_package(
    fixture: dict[str, Any],
    sources: dict[str, Any],
) -> dict[str, Any]:

    checks: list[dict[str, Any]] = []

    # ------------------------------------------------------------
    # 1. Identity consistency
    # ------------------------------------------------------------

    require_equal(
        checks,
        "fixture validation_id",
        fixture.get("validation_id"),
        EXPECTED_VALIDATION_ID,
    )

    require_equal(
        checks,
        "source manifest validation_id",
        sources.get("validation_id"),
        EXPECTED_VALIDATION_ID,
    )

    require_equal(
        checks,
        "fixture fixture_id",
        fixture.get("fixture_id"),
        EXPECTED_FIXTURE_ID,
    )

    require_equal(
        checks,
        "source manifest fixture_id",
        sources.get("fixture_id"),
        EXPECTED_FIXTURE_ID,
    )

    fixture_incident_id = (
        nested_get(fixture, "incident", "incident_id")
        or nested_get(fixture, "source", "incident_id")
    )

    source_incident_id = nested_get(
        sources,
        "incident",
        "incident_id",
    )

    require_equal(
        checks,
        "fixture incident_id",
        fixture_incident_id,
        EXPECTED_INCIDENT_ID,
    )

    require_equal(
        checks,
        "source manifest incident_id",
        source_incident_id,
        EXPECTED_INCIDENT_ID,
    )

    # ------------------------------------------------------------
    # 2. Provenance policy
    # ------------------------------------------------------------

    policy = sources.get("provenance_policy")

    require_true(
        checks,
        "source manifest has provenance policy",
        isinstance(policy, dict),
        "provenance_policy must be a JSON object",
    )

    assert isinstance(policy, dict)

    require_equal(
        checks,
        "AIID is not ground truth",
        policy.get("aiid_is_ground_truth"),
        False,
    )

    require_equal(
        checks,
        "single source is not ground truth",
        policy.get("single_source_is_ground_truth"),
        False,
    )

    require_equal(
        checks,
        "sources are external inputs",
        policy.get("sources_are_external_inputs"),
        True,
    )

    require_equal(
        checks,
        "expected PHAGE result is not encoded",
        policy.get("expected_phage_result_encoded"),
        False,
    )

    require_equal(
        checks,
        "negative or unresolved result is allowed",
        policy.get("negative_or_unresolved_results_allowed"),
        True,
    )

    # ------------------------------------------------------------
    # 3. External sources
    # ------------------------------------------------------------

    source_list = sources.get("sources")

    require_true(
        checks,
        "source list exists",
        isinstance(source_list, list),
        "sources must be a JSON array",
    )

    assert isinstance(source_list, list)

    require_true(
        checks,
        "at least two source records exist",
        len(source_list) >= 2,
        f"observed {len(source_list)} source record(s)",
    )

    source_ids: list[str] = []

    for index, source in enumerate(source_list):
        require_true(
            checks,
            f"source[{index}] is an object",
            isinstance(source, dict),
            "each source must be a JSON object",
        )

        assert isinstance(source, dict)

        sid = source.get("source_id")

        require_true(
            checks,
            f"source[{index}] has source_id",
            isinstance(sid, str) and bool(sid.strip()),
            f"observed source_id={sid!r}",
        )

        source_ids.append(str(sid))

        require_equal(
            checks,
            f"source[{index}] ground_truth",
            source.get("ground_truth"),
            False,
        )

        require_true(
            checks,
            f"source[{index}] has URL",
            isinstance(source.get("url"), str)
            and source["url"].startswith(("https://", "http://")),
            f"observed url={source.get('url')!r}",
        )

    require_true(
        checks,
        "source IDs are unique",
        len(source_ids) == len(set(source_ids)),
        f"source_ids={source_ids}",
    )

    # ------------------------------------------------------------
    # 4. Hash handling
    # ------------------------------------------------------------

    hashes_verified = policy.get("source_content_hashes_verified")

    if hashes_verified is True:
        missing_hashes = [
            s.get("source_id")
            for s in source_list
            if not isinstance(s.get("sha256"), str)
            or len(s.get("sha256", "")) != 64
        ]

        require_true(
            checks,
            "verified source hashes are present",
            not missing_hashes,
            f"missing/invalid SHA-256 for {missing_hashes}",
        )
    else:
        checks.append(
            {
                "check": "source hashes",
                "status": "UNRESOLVED",
                "detail": (
                    "source_content_hashes_verified is false; "
                    "remote source content is therefore not yet a fully "
                    "frozen reproducible snapshot"
                ),
            }
        )

    # ------------------------------------------------------------
    # 5. Detect accidental expected-result leakage
    # ------------------------------------------------------------

    forbidden_keys = {
        "expected_result",
        "expected_phage_result",
        "expected_verdict",
        "golden_result",
        "golden_verdict",
    }

    leaked_keys = sorted(
        key for key in forbidden_keys
        if key in fixture or key in sources
    )

    require_true(
        checks,
        "no top-level expected-result leakage",
        not leaked_keys,
        f"forbidden keys found: {leaked_keys}",
    )

    # ------------------------------------------------------------
    # Final package-level result
    # ------------------------------------------------------------

    unresolved = any(
        check["status"] == "UNRESOLVED"
        for check in checks
    )

    result = "UNRESOLVED" if unresolved else "PASS"

    return {
        "schema": "phage.df017.validation-output.v1",
        "validation_id": EXPECTED_VALIDATION_ID,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "incident_id": EXPECTED_INCIDENT_ID,
        "result": result,
        "scope": "validation-package-integrity",
        "checks": checks,
        "interpretation": (
            "PASS means the checked DF-017 validation package "
            "satisfies the structural and provenance preconditions. "
            "UNRESOLVED means one or more reproducibility conditions "
            "remain incomplete. Neither result proves a substantive "
            "PHAGE claim."
        ),
    }


def main() -> int:
    root = Path(__file__).resolve().parent

    fixture_path = root / FIXTURE_FILE
    sources_path = root / SOURCES_FILE

    try:
        fixture = load_json(fixture_path)
        sources = load_json(sources_path)

        report = validate_package(fixture, sources)

    except ValidationFailure as exc:
        report = {
            "schema": "phage.df017.validation-output.v1",
            "validation_id": EXPECTED_VALIDATION_ID,
            "fixture_id": EXPECTED_FIXTURE_ID,
            "incident_id": EXPECTED_INCIDENT_ID,
            "result": "FAIL",
            "scope": "validation-package-integrity",
            "error": str(exc),
        }

        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    if report["result"] not in ALLOWED_RESULTS:
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
