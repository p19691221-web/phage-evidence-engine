"""RED tests for the proposed optional diagnostic output contract."""
import unittest
from unittest.mock import patch
import phage_trust_evidence_origin_v0_1 as m


class ProducerVerifierContract(unittest.TestCase):
    def invoke(self, diagnostics):
        return m.produce_trusted_evidence_authorized(
            authority_status="AUTHORIZED",
            caller_authentication_evidence=m._CALLER_AUTHENTICATION_VERIFIED_FIXTURE,
            authority_evidence=m._PRODUCER_AUTHORITY_VERIFIED_FIXTURE,
            diagnostics=diagnostics,
            value="SCHEDULE_NO_MATCH", source="schedule_engine",
            schedule_ref="schedule-OR-7", policy_version="v17",
            observed_at="2026-09-09T00:00:00Z",
        )

    def denied(self, auth, authority, expected_auth, expected_authority, reason):
        before = len(m._TRUSTED_ORIGIN_BINDINGS)
        events = []
        diagnostics = {"authentication_status": "ESTABLISHED",
                       "authority_status": "AUTHORIZED", "reason": "caller claim"}

        def authenticate(*args, **kwargs):
            events.append("authentication")
            if isinstance(auth, Exception):
                raise auth
            return auth

        def authorize(*args, **kwargs):
            events.append("authority")
            if isinstance(authority, Exception):
                raise authority
            return authority

        with patch.object(m, "verify_caller_authentication", authenticate), \
             patch.object(m, "verify_producer_authority", authorize), \
             patch.object(m, "_produce_trusted_evidence") as producer:
            try:
                result = self.invoke(diagnostics)
            except Exception as exc:
                self.fail("verifier failure escaped: " + type(exc).__name__)
            self.assertIsNone(result)
            producer.assert_not_called()
        self.assertEqual(len(m._TRUSTED_ORIGIN_BINDINGS), before)
        self.assertEqual(events, ["authentication"] if expected_auth != "ESTABLISHED"
                         else ["authentication", "authority"])
        self.assertEqual(diagnostics, {
            "authentication_status": expected_auth,
            "authority_status": expected_authority, "reason": reason})

    def test_authentication_failure_skips_authority(self):
        self.denied("NOT_ESTABLISHED", "AUTHORIZED", "NOT_ESTABLISHED",
                    "not_evaluated", "AUTHENTICATION_NOT_ESTABLISHED")

    def test_authentication_exception_skips_authority(self):
        self.denied(RuntimeError("auth fault"), "AUTHORIZED", "VERIFICATION_ERROR",
                    "not_evaluated", "AUTHENTICATION_VERIFICATION_ERROR")

    def test_authentication_bad_result_skips_authority(self):
        self.denied("UNEXPECTED", "AUTHORIZED", "VERIFICATION_ERROR",
                    "not_evaluated", "AUTHENTICATION_VERIFICATION_ERROR")

    def test_authentication_reported_error_skips_authority(self):
        self.denied("VERIFICATION_ERROR", "AUTHORIZED", "VERIFICATION_ERROR",
                    "not_evaluated", "AUTHENTICATION_VERIFICATION_ERROR")

    def test_authority_revoked_preserved(self):
        self.denied("ESTABLISHED", "REVOKED", "ESTABLISHED", "REVOKED",
                    "AUTHORITY_REVOKED")

    def test_authority_unresolved_preserved(self):
        self.denied("ESTABLISHED", "UNRESOLVED", "ESTABLISHED", "UNRESOLVED",
                    "AUTHORITY_UNRESOLVED")

    def test_authority_unknown_preserved(self):
        self.denied("ESTABLISHED", "UNKNOWN", "ESTABLISHED", "UNKNOWN",
                    "AUTHORITY_UNKNOWN")

    def test_authority_exception_distinguished(self):
        self.denied("ESTABLISHED", RuntimeError("authority fault"), "ESTABLISHED",
                    "VERIFICATION_ERROR", "AUTHORITY_VERIFICATION_ERROR")

    def test_authority_bad_result_distinguished(self):
        self.denied("ESTABLISHED", "UNEXPECTED", "ESTABLISHED",
                    "VERIFICATION_ERROR", "AUTHORITY_VERIFICATION_ERROR")

    def test_authority_reported_error_distinguished(self):
        self.denied("ESTABLISHED", "VERIFICATION_ERROR", "ESTABLISHED",
                    "VERIFICATION_ERROR", "AUTHORITY_VERIFICATION_ERROR")

    def test_positive_sequence_and_diagnostic_isolation(self):
        events = []
        diagnostics = {}
        before = len(m._TRUSTED_ORIGIN_BINDINGS)
        original = m._produce_trusted_evidence

        def authenticate(*args, **kwargs):
            events.append("authentication")
            return "ESTABLISHED"

        def authorize(*args, **kwargs):
            events.append("authority")
            return "AUTHORIZED"

        def produce(**kwargs):
            events.append("producer")
            self.assertNotIn("diagnostics", kwargs)
            return original(**kwargs)

        with patch.object(m, "verify_caller_authentication", authenticate), \
             patch.object(m, "verify_producer_authority", authorize), \
             patch.object(m, "_produce_trusted_evidence", produce):
            candidate = self.invoke(diagnostics)
        try:
            self.assertEqual(events, ["authentication", "authority", "producer"])
            self.assertEqual(len(m._TRUSTED_ORIGIN_BINDINGS), before + 1)
            self.assertNotIn("diagnostics", candidate)
            self.assertEqual(diagnostics, {
                "authentication_status": "ESTABLISHED",
                "authority_status": "AUTHORIZED",
                "reason": "VERIFIED_PRODUCTION_PERMITTED"})
            self.assertEqual(m.evaluate_evidence_origin(candidate=candidate)
                             ["origin_status"], m.EVIDENCE_ORIGIN_VERIFIED)
        finally:
            if isinstance(candidate, dict):
                m._TRUSTED_ORIGIN_BINDINGS.pop(
                    candidate.get(m._TRUST_MARKER_KEY), None)

    def test_default_path_verifier_errors_are_observable(self):
        for stage in ("authentication", "authority"):
            for failure in (RuntimeError("fault"), "VERIFICATION_ERROR",
                            "UNEXPECTED"):
                with self.subTest(stage=stage, failure=repr(failure)):
                    before = len(m._TRUSTED_ORIGIN_BINDINGS)
                    auth_result = "ESTABLISHED"
                    authority_result = "AUTHORIZED"
                    target = ({"side_effect": failure} if isinstance(failure, Exception)
                              else {"return_value": failure})
                    auth_args = (target if stage == "authentication"
                                 else {"return_value": auth_result})
                    authority_args = (target if stage == "authority"
                                      else {"return_value": authority_result})
                    with patch.object(m, "verify_caller_authentication",
                                      **auth_args) as authenticate, \
                         patch.object(m, "verify_producer_authority",
                                      **authority_args) as authorize, \
                         patch.object(m, "_produce_trusted_evidence") as producer:
                        with self.assertRaises(m.ProducerVerificationError) as caught:
                            self.invoke(None)
                        self.assertEqual(caught.exception.stage, stage)
                        self.assertIsNone(caught.exception.__cause__)
                        self.assertIsNone(caught.exception.__context__)
                        self.assertEqual(caught.exception.reason,
                                         stage.upper() + "_VERIFICATION_ERROR")
                        authenticate.assert_called_once()
                        if stage == "authentication":
                            authorize.assert_not_called()
                        else:
                            authorize.assert_called_once()
                        producer.assert_not_called()
                    self.assertEqual(len(m._TRUSTED_ORIGIN_BINDINGS), before)

    def test_default_path_ordinary_denial_remains_none(self):
        with patch.object(m, "verify_caller_authentication",
                          return_value="NOT_ESTABLISHED"), \
             patch.object(m, "verify_producer_authority") as authority, \
             patch.object(m, "_produce_trusted_evidence") as producer:
            self.assertIsNone(self.invoke(None))
            authority.assert_not_called()
            producer.assert_not_called()

    def test_supported_caller_status_does_not_override_verifier(self):
        for status in ("AUTHORIZED", "REVOKED", "UNRESOLVED"):
            with self.subTest(status=status):
                sentinel = object()
                diagnostics = {}
                with patch.object(m, "_produce_trusted_evidence",
                                  return_value=sentinel) as producer:
                    result = m.produce_trusted_evidence_authorized(
                        authority_status=status,
                        caller_authentication_evidence=
                            m._CALLER_AUTHENTICATION_VERIFIED_FIXTURE,
                        authority_evidence=m._PRODUCER_AUTHORITY_VERIFIED_FIXTURE,
                        diagnostics=diagnostics)
                self.assertIs(result, sentinel)
                producer.assert_called_once()
                self.assertEqual(diagnostics["authority_status"], "AUTHORIZED")

    def test_invalid_sink_rejected_before_verification(self):
        class DictSubclass(dict):
            pass
        for sink in ([], 1, "sink", DictSubclass()):
            with self.subTest(sink=repr(sink)), \
                 patch.object(m, "verify_caller_authentication") as auth, \
                 patch.object(m, "verify_producer_authority") as authority, \
                 patch.object(m, "_produce_trusted_evidence") as producer:
                with self.assertRaises(TypeError):
                    self.invoke(sink)
                auth.assert_not_called()
                authority.assert_not_called()
                producer.assert_not_called()

    def test_binding_registry_rejected_as_sink_without_mutation(self):
        original = dict(m._TRUSTED_ORIGIN_BINDINGS)
        token = object()
        m._TRUSTED_ORIGIN_BINDINGS[token] = ("existing binding",)
        expected = dict(m._TRUSTED_ORIGIN_BINDINGS)
        try:
            with patch.object(m, "verify_caller_authentication") as auth, \
                 patch.object(m, "verify_producer_authority") as authority, \
                 patch.object(m, "_produce_trusted_evidence") as producer:
                with self.assertRaises(TypeError):
                    self.invoke(m._TRUSTED_ORIGIN_BINDINGS)
                auth.assert_not_called()
                authority.assert_not_called()
                producer.assert_not_called()
            self.assertEqual(m._TRUSTED_ORIGIN_BINDINGS, expected)
        finally:
            m._TRUSTED_ORIGIN_BINDINGS.clear()
            m._TRUSTED_ORIGIN_BINDINGS.update(original)

    def test_module_globals_rejected_without_mutation(self):
        snapshot = dict(vars(m))
        with patch.object(m, "verify_caller_authentication") as auth, \
             patch.object(m, "verify_producer_authority") as authority, \
             patch.object(m, "_produce_trusted_evidence") as producer:
            with self.assertRaises(TypeError):
                self.invoke(vars(m))
            auth.assert_not_called()
            authority.assert_not_called()
            producer.assert_not_called()
        self.assertEqual(vars(m), snapshot)

    def test_trusted_candidate_rejected_without_mutation(self):
        candidate = m._produce_trusted_evidence(
            value="SCHEDULE_NO_MATCH", source="schedule_engine",
            schedule_ref="schedule-OR-7", policy_version="v17",
            observed_at="2026-09-09T00:00:00Z")
        snapshot = dict(candidate)
        bindings = dict(m._TRUSTED_ORIGIN_BINDINGS)
        token = candidate[m._TRUST_MARKER_KEY]
        try:
            with patch.object(m, "verify_caller_authentication") as auth, \
                 patch.object(m, "verify_producer_authority") as authority, \
                 patch.object(m, "_produce_trusted_evidence") as producer:
                with self.assertRaises(TypeError):
                    self.invoke(candidate)
                auth.assert_not_called()
                authority.assert_not_called()
                producer.assert_not_called()
            self.assertEqual(candidate, snapshot)
            self.assertEqual(m._TRUSTED_ORIGIN_BINDINGS, bindings)
            self.assertEqual(m.evaluate_evidence_origin(candidate=candidate)
                             ["origin_status"], m.EVIDENCE_ORIGIN_VERIFIED)
        finally:
            m._TRUSTED_ORIGIN_BINDINGS.pop(token, None)

    def test_unsupported_input_does_not_write_diagnostics(self):
        diagnostics = {"caller": "unchanged"}
        with patch.object(m, "verify_caller_authentication") as auth, \
             patch.object(m, "verify_producer_authority") as authority, \
             patch.object(m, "_produce_trusted_evidence") as producer:
            with self.assertRaises(NotImplementedError):
                m.produce_trusted_evidence_authorized(
                    authority_status="UNKNOWN_STATE", diagnostics=diagnostics)
            self.assertEqual(diagnostics, {"caller": "unchanged"})
            auth.assert_not_called()
            authority.assert_not_called()
            producer.assert_not_called()

    def test_output_clears_extra_keys_and_permission_is_gate_only(self):
        diagnostics = {"extra": "remove me", "authority_status": "REVOKED"}
        with patch.object(m, "_produce_trusted_evidence",
                          side_effect=RuntimeError("production failed")) as producer:
            with self.assertRaisesRegex(RuntimeError, "production failed"):
                self.invoke(diagnostics)
            producer.assert_called_once()
        self.assertEqual(diagnostics, {
            "authentication_status": "ESTABLISHED",
            "authority_status": "AUTHORIZED",
            "reason": "VERIFIED_PRODUCTION_PERMITTED"})


if __name__ == "__main__":
    unittest.main()
