"""RED tests: Principle 0 authority-status type boundary.

Contract: PHAGE_PRINCIPLE0_AUTHORITY_STATUS_TYPE_DECISION_v0_1.md rev 2
(merged in #104), cases K1-K3, R1-R7 (evaluate_override) and M1-M5
(mutate_schedule). Scope is the authority-status input only.

Not in CI yet (decision §5): the fix PR enables it. Hook recorders are cleared
after inputs are built and immediately before each call.
"""
import enum
import types
import unittest

from phage_authority_engine_v0_1 import AuthorityStatus
from phage_principle0_emergency_override_v0_1 import evaluate_override
from phage_principle0_schedule_v0_1 import mutate_schedule
from test_phage_principle0_emergency_override_v0_1 import (
    make_override_grant, make_request)

RECORDER = []
DEEPCOPY_CALLS = []
MISSING = object()

INVALID_OVERRIDE = 'invalid ordinary_authority_status'
INVALID_MUTATE = 'invalid authority_status'
NON_CLEAN = [AuthorityStatus.AUTHORITY_UNRESOLVED, AuthorityStatus.AUTHORITY_SCOPE_VIOLATION,
             AuthorityStatus.AUTHORITY_REVOKED, AuthorityStatus.AUTHORITY_EXPIRED]


# --- rejected inputs ----------------------------------------------------------

class HookStr(str):
    def __hash__(self):
        RECORDER.append(('HookStr', '__hash__'))
        return str.__hash__(self)

    def __eq__(self, other):
        RECORDER.append(('HookStr', '__eq__'))
        return str.__eq__(self, other)

    def __str__(self):
        RECORDER.append(('HookStr', '__str__'))
        return str.__str__(self)


class LyingStr(str):
    def __hash__(self):
        RECORDER.append(('LyingStr', '__hash__'))
        return hash('CLEAN')

    def __eq__(self, other):
        RECORDER.append(('LyingStr', '__eq__'))
        return True

    def __str__(self):
        RECORDER.append(('LyingStr', '__str__'))
        return 'CLEAN'


class RaisingHashStr(str):
    def __hash__(self):
        RECORDER.append(('RaisingHashStr', '__hash__'))
        raise RuntimeError('hash fault')


class SideEffectStr(str):
    touched = []

    def __hash__(self):
        RECORDER.append(('SideEffectStr', '__hash__'))
        SideEffectStr.touched.append('touched')
        return str.__hash__(self)


class ForeignStatus(enum.Enum):
    CLEAN = 'CLEAN'


class StrSaysClean:
    def __str__(self):
        RECORDER.append(('StrSaysClean', '__str__'))
        return 'CLEAN'


class NameRaises:
    @property
    def name(self):
        RECORDER.append(('NameRaises', 'name'))
        raise RuntimeError('name fault')


class NamedClean:
    @property
    def name(self):
        RECORDER.append(('NamedClean', 'name'))
        return 'CLEAN'


class ClassSpoof:
    @property
    def __class__(self):
        # isinstance() falls back to reading __class__; record that access so an
        # implementation that probes with isinstance and then rejects still fails.
        RECORDER.append(('ClassSpoof', '__class__'))
        return str

    def __hash__(self):
        RECORDER.append(('ClassSpoof', '__hash__'))
        return hash('CLEAN')

    def __eq__(self, other):
        RECORDER.append(('ClassSpoof', '__eq__'))
        return True


def r3_values():
    return [1, 0, b'CLEAN', ['CLEAN'], {'name': 'CLEAN'},
            types.SimpleNamespace(name='CLEAN'), NamedClean(), ForeignStatus.CLEAN,
            StrSaysClean(), NameRaises()]


def r4_values():
    return [HookStr('CLEAN'), LyingStr('AUTHORITY_REVOKED'),
            RaisingHashStr('CLEAN'), SideEffectStr('AUTHORITY_REVOKED')]


def r5_values():
    return [ClassSpoof()]


def label(value):
    return value if value is MISSING else '%s:%r' % (type(value).__name__, value)[:60]


# --- harness ------------------------------------------------------------------

