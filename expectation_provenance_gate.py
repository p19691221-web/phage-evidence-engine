"""Expectation provenance boundary; no E/O delta computation.

Authority registry trust and principal independence are caller-supplied
assumptions. This module does not establish institutional legitimacy.
"""
from dataclasses import dataclass
from gate import GateState
import gate


@dataclass(frozen=True)
class ExpectationAuthorityDependency:
    expectation_set_id: str
    dependency_type: str = "EXPECTATION_AUTHORITY_UNRESOLVED"


@dataclass(frozen=True)
class UnresolvedExpectationResult:
    evidence_id: str
    open_dependencies: tuple[ExpectationAuthorityDependency, ...]
    state: GateState = GateState.UNRESOLVED
    evaluation_started: bool = False


def _canonical_actor(value, identities):
    return (
        type(value) is str
        and value.isascii()
        and value in identities
    )


def _supported(binding, provenance, registry, identities):
    if not all(type(x) is dict for x in
               (binding, provenance, registry)):
        return False
    actor = binding.get("governed_actor")
    proposer = provenance.get("proposed_by")
    approver = provenance.get("approved_by")
    if not all(_canonical_actor(x, identities)
               for x in (actor, proposer, approver)):
        return False
    if approver == actor:
        return False
    if provenance.get("governed_actor") != actor:
        return False
    set_id = binding.get("expectation_set_id")
    if type(set_id) is not str or not set_id:
        return False
    if provenance.get("expectation_set_id") != set_id:
        return False
    approval = provenance.get("approval")
    if type(approval) is not dict:
        return False
    if approval.get("approved_by") != approver:
        return False
    if approval.get("binding") != binding:
        return False
    required = {
        "governed_actor", "action", "object", "expectation_set_id",
        "expectation_version", "expectation_content",
    }
    if set(binding) != required:
        return False
    for key in ("action", "object"):
        if type(binding[key]) is not str or not binding[key]:
            return False
    if type(binding["expectation_version"]) is not int:
        return False
    if binding["expectation_version"] < 1:
        return False
    content = binding["expectation_content"]
    if type(content) is not list or not content:
        return False
    if not all(
        type(row) is list and len(row) == 3
        and all(type(x) is str and x for x in row)
        for row in content
    ):
        return False
    refs = provenance.get("authority_source_refs")
    if type(refs) is not list or not refs:
        return False
    if not all(type(ref) is str and ref for ref in refs):
        return False
    if len(set(refs)) != len(refs):
        return False
    if approval.get("authority_source_refs") != refs:
        return False
    if type(approval.get("id")) is not str or not approval["id"]:
        return False
    for ref in refs:
        source = registry.get(ref)
        if type(source) is not dict:
            return False
        if source.get("id") != ref:
            return False
        if source.get("grantee") != approver:
            return False
        if source.get("permission") != "APPROVE_EXPECTATION_SET":
            return False
        if source.get("binding") != binding:
            return False
    return True


def run_expectation_gate(
    *, binding, provenance, authority_registry, canonical_identities,
    evidence_id, epistemic_cutoff, evidence_store, availability_view,
    downstream_evaluator=None,
):
    """Registry and identities come from trusted assessment policy.

    Authenticity and real-world legitimacy remain external assumptions.
    """
    if not _supported(
        binding, provenance, authority_registry, canonical_identities
    ):
        set_id = (
            binding.get("expectation_set_id", "")
            if type(binding) is dict else ""
        )
        return UnresolvedExpectationResult(
            evidence_id=evidence_id,
            open_dependencies=(
                ExpectationAuthorityDependency(set_id),
            ),
        )
    return gate.run_gate(
        evidence_id=evidence_id,
        epistemic_cutoff=epistemic_cutoff,
        evidence_store=evidence_store,
        availability_view=availability_view,
        downstream_evaluator=downstream_evaluator,
    )
