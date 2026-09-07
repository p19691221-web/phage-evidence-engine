"""
Executable regression contract for PHAGE Principle 0 Schedule v0.1.

Frozen semantic fixtures: A-F.

This regression freezes only:
- the Schedule implementation module boundary
- the callable evaluate_schedule entry point
- the callable mutate_schedule entry point
- the minimal dict-based observation contract required by A-F

It does not freeze a ScheduleDefinition class, CurrentScheduleContext class,
storage model, production clock, universal freshness TTL, scheduler
architecture, callback ordering, Emergency Override, or production execution API.
"""

import importlib
from copy import deepcopy
from datetime import datetime, timezone

from phage_authority_engine_v0_1 import AuthorityStatus


SCHEDULE_MODULE = "phage_principle0_schedule_v0_1"
SCHEDULE_EVALUATOR = "evaluate_schedule"
SCHEDULE_MUTATOR = "mutate_schedule"

AT = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)


FROZEN_FIXTURES = (
    {
        "id": "A",
        "name": "valid time space and context",
        "expected_schedule_status": "SCHEDULE_MATCH",
    },
    {
        "id": "B",
        "name": "explicit time mismatch",
        "expected_schedule_status": "SCHEDULE_NO_MATCH",
    },
    {
        "id": "C",
        "name": "explicit bounded-space mismatch",
        "expected_schedule_status": "SCHEDULE_NO_MATCH",
    },
    {
        "id": "D",
        "name": "earlier match does not survive schedule change",
        "expected_schedule_status": "SCHEDULE_NO_MATCH",
        "expected_effect_path": "BLOCKED",
    },
    {
        "id": "E",
        "name": "unauthorized schedule mutation is blocked",
        "expected_mutation": "BLOCKED",
        "expected_schedule_change": "UNCHANGED",
    },
    {
        "id": "F",
        "name": "missing or stale current context is unresolved",
        "expected_schedule_status": "SCHEDULE_UNRESOLVED",
    },
)


def status_name(value) -> str:
    if value is None:
        return "NONE"

    if hasattr(value, "name"):
        return value.name

    return str(value)


def load_schedule_contract():
    module = importlib.import_module(SCHEDULE_MODULE)

    assert hasattr(module, SCHEDULE_EVALUATOR), (
        f"{SCHEDULE_MODULE} must expose {SCHEDULE_EVALUATOR}"
    )

    assert hasattr(module, SCHEDULE_MUTATOR), (
        f"{SCHEDULE_MODULE} must expose {SCHEDULE_MUTATOR}"
    )

    evaluator = getattr(module, SCHEDULE_EVALUATOR)
    mutator = getattr(module, SCHEDULE_MUTATOR)

    assert callable(evaluator), (
        f"{SCHEDULE_EVALUATOR} must be callable"
    )

    assert callable(mutator), (
        f"{SCHEDULE_MUTATOR} must be callable"
    )

    return evaluator, mutator


def make_schedule(
    *,
    version: str = "v17",
    space_ref: str = "OR-7",
) -> dict:
    return {
        "schedule_id": "schedule-OR-7",
        "version": version,
        "time_rule": {
            "start": "09:00",
            "end": "18:00",
        },
        "space_ref": space_ref,
        "context_constraints": {
            "context_state": "NORMAL_OPERATION",
        },
        "effective_from": datetime(
            2026, 9, 1, 0, 0, tzinfo=timezone.utc
        ),
        "effective_until": datetime(
            2026, 9, 30, 23, 59, tzinfo=timezone.utc
        ),
        "source_ref": "schedule-policy-17",
    }


def make_context(
    *,
    observed_at: datetime = AT,
    space_ref: str = "OR-7",
    context_state: str = "NORMAL_OPERATION",
    freshness: str = "FRESH",
) -> dict:
    return {
        "observed_at": observed_at,
        "space_ref": space_ref,
        "context_state": context_state,
        "observation_freshness": freshness,
    }


def test_frozen_fixture_manifest_is_complete() -> None:
    assert tuple(
        fixture["id"] for fixture in FROZEN_FIXTURES
    ) == tuple("ABCDEF")