def call_override(value, schedule_status='SCHEDULE_NO_MATCH'):
    """Build inputs, clear recorders, call. Returns ('ok', result) or ('raise', exc)."""
    request = make_request(schedule_status=schedule_status, ordinary_authority_status=None)
    if value is MISSING:
        del request['ordinary_authority_status']
    else:
        request['ordinary_authority_status'] = value
    grant = make_override_grant()
    RECORDER.clear()
    try:
        return 'ok', evaluate_override(request=request, override_grant=grant)
    except Exception as error:
        return 'raise', error


class RecordingSchedule(dict):
    """Probe for ordering: records whether deepcopy was reached."""
    def __deepcopy__(self, memo):
        DEEPCOPY_CALLS.append('deepcopy')
        return dict(self)


def call_mutate(value):
    schedule = RecordingSchedule(schedule_id='schedule-OR-7', version='v17')
    snapshot = dict(schedule)
    mutation = {'action': 'MODIFY_SCHEDULE'}
    kwargs = dict(schedule=schedule, mutation=mutation)
    if value is not MISSING:
        kwargs['authority_status'] = value
    RECORDER.clear()
    DEEPCOPY_CALLS.clear()
    try:
        outcome = 'ok', mutate_schedule(**kwargs)
    except Exception as error:
        outcome = 'raise', error
    return outcome, dict(schedule) == snapshot


class Assertions(unittest.TestCase):
    def assert_value_error(self, outcome, message):
        kind, payload = outcome
        self.assertEqual(kind, 'raise', 'expected ValueError, got result %r' % (payload,))
        self.assertIs(type(payload), ValueError,
                      'expected ValueError, got %s: %s' % (type(payload).__name__, payload))
        self.assertEqual(str(payload), message)

    def assert_override(self, outcome, override_status, effect_path, member):
        kind, payload = outcome
        self.assertEqual(kind, 'ok', 'unexpected %r' % (payload,))
        self.assertEqual((payload['override_status'], payload['effect_path']),
                         (override_status, effect_path))
        self.assertIs(payload['authority_status'], member)


# ---------------------------------------------------------------------------
# evaluate_override
# ---------------------------------------------------------------------------

class OverrideAccepted(Assertions):
    def expected(self, member):
        if member is AuthorityStatus.CLEAN:
            return 'OVERRIDE_APPLICABLE', 'NOT_DETERMINED'
        return 'OVERRIDE_NOT_APPLICABLE', 'BLOCKED'

    def test_K1_each_enum_member(self):
        for member in AuthorityStatus:
            with self.subTest(member=member.name):
                outcome = call_override(member)
                self.assert_override(outcome, *self.expected(member), member)
                self.assertEqual(RECORDER, [])

    def test_K2_each_canonical_name_as_exact_str(self):
        for member in AuthorityStatus:
            with self.subTest(name=member.name):
                outcome = call_override(member.name)
                self.assert_override(outcome, *self.expected(member), member)

    def test_K3_unknown_exact_str_keeps_53_message(self):
        self.assert_value_error(call_override('NOT_A_STATUS'),
                                'unknown ordinary_authority_status: NOT_A_STATUS')


