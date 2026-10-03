"""L/M proposed executable boundary; no implementation in this RED PR."""
import importlib
import unittest
from unittest.mock import Mock, patch

MODULE = "phage_trust_boundary_lm_v0_1"
try:
    lm = importlib.import_module(MODULE)
except ModuleNotFoundError as exc:
    if exc.name != MODULE:
        raise
    lm = None
import phage_trust_evidence_origin_v0_1 as producer


def request():
    return dict(
        authority_status="AUTHORIZED",
        caller_authentication_evidence=producer._CALLER_AUTHENTICATION_VERIFIED_FIXTURE,
        authority_evidence=producer._PRODUCER_AUTHORITY_VERIFIED_FIXTURE,
        value="origin issuance fixture",
        source="lm-regression",
        schedule_ref="fixture-only",
        policy_version="fixture-only",
        observed_at="2026-10-03T08:00:00Z",
    )


class Boundary:
    def setUp(self):
        self.assertIsNotNone(lm, "L/M surface RED: implementation module absent")
        self.issue = getattr(lm, "issue_" + self.kind)
        self.consume = getattr(lm, "consume_" + self.kind)
        self.verify_name = "verify_" + self.kind + "_origin"
        self.bindings = dict(producer._TRUSTED_ORIGIN_BINDINGS)
        self.payload = {"reference": "fixture-1", "outcome": "fixture-observation",
                        "details": {"steps": ["original"]}}

    def tearDown(self):
        # Only remove producer tokens created by this isolated test.
        for token in tuple(producer._TRUSTED_ORIGIN_BINDINGS):
            if token not in self.bindings:
                producer._TRUSTED_ORIGIN_BINDINGS.pop(token)

    def issued(self):
        result = self.issue(payload=self.payload, producer_request=request())
        self.assertEqual(result["producer_diagnostics"]["reason"],
                         "VERIFIED_PRODUCTION_PERMITTED")
        self.assertIsNotNone(result["artifact"])
        return result["artifact"]

    def test_positive_origin_at_use(self):
        artifact = self.issued()
        use = Mock(return_value="observation")
        actual = getattr(lm, self.verify_name)
        events = []
        def checked(value):
            events.append("verify")
            return actual(value)
        def used(payload):
            events.append("use")
            return use(payload)
        with patch.object(lm, self.verify_name, side_effect=checked) as verifier:
            result = self.consume(candidate=artifact, on_verified=used)
        self.assertEqual(result["origin_status"], self.verified)
        self.assertEqual(result["effect_path"], "NOT_DETERMINED")
        self.assertEqual(events, ["verify", "use"])
        verifier.assert_called_once_with(artifact)
        use.assert_called_once_with(self.payload)

    def test_caller_created_object_rejected(self):
        for candidate in (None, self.payload, object(),
                          {"payload": self.payload, "origin_status": self.verified}):
            with self.subTest(candidate=type(candidate).__name__):
                use = Mock()
                result = self.consume(candidate=candidate, on_verified=use)
                self.assertEqual(result["origin_status"], self.unverified)
                self.assertEqual(result["effect_path"], "BLOCKED")
                use.assert_not_called()

    def test_other_artifact_kind_rejected(self):
        other = "audit_receipt" if self.kind == "decision" else "decision"
        artifact = getattr(lm, "issue_" + other)(
            payload=self.payload, producer_request=request())["artifact"]
        self.assertIsNotNone(artifact)
        use = Mock()
        result = self.consume(candidate=artifact, on_verified=use)
        self.assertEqual(result["origin_status"], self.unverified)
        self.assertEqual(result["effect_path"], "BLOCKED")
        use.assert_not_called()

    def test_fault_injection_is_distinct(self):
        artifact = self.issued()
        use = Mock()
        with patch.object(lm, self.verify_name,
                          side_effect=RuntimeError("injected verifier fault")):
            result = self.consume(candidate=artifact, on_verified=use)
        self.assertEqual(result["origin_status"], self.error)
        self.assertEqual(result["effect_path"], "BLOCKED")
        use.assert_not_called()

    def test_verifier_must_return_exact_boolean(self):
        artifact = self.issued()
        for value in ("VERIFIED", 1, None, object()):
            with self.subTest(value=type(value).__name__):
                use = Mock()
                with patch.object(lm, self.verify_name, return_value=value):
                    result = self.consume(candidate=artifact, on_verified=use)
                self.assertEqual(result["origin_status"], self.error)
                self.assertEqual(result["effect_path"], "BLOCKED")
                use.assert_not_called()

    def test_reverify_every_use(self):
        artifact = self.issued()
        use = Mock()
        with patch.object(lm, self.verify_name, side_effect=[True, False]) as verifier:
            first = self.consume(candidate=artifact, on_verified=use)
            second = self.consume(candidate=artifact, on_verified=use)
        self.assertEqual(first["origin_status"], self.verified)
        self.assertEqual(second["origin_status"], self.unverified)
        self.assertEqual(second["effect_path"], "BLOCKED")
        self.assertEqual(verifier.call_count, 2)
        self.assertEqual(use.call_count, 1)

    def test_payload_snapshot_isolated(self):
        artifact = self.issued()
        self.payload["outcome"] = "caller mutation"
        self.payload["details"]["steps"].append("caller mutation")
        seen = []
        result = self.consume(candidate=artifact, on_verified=seen.append)
        self.assertEqual(result["origin_status"], self.verified)
        self.assertEqual(seen[0]["outcome"], "fixture-observation")
        self.assertEqual(seen[0]["details"]["steps"], ["original"])
        seen[0]["outcome"] = "consumer mutation"
        seen[0]["details"]["steps"].append("consumer mutation")
        seen.clear()
        result = self.consume(candidate=artifact, on_verified=seen.append)
        self.assertEqual(result["origin_status"], self.verified)
        self.assertEqual(seen[0]["outcome"], "fixture-observation")

    def test_nested_snapshot_after_consumer_mutation(self):
        artifact = self.issued()
        def mutate(payload):
            payload["details"]["steps"].append("consumer mutation")
        self.consume(candidate=artifact, on_verified=mutate)
        seen = []
        result = self.consume(candidate=artifact, on_verified=seen.append)
        self.assertEqual(result["origin_status"], self.verified)
        self.assertEqual(seen[0]["details"]["steps"], ["original"])

    def test_verified_evidence_is_not_artifact(self):
        candidate = producer.produce_trusted_evidence_authorized(**request())
        self.assertEqual(producer.evaluate_evidence_origin(candidate=candidate)["origin_status"],
                         "EVIDENCE_ORIGIN_VERIFIED")
        use = Mock()
        result = self.consume(candidate=candidate, on_verified=use)
        self.assertEqual(result["origin_status"], self.unverified)
        self.assertEqual(result["effect_path"], "BLOCKED")
        use.assert_not_called()

    def test_callback_exception_propagates(self):
        artifact = self.issued()
        failure = RuntimeError("callback failure")
        use = Mock(side_effect=failure)
        with self.assertRaises(RuntimeError) as caught:
            self.consume(candidate=artifact, on_verified=use)
        self.assertIs(caught.exception, failure)
        use.assert_called_once()

    def test_tampered_content_rejected(self):
        artifact = self.issued()
        getattr(lm, "_tamper_" + self.kind + "_for_test")(
            artifact, payload={"reference": "fixture-1", "outcome": "tampered"})
        use = Mock()
        result = self.consume(candidate=artifact, on_verified=use)
        self.assertEqual(result["origin_status"], self.unverified)
        self.assertEqual(result["effect_path"], "BLOCKED")
        use.assert_not_called()

    def test_payload_requires_plain_dict_before_gate(self):
        class DictSubclass(dict):
            pass
        for payload in (None, [], "payload", DictSubclass(self.payload)):
            with self.subTest(payload=type(payload).__name__):
                with patch.object(producer, "produce_trusted_evidence_authorized") as gate:
                    with self.assertRaises(TypeError):
                        self.issue(payload=payload, producer_request=request())
                gate.assert_not_called()
                self.assertEqual(producer._TRUSTED_ORIGIN_BINDINGS, self.bindings)

    def test_caller_diagnostics_rejected_before_gate(self):
        req = request()
        supplied = {"reason": "caller claim"}
        req["diagnostics"] = supplied
        with patch.object(producer, "produce_trusted_evidence_authorized") as gate:
            with self.assertRaises(TypeError):
                self.issue(payload=self.payload, producer_request=req)
        gate.assert_not_called()
        self.assertEqual(supplied, {"reason": "caller claim"})
        self.assertEqual(producer._TRUSTED_ORIGIN_BINDINGS, self.bindings)

    def test_issuance_evidence_trace_and_dedicated_diagnostics(self):
        issued_candidates = []
        sinks = []
        actual = producer.produce_trusted_evidence_authorized
        def traced(**kwargs):
            sinks.append(kwargs["diagnostics"])
            candidate = actual(**kwargs)
            issued_candidates.append(candidate)
            return candidate
        with patch.object(producer, "produce_trusted_evidence_authorized", side_effect=traced):
            first = self.issued()
            second = self.issued()
        self.assertEqual(len(sinks), 2)
        self.assertIsNot(sinks[0], sinks[1])
        for artifact, candidate in zip((first, second), issued_candidates):
            trace = getattr(lm, "_issuance_provenance_for_test")(artifact)
            self.assertIs(trace["evidence_origin_token"],
                          candidate[producer._TRUST_MARKER_KEY])
            self.assertEqual(trace["artifact_kind"], self.kind)

    def test_authentication_hard_stop_at_issuance(self):
        req = request()
        req["caller_authentication_evidence"] = object()
        with patch.object(producer, "verify_producer_authority") as authority:
            result = self.issue(payload=self.payload, producer_request=req)
        self.assertIsNone(result["artifact"])
        self.assertEqual(result["producer_diagnostics"]["authentication_status"],
                         "NOT_ESTABLISHED")
        self.assertEqual(result["producer_diagnostics"]["authority_status"],
                         "not_evaluated")
        authority.assert_not_called()
        self.assertEqual(producer._TRUSTED_ORIGIN_BINDINGS, self.bindings)

    def test_authority_denials_preserved_at_issuance(self):
        for status in ("UNRESOLVED", "REVOKED", "UNKNOWN"):
            with self.subTest(status=status):
                with patch.object(producer, "verify_producer_authority",
                                  return_value=status):
                    result = self.issue(payload=self.payload, producer_request=request())
                self.assertIsNone(result["artifact"])
                self.assertEqual(result["producer_diagnostics"]["authority_status"], status)
                self.assertEqual(result["producer_diagnostics"]["reason"], "AUTHORITY_" + status)
                self.assertEqual(producer._TRUSTED_ORIGIN_BINDINGS, self.bindings)

    def test_producer_verifier_errors_preserved_at_issuance(self):
        for stage, name in (("authentication", "verify_caller_authentication"),
                            ("authority", "verify_producer_authority")):
            with self.subTest(stage=stage):
                with patch.object(producer, name, side_effect=RuntimeError("injected")):
                    result = self.issue(payload=self.payload, producer_request=request())
                self.assertIsNone(result["artifact"])
                self.assertEqual(result["producer_diagnostics"]["reason"],
                                 stage.upper() + "_VERIFICATION_ERROR")
                self.assertEqual(producer._TRUSTED_ORIGIN_BINDINGS, self.bindings)


class DecisionTests(Boundary, unittest.TestCase):
    kind = "decision"
    verified = "DECISION_ORIGIN_VERIFIED"
    unverified = "DECISION_ORIGIN_UNVERIFIED"
    error = "DECISION_VERIFICATION_ERROR"


class ReceiptTests(Boundary, unittest.TestCase):
    kind = "audit_receipt"
    verified = "AUDIT_ORIGIN_VERIFIED"
    unverified = "AUDIT_ORIGIN_UNVERIFIED"
    error = "AUDIT_VERIFICATION_ERROR"



if __name__ == "__main__":
    unittest.main()