def run_fixture_a(evaluate_schedule) -> None:
    result = evaluate_schedule(
        schedule=make_schedule(),
        context=make_context(),
    )

    assert status_name(result) == "SCHEDULE_MATCH"


def run_fixture_b(evaluate_schedule) -> None:
    result = evaluate_schedule(
        schedule=make_schedule(),
        context=make_context(
            observed_at=datetime(
                2026, 9, 8, 3, 0, tzinfo=timezone.utc
            )
        ),
    )

    assert status_name(result) == "SCHEDULE_NO_MATCH"


def run_fixture_c(evaluate_schedule) -> None:
    result = evaluate_schedule(
        schedule=make_schedule(),
        context=make_context(space_ref="OR-8"),
    )

    assert status_name(result) == "SCHEDULE_NO_MATCH"


def run_fixture_d(evaluate_schedule) -> None:
    context = make_context()

    earlier = evaluate_schedule(
        schedule=make_schedule(
            version="v17",
            space_ref="OR-7",
        ),
        context=context,
    )

    assert status_name(earlier) == "SCHEDULE_MATCH"

    current = evaluate_schedule(
        schedule=make_schedule(
            version="v18",
            space_ref="OR-8",
        ),
        context=context,
    )

    assert status_name(current) == "SCHEDULE_NO_MATCH"

    effect_eligible = (
        status_name(current) == "SCHEDULE_MATCH"
    )

    assert effect_eligible is False


def run_fixture_e(mutate_schedule) -> None:
    schedule_before = make_schedule()

    mutation = {
        "action": "MODIFY_SCHEDULE",
        "target": "schedule-OR-7",
        "changes": {
            "time_rule": {
                "start": "10:00",
                "end": "18:00",
            }
        },
    }

    result = mutate_schedule(
        schedule=deepcopy(schedule_before),
        mutation=mutation,
        authority_status=(
            AuthorityStatus.AUTHORITY_SCOPE_VIOLATION
        ),
    )

    assert isinstance(result, dict)

    assert {
        "mutation_status",
        "schedule_after",
        "authority_status",
    }.issubset(result)

    assert status_name(
        result["mutation_status"]
    ) == "BLOCKED"

    assert result["schedule_after"] == schedule_before

    assert status_name(
        result["authority_status"]
    ) == "AUTHORITY_SCOPE_VIOLATION"


def run_fixture_f(evaluate_schedule) -> None:
    schedule = make_schedule()

    unresolved_contexts = (
        None,
        {
            "observed_at": AT,
            "space_ref": "OR-7",
            "observation_freshness": "FRESH",
        },
        make_context(
            freshness="STALE"
        ),
        make_context(
            freshness="FRESHNESS_UNRESOLVED"
        ),
    )

    for context in unresolved_contexts:
        result = evaluate_schedule(
            schedule=schedule,
            context=context,
        )

        assert status_name(
            result
        ) == "SCHEDULE_UNRESOLVED"


if __name__ == "__main__":
    test_frozen_fixture_manifest_is_complete()

    evaluate_schedule, mutate_schedule = (
        load_schedule_contract()
    )

    fixtures = (
        (
            "A",
            "valid_time_space_and_context",
            lambda: run_fixture_a(evaluate_schedule),
        ),
        (
            "B",
            "explicit_time_mismatch",
            lambda: run_fixture_b(evaluate_schedule),
        ),
        (
            "C",
            "explicit_space_mismatch",
            lambda: run_fixture_c(evaluate_schedule),
        ),
        (
            "D",
            "effect_time_schedule_change",
            lambda: run_fixture_d(evaluate_schedule),
        ),
        (
            "E",
            "unauthorized_mutation_blocked",
            lambda: run_fixture_e(mutate_schedule),
        ),
        (
            "F",
            "unresolved_current_context",
            lambda: run_fixture_f(evaluate_schedule),
        ),
    )

    for fixture_id, name, run in fixtures:
        run()

        print(
            f"PASS: fixture_{fixture_id}_{name}"
        )

    print(
        "Principle 0 Schedule regression PASS: 6 / 6"
    )
