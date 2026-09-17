"""
PHAGE Applicable Evidence Reuse v0.1.

Interface-only scaffold.

This module intentionally does NOT implement reuse enforcement yet.
Its purpose is to satisfy the frozen module/entry-point surface while
leaving G6A as a meaningful semantic RED.
"""


def evaluate_applicable_evidence_reuse(*args, **kwargs):
    raise NotImplementedError(
        "public applicable-evidence-reuse orchestration is not implemented"
    )


def _evaluate_applicable_evidence_reuse_from_verified_facts(
    *,
    verified_facts,
):
    raise NotImplementedError(
        "G6A applicable-evidence-reuse semantics are not implemented"
    )
