"""

Executable regression contract for PHAGE Trust Evidence Origin v0.1.

G1 — Forged Evidence Origin
G2 — Evidence Verifier Internal Failure

Specification closure does not imply enforcement closure.
"""
import inspect
import importlib


MODULE = "phage_trust_evidence_origin_v0_1"

EVIDENCE_ORIGIN_VERIFIED = "EVIDENCE_ORIGIN_VERIFIED"
EVIDENCE_ORIGIN_UNVERIFIED = "EVIDENCE_ORIGIN_UNVERIFIED"
EVIDENCE_VERIFICATION_ERROR = "EVIDENCE_VERIFICATION_ERROR"

BLOCKED = "BLOCKED"
NOT_DETERMINED = "NOT_DETERMINED"



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
PRODUCER_AUTHORITY_ENTRY_POINT = "produce_trusted_evidence_authorized"


def run_producer_authority_gate_surface(module):
    entry_point = getattr(
        module,
        PRODUCER_AUTHORITY_ENTRY_POINT,
        None,
    )

    assert callable(entry_point), (
        "producer-authority gated entry point is not implemented: "
        f"{PRODUCER_AUTHORITY_ENTRY_POINT}"
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


def run_fixture_g3(module):
    assert module is not None, (
        "G3 contract RED: phage_trust_evidence_origin_v0_1 "
        "is not implemented"
    )

    public_entry = getattr(
        module,
        "evaluate_evidence_origin",
        None,
    )
    assert callable(public_entry), (
        "G3 contract RED: public evidence-origin entry is not implemented"
    )

    original_seam = getattr(
        module,
        "_evaluate_evidence_origin_with_verifier",
        None,
    )
    assert callable(original_seam), (
        "G3 contract RED: verifier enforcement seam is not implemented"
    )

    captured = {}
    sentinel_result = {
        "origin_status": "G3_SENTINEL",
        "effect_path": "G3_SENTINEL",
    }

    def spy(*, candidate, verifier):
        captured["candidate"] = candidate
        captured["verifier"] = verifier
        return sentinel_result

    candidate = _forged_evidence()

    module._evaluate_evidence_origin_with_verifier = spy
    try:
        result = public_entry(candidate=candidate)
    finally:
        module._evaluate_evidence_origin_with_verifier = original_seam

    assert captured.get("candidate") is candidate, (
        "G3 contract RED: public entry did not delegate the original "
        "candidate through verifier seam"
    )
    assert callable(captured.get("verifier")), (
        "G3 contract RED: public entry did not supply a callable "
        "default verifier"
    )
    assert result is sentinel_result, (
        "G3 contract RED: public entry must be a thin wrapper over "
        "the verifier seam"
    )   
def run_fixture_g4(module):
        producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
        assert callable(producer), (
        "G4 characterization: trusted producer path is not implemented"
    )

        evaluate = getattr(
        module,
        "evaluate_evidence_origin",
        None,
    )
        assert callable(evaluate), (
        "G4 characterization: public evidence-origin entry is not implemented"
    )

        candidate = producer(
        value="SCHEDULE_NO_MATCH",
        source="schedule_engine",
        schedule_ref="schedule-OR-7",
        policy_version="v17",
        observed_at="2026-09-09T00:00:00Z",
    )

        result = evaluate(candidate=candidate)

        _assert_result_shape(result)

        assert result["origin_status"] == EVIDENCE_ORIGIN_VERIFIED
        assert result["effect_path"] == NOT_DETERMINED           
def run_fixture_g5(module):
    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer), (
        "G5 contract RED: trusted producer path is not implemented"
    )

    evaluate = getattr(
        module,
        "evaluate_evidence_origin",
        None,
    )
    assert callable(evaluate), (
        "G5 contract RED: public evidence-origin entry is not implemented"
    )

    trusted = producer(
        value="SCHEDULE_NO_MATCH",
        source="schedule_engine",
        schedule_ref="schedule-OR-7",
        policy_version="v17",
        observed_at="2026-09-09T00:00:00Z",
    )

    tampered = dict(trusted)
    tampered["value"] = "SCHEDULE_MATCH"

    result = evaluate(candidate=tampered)

    _assert_result_shape(result)

    assert result["origin_status"] == EVIDENCE_ORIGIN_UNVERIFIED, (
        "G5 contract RED: post-production content mutation retained "
        "verified origin"
    )
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
                (
            "G3",
            "public_entry_uses_verifier_seam",
            lambda: run_fixture_g3(module),
        ),
                (
            "G4",
            "trusted_producer_positive_origin",
            lambda: run_fixture_g4(module),
        ),
    
    
                (
            "G5",
            "post_production_evidence_tamper",
            lambda: run_fixture_g5(module),
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
        run_producer_authority_gate_surface(module)
        run_producer_authority_unresolved_red(module)
        
        run_producer_authority_authorized_red(module)
        run_producer_authority_revoked_red(module)
        run_producer_authority_unknown_behavior(module)
        run_producer_caller_authentication_surface_red(module)
        run_producer_caller_authentication_not_established_red(module)
        run_producer_caller_authentication_established_authorized(module)
def run_producer_authority_revoked_red(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer)

    bindings = getattr(
        module,
        "_TRUSTED_ORIGIN_BINDINGS",
        None,
    )
    assert isinstance(bindings, dict)

    before_count = len(bindings)

    producer_called = False
    original_producer = producer

    def sentinel_producer(*args, **kwargs):
        nonlocal producer_called
        producer_called = True
        return None

    module._produce_trusted_evidence = sentinel_producer

    try:
        try:
            entry_point(
                authority_status="REVOKED",
                value="SCHEDULE_NO_MATCH",
                source="schedule_engine",
                schedule_ref="schedule-OR-7",
                policy_version="v17",
                observed_at="2026-09-09T00:00:00Z",
            )
        except NotImplementedError as exc:
            raise AssertionError(
                "revoked producer-authority behavior is not implemented"
            ) from exc
    finally:
        module._produce_trusted_evidence = original_producer

    assert producer_called is False, (
        "REVOKED producer authority must fail closed before "
        "_produce_trusted_evidence"
    )

    assert len(bindings) == before_count, (
        "REVOKED producer authority must not create trusted-origin bindings"
    )    
def run_producer_authority_unresolved_red(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer)

    bindings = getattr(
        module,
        "_TRUSTED_ORIGIN_BINDINGS",
        None,
    )
    assert isinstance(bindings, dict)

    before_count = len(bindings)

    producer_called = False
    original_producer = producer

    def sentinel_producer(*args, **kwargs):
        nonlocal producer_called
        producer_called = True
        return None

    module._produce_trusted_evidence = sentinel_producer

    try:
        try:
            entry_point(
                authority_status="UNRESOLVED",
                value="SCHEDULE_NO_MATCH",
                source="schedule_engine",
                schedule_ref="schedule-OR-7",
                policy_version="v17",
                observed_at="2026-09-09T00:00:00Z",
            )
        except NotImplementedError as exc:
            raise AssertionError(
                "unresolved producer-authority behavior is not implemented"
            ) from exc
    finally:
        module._produce_trusted_evidence = original_producer

    assert producer_called is False, (
        "unresolved producer authority must fail closed before "
        "_produce_trusted_evidence"
    )

    assert len(bindings) == before_count, (
        "unresolved producer authority must not create trusted-origin bindings"
    )
def run_producer_authority_authorized_red(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer)

    evaluate = getattr(
        module,
        "evaluate_evidence_origin",
        None,
    )
    assert callable(evaluate)

    bindings = getattr(
        module,
        "_TRUSTED_ORIGIN_BINDINGS",
        None,
    )
    assert isinstance(bindings, dict)

    before_keys = set(bindings)

    producer_call_count = 0
    producer_result = None
    original_producer = producer
    def sentinel_producer(*args, **kwargs):
        nonlocal producer_call_count, producer_result
        producer_call_count += 1
        producer_result = original_producer(*args, **kwargs)
        return producer_result

    module._produce_trusted_evidence = sentinel_producer

    try:
        try:
            result = entry_point(
                authority_status="AUTHORIZED",
                value="SCHEDULE_NO_MATCH",
                source="schedule_engine",
                schedule_ref="schedule-OR-7",
                policy_version="v17",
                observed_at="2026-09-09T00:00:00Z",
            )
        except NotImplementedError as exc:
            raise AssertionError(
                "authorized producer-authority behavior is not implemented"
            ) from exc

        assert producer_call_count == 1, (
            "AUTHORIZED producer authority must invoke "
            "_produce_trusted_evidence exactly once"
        )

        assert len(bindings) == len(before_keys) + 1, (
            "AUTHORIZED producer authority must create exactly one "
            "trusted-origin binding"
        )

        assert result is producer_result, (
            "gated entry point must return the trusted producer result"
        )

        evaluated = evaluate(candidate=result)

        _assert_result_shape(evaluated)

        assert evaluated["origin_status"] == EVIDENCE_ORIGIN_VERIFIED
        assert evaluated["effect_path"] == NOT_DETERMINED

    finally:
        module._produce_trusted_evidence = original_producer

        for key in set(bindings) - before_keys:
            bindings.pop(key, None)
def run_producer_authority_unknown_behavior(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer)

    bindings = getattr(
        module,
        "_TRUSTED_ORIGIN_BINDINGS",
        None,
    )
    assert isinstance(bindings, dict)

    before_count = len(bindings)

    producer_called = False
    original_producer = producer

    def sentinel_producer(*args, **kwargs):
        nonlocal producer_called
        producer_called = True
        return None

    module._produce_trusted_evidence = sentinel_producer

    try:
        try:
            entry_point(
                authority_status="UNKNOWN_STATE",
                value="SCHEDULE_NO_MATCH",
                source="schedule_engine",
                schedule_ref="schedule-OR-7",
                policy_version="v17",
                observed_at="2026-09-09T00:00:00Z",
            )
        except NotImplementedError:
            pass
    finally:
        module._produce_trusted_evidence = original_producer

    assert producer_called is False, (
        "unsupported producer authority must fail closed before "
        "_produce_trusted_evidence"
    )

    assert len(bindings) == before_count, (
        "unsupported producer authority must not create trusted-origin bindings"
    )            
def run_producer_caller_authentication_surface_red(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    signature = inspect.signature(entry_point)

    assert "caller_authentication_status" in signature.parameters, (
        "caller-authentication surface RED: "
        "produce_trusted_evidence_authorized must expose "
        "caller_authentication_status explicitly"
    )
def run_producer_caller_authentication_not_established_red(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer)

    bindings = getattr(
        module,
        "_TRUSTED_ORIGIN_BINDINGS",
        None,
    )
    assert isinstance(bindings, dict)

    before_count = len(bindings)

    producer_called = False
    original_producer = producer

    def sentinel_producer(*args, **kwargs):
        nonlocal producer_called
        producer_called = True
        return None

    module._produce_trusted_evidence = sentinel_producer

    try:
        entry_point(
            authority_status="AUTHORIZED",
            caller_authentication_status="NOT_ESTABLISHED",
            value="SCHEDULE_NO_MATCH",
            source="schedule_engine",
            schedule_ref="schedule-OR-7",
            policy_version="v17",
            observed_at="2026-09-09T00:00:00Z",
        )
    finally:
        module._produce_trusted_evidence = original_producer

    assert producer_called is False, (
        "NOT_ESTABLISHED caller authentication must fail closed before "
        "_produce_trusted_evidence"
    )

    assert len(bindings) == before_count, (
        "NOT_ESTABLISHED caller authentication must not create "
        "trusted-origin bindings"
    )
    
def run_producer_caller_authentication_established_authorized(module):
    entry_point = getattr(
        module,
        "produce_trusted_evidence_authorized",
        None,
    )
    assert callable(entry_point)

    producer = getattr(
        module,
        "_produce_trusted_evidence",
        None,
    )
    assert callable(producer)

    evaluate = getattr(
        module,
        "evaluate_evidence_origin",
        None,
    )
    assert callable(evaluate)

    bindings = getattr(
        module,
        "_TRUSTED_ORIGIN_BINDINGS",
        None,
    )
    assert isinstance(bindings, dict)

    before_keys = set(bindings)

    producer_call_count = 0
    producer_result = None
    original_producer = producer

    def sentinel_producer(*args, **kwargs):
        nonlocal producer_call_count, producer_result
        producer_call_count += 1
        producer_result = original_producer(*args, **kwargs)
        return producer_result

    module._produce_trusted_evidence = sentinel_producer

    try:
        result = entry_point(
            caller_authentication_status="ESTABLISHED",
            authority_status="AUTHORIZED",
            value="SCHEDULE_NO_MATCH",
            source="schedule_engine",
            schedule_ref="schedule-OR-7",
            policy_version="v17",
            observed_at="2026-09-09T00:00:00Z",
        )

        assert producer_call_count == 1
        assert len(bindings) == len(before_keys) + 1
        assert result is producer_result

        evaluated = evaluate(candidate=result)
        _assert_result_shape(evaluated)

        assert evaluated["origin_status"] == EVIDENCE_ORIGIN_VERIFIED
        assert evaluated["effect_path"] == NOT_DETERMINED

    finally:
        module._produce_trusted_evidence = original_producer

        for key in set(bindings) - before_keys:
            bindings.pop(key, None)
if __name__ == "__main__":
        run()
