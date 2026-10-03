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
            m._TRUSTED_ORIGIN_BINDINGS.pop(candidate[m._TRUST_MARKER_KEY], None)


if __name__ == "__main__":
    unittest.main()