class OverrideRejected(Assertions):
    def check_rejected(self, values):
        for value in values:
            with self.subTest(value=label(value)):
                SideEffectStr.touched.clear()
                outcome = call_override(value)
                recorded = list(RECORDER)
                self.assert_value_error(outcome, INVALID_OVERRIDE)
                self.assertEqual(recorded, [])
                self.assertEqual(SideEffectStr.touched, [])

    def test_R1_explicit_none(self):
        self.check_rejected([None])

    def test_R2_missing_key(self):
        self.check_rejected([MISSING])

    def test_R3_non_str_values(self):
        self.check_rejected(r3_values())

    def test_R4_str_subclasses(self):
        self.check_rejected(r4_values())

    def test_R5_class_spoof(self):
        self.check_rejected(r5_values())

    def test_R6_normalization_precedes_schedule_branches(self):
        for status in ['SCHEDULE_UNRESOLVED', 'SCHEDULE_MATCH']:
            for value in [None, MISSING] + r3_values() + r4_values() + r5_values():
                with self.subTest(schedule_status=status, value=label(value)):
                    SideEffectStr.touched.clear()
                    outcome = call_override(value, schedule_status=status)
                    recorded = list(RECORDER)
                    self.assert_value_error(outcome, INVALID_OVERRIDE)
                    self.assertEqual(recorded, [])
                    self.assertEqual(SideEffectStr.touched, [])
        controls = {'SCHEDULE_UNRESOLVED': ('OVERRIDE_UNRESOLVED', 'BLOCKED'),
                    'SCHEDULE_MATCH': ('OVERRIDE_NOT_APPLICABLE', 'NOT_DETERMINED')}
        for status, expected in controls.items():
            for value, member in [(AuthorityStatus.AUTHORITY_REVOKED, AuthorityStatus.AUTHORITY_REVOKED),
                                  ('AUTHORITY_REVOKED', AuthorityStatus.AUTHORITY_REVOKED),
                                  (AuthorityStatus.CLEAN, AuthorityStatus.CLEAN)]:
                with self.subTest(control=status, value=label(value)):
                    self.assert_override(call_override(value, schedule_status=status),
                                         *expected, member)

    def test_R7_every_call_raises_value_error_or_returns_genuine_member(self):
        values = (list(AuthorityStatus) + [m.name for m in AuthorityStatus] + ['NOT_A_STATUS', None, MISSING]
                  + r3_values() + r4_values() + r5_values())
        for status in ['SCHEDULE_NO_MATCH', 'SCHEDULE_UNRESOLVED', 'SCHEDULE_MATCH']:
            for value in values:
                with self.subTest(schedule_status=status, value=label(value)):
                    kind, payload = call_override(value, schedule_status=status)
                    if kind == 'raise':
                        self.assertIs(type(payload), ValueError,
                                      '%s: %s' % (type(payload).__name__, payload))
                    else:
                        self.assertIs(type(payload['authority_status']), AuthorityStatus,
                                      repr(payload['authority_status']))


# ---------------------------------------------------------------------------
# mutate_schedule
# ---------------------------------------------------------------------------

class MutateSchedule(Assertions):
    def test_M1_non_clean_member_and_name_block(self):
        for member in NON_CLEAN:
            for value in [member, member.name]:
                with self.subTest(value=label(value)):
                    (kind, payload), unchanged = call_mutate(value)
                    self.assertEqual(kind, 'ok', 'unexpected %r' % (payload,))
                    self.assertEqual(payload['mutation_status'], 'BLOCKED')
                    self.assertIs(payload['authority_status'], member)
                    self.assertTrue(unchanged)

    def test_M2_clean_keeps_not_implemented(self):
        for value in [AuthorityStatus.CLEAN, 'CLEAN']:
            with self.subTest(value=label(value)):
                (kind, payload), unchanged = call_mutate(value)
                self.assertEqual(kind, 'raise')
                self.assertIs(type(payload), NotImplementedError)
                self.assertTrue(unchanged)

    def test_M3_rejected_before_deepcopy(self):
        for value in [None] + r3_values() + r4_values() + r5_values():
            with self.subTest(value=label(value)):
                SideEffectStr.touched.clear()
                outcome, unchanged = call_mutate(value)
                recorded, copies = list(RECORDER), list(DEEPCOPY_CALLS)
                self.assert_value_error(outcome, INVALID_MUTATE)
                self.assertEqual(recorded, [])
                self.assertEqual(copies, [], 'validation must precede deepcopy')
                self.assertEqual(SideEffectStr.touched, [])
                self.assertTrue(unchanged)

    def test_M4_unknown_exact_str_rejected_before_deepcopy(self):
        outcome, unchanged = call_mutate('NOT_A_STATUS')
        copies = list(DEEPCOPY_CALLS)
        self.assert_value_error(outcome, 'unknown authority_status: NOT_A_STATUS')
        self.assertEqual(copies, [], 'validation must precede deepcopy')
        self.assertTrue(unchanged)

    def test_M5_omitted_argument_is_signature_type_error(self):
        (kind, payload), unchanged = call_mutate(MISSING)
        self.assertEqual(kind, 'raise')
        self.assertIs(type(payload), TypeError)
        self.assertEqual(DEEPCOPY_CALLS, [])
        self.assertTrue(unchanged)


if __name__ == '__main__':
    unittest.main()
