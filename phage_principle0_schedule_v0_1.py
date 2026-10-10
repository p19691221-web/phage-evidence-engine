"""
Minimal PHAGE Principle 0 Schedule implementation v0.1.

This module implements only the frozen executable regression contract A-F.

It does not implement a production scheduler, trusted clock, storage system,
Emergency Override, Tool Adapter invocation, or production execution.
"""

from copy import deepcopy
from datetime import datetime, time
from typing import Any

from phage_authority_engine_v0_1 import AuthorityStatus


SCHEDULE_MATCH = "SCHEDULE_MATCH"
SCHEDULE_NO_MATCH = "SCHEDULE_NO_MATCH"
SCHEDULE_UNRESOLVED = "SCHEDULE_UNRESOLVED"


_STATUS_BY_NAME = {member.name: member for member in AuthorityStatus}


def _normalize_authority_status(value: Any, field: str) -> AuthorityStatus:
    """Authority-status type boundary (decision record v0.1 rev 2, D1, D2, D5).

    Same rule as the Emergency Override module: exact AuthorityStatus member or
    exact canonical str; everything else raises ValueError without touching the
    value. Only an unknown exact str is echoed in the message.
    """
    if type(value) is AuthorityStatus:
        return value
    if type(value) is str:
        member = _STATUS_BY_NAME.get(value)
        if member is not None:
            return member
        raise ValueError(f"unknown {field}: {value}")
    raise ValueError(f"invalid {field}")


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def evaluate_schedule(
    *,
    schedule: dict | None,
    context: dict | None,
) -> str:
    """
    Evaluate the frozen Principle 0 Schedule boundary.

    MATCH requires sufficiently resolved, fresh context and explicit agreement
    across the required schedule dimensions.

    Missing or stale observations remain UNRESOLVED rather than being converted
    into a clean negative.
    """

    if schedule is None or context is None:
        return SCHEDULE_UNRESOLVED

    required_schedule_keys = {
        "schedule_id",
        "version",
        "time_rule",
        "space_ref",
        "context_constraints",
        "effective_from",
        "effective_until",
        "source_ref",
    }

    if not required_schedule_keys.issubset(schedule):
        return SCHEDULE_UNRESOLVED

    required_context_keys = {
        "observed_at",
        "space_ref",
        "context_state",
        "observation_freshness",
    }

    if not required_context_keys.issubset(context):
        return SCHEDULE_UNRESOLVED

    if context["observation_freshness"] != "FRESH":
        return SCHEDULE_UNRESOLVED

    observed_at = context["observed_at"]

    if not isinstance(observed_at, datetime):
        return SCHEDULE_UNRESOLVED

    effective_from = schedule["effective_from"]
    effective_until = schedule["effective_until"]

    if not isinstance(effective_from, datetime):
        return SCHEDULE_UNRESOLVED

    if not isinstance(effective_until, datetime):
        return SCHEDULE_UNRESOLVED

    if observed_at < effective_from or observed_at > effective_until:
        return SCHEDULE_NO_MATCH

    time_rule = schedule["time_rule"]

    if not isinstance(time_rule, dict):
        return SCHEDULE_UNRESOLVED

    if not {"start", "end"}.issubset(time_rule):
        return SCHEDULE_UNRESOLVED

    try:
        start_time = _parse_hhmm(time_rule["start"])
        end_time = _parse_hhmm(time_rule["end"])
    except (AttributeError, TypeError, ValueError):
        return SCHEDULE_UNRESOLVED

    current_time = observed_at.time().replace(tzinfo=None)

    if current_time < start_time or current_time > end_time:
        return SCHEDULE_NO_MATCH

    if context["space_ref"] != schedule["space_ref"]:
        return SCHEDULE_NO_MATCH

    constraints = schedule["context_constraints"]

    if not isinstance(constraints, dict):
        return SCHEDULE_UNRESOLVED

    if "context_state" not in constraints:
        return SCHEDULE_UNRESOLVED

    if context["context_state"] != constraints["context_state"]:
        return SCHEDULE_NO_MATCH

    return SCHEDULE_MATCH


def mutate_schedule(
    *,
    schedule: dict,
    mutation: dict,
    authority_status: Any,
) -> dict:
    """
    Enforce the frozen unauthorized-mutation boundary.

    Fixture E requires existing Authority failure semantics to block mutation
    and leave the ScheduleDefinition unchanged.
    """

    # D5: validate before deepcopy and before the authorized branch.
    authority_status = _normalize_authority_status(authority_status, "authority_status")
    schedule_before = deepcopy(schedule)

    if authority_status is not AuthorityStatus.CLEAN:
        return {
            "mutation_status": "BLOCKED",
            "schedule_after": schedule_before,
            "authority_status": authority_status,
        }

    raise NotImplementedError(
        "Authorized Schedule mutation is outside the frozen A-F v0.1 "
        "regression scope."
    )
