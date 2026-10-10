"""Characterization of Principle 0 authority-status input typing (reproduction only).

Baseline: main 6eb0ee2. Asserts CURRENT behavior so each gap is reproducible;
no Principle 0 implementation is changed. A later fix is expected to turn the
`observed_gap` assertions into failures, at which point this file is replaced
by RED tests for the agreed contract.

Not a test_* module and not referenced by any workflow: it is evidence, not a
regression gate. Run: python -m unittest -v repro_principle0_authority_status_type_v0_1
"""
import enum
import re
import types
import unittest
from copy import deepcopy
from pathlib import Path

from phage_authority_engine_v0_1 import AuthorityStatus
from phage_principle0_emergency_override_v0_1 import evaluate_override
from phage_principle0_schedule_v0_1 import mutate_schedule
from test_phage_principle0_emergency_override_v0_1 import (
    make_override_grant, make_request)

HERE = Path(__file__).resolve().parent
RECORDER = []
MISSING = object()


# --- hostile / non-canonical inputs -------------------------------------------

class HookStr(str):
    """Well-behaved value; records hash/eq."""
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
    """Any value; hashes and compares as 'CLEAN'."""
    def __hash__(self):
        RECORDER.append(('LyingStr', '__hash__'))
        return hash('CLEAN')

    def __eq__(self, other):
        RECORDER.append(('LyingStr', '__eq__'))
        return True


class RaisingHashStr(str):
    def __hash__(self):
        RECORDER.append(('RaisingHashStr', '__hash__'))
        raise RuntimeError('hash fault')


class SideEffectStr(str):
    """Correct value; mutates external state when hashed."""
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


class ClassSpoof:
    """Not a str; claims to be one via __class__ and collides with 'CLEAN'."""
    @property
    def __class__(self):
        return str

    def __hash__(self):
        RECORDER.append(('ClassSpoof', '__hash__'))
        return hash('CLEAN')

    def __eq__(self, other):
        RECORDER.append(('ClassSpoof', '__eq__'))
        return True


# --- harness ------------------------------------------------------------------

def run_override(value):
    """Build inputs, clear the recorder, then call. Returns (outcome, hooks)."""
    request = make_request(ordinary_authority_status=None)
    if value is MISSING:
        del request['ordinary_authority_status']
    else:
        request['ordinary_authority_status'] = value
    grant = make_override_grant()
    RECORDER.clear()
    try:
        result = evaluate_override(request=request, override_grant=grant)
    except Exception as error:  # characterization records the escape
        return ('RAISE', type(error).__name__), list(RECORDER)
    status = result['authority_status']
    return (result['override_status'], result['effect_path'],
            type(status).__name__, status is AuthorityStatus.CLEAN), list(RECORDER)


def run_mutation(value):
    schedule = {'schedule_id': 'schedule-OR-7', 'version': 'v17'}
    before = deepcopy(schedule)
    RECORDER.clear()
    try:
        result = mutate_schedule(schedule=schedule, mutation={'action': 'MODIFY_SCHEDULE'},
                                 authority_status=value)
    except Exception as error:
        return ('RAISE', type(error).__name__, schedule == before), list(RECORDER)
    return (result['mutation_status'], schedule == before), list(RECORDER)


APPLICABLE = 'OVERRIDE_APPLICABLE'
NOT_APPLICABLE = 'OVERRIDE_NOT_APPLICABLE'


class OverrideCanonicalControls(unittest.TestCase):
    """Exact canonical inputs: current contract, expected to be kept."""

    def test_enum_clean_applies(self):
        self.assertEqual(run_override(AuthorityStatus.CLEAN),
                         ((APPLICABLE, 'NOT_DETERMINED', 'AuthorityStatus', True), []))

    def test_exact_str_clean_applies(self):
        self.assertEqual(run_override('CLEAN'),
                         ((APPLICABLE, 'NOT_DETERMINED', 'AuthorityStatus', True), []))

    def test_exact_str_revoked_blocks(self):
        self.assertEqual(run_override('AUTHORITY_REVOKED'),
                         ((NOT_APPLICABLE, 'BLOCKED', 'AuthorityStatus', False), []))

    def test_exact_str_unknown_raises_value_error(self):
        self.assertEqual(run_override('NOT_A_STATUS'), (('RAISE', 'ValueError'), []))


class OverrideNoneAndMissing(unittest.TestCase):
    def test_explicit_none_blocks_but_passes_none_through(self):
        self.assertEqual(run_override(None),
                         ((NOT_APPLICABLE, 'BLOCKED', 'NoneType', False), []))

    def test_missing_key_is_indistinguishable_from_none(self):
        self.assertEqual(run_override(MISSING), run_override(None))


class OverrideNonStrValues(unittest.TestCase):
    def test_observed_blocks_with_raw_passthrough(self):
        for value in [1, 0, b'CLEAN', ['CLEAN'], {'name': 'CLEAN'}]:
            with self.subTest(value=value):
                outcome, hooks = run_override(value)
                self.assertEqual(outcome[:2], (NOT_APPLICABLE, 'BLOCKED'))
                self.assertEqual(outcome[2], type(value).__name__)   # raw object in result
                self.assertEqual(hooks, [])

    def test_observed_gap_forged_clean_by_name_attribute(self):
        for value in [types.SimpleNamespace(name='CLEAN'), ForeignStatus.CLEAN]:
            with self.subTest(value=type(value).__name__):
                outcome, _ = run_override(value)
                self.assertEqual(outcome, (APPLICABLE, 'NOT_DETERMINED',
                                           type(value).__name__, False))

    def test_observed_gap_forged_clean_by_str_method(self):
        self.assertEqual(run_override(StrSaysClean()),
                         ((APPLICABLE, 'NOT_DETERMINED', 'StrSaysClean', False),
                          [('StrSaysClean', '__str__')]))

    def test_observed_gap_name_property_exception_escapes(self):
        self.assertEqual(run_override(NameRaises()),
                         (('RAISE', 'RuntimeError'), [('NameRaises', 'name')]))

    def test_observed_gap_class_spoof_laundered_to_genuine_clean(self):
        outcome, hooks = run_override(ClassSpoof())
        self.assertEqual(outcome, (APPLICABLE, 'NOT_DETERMINED', 'AuthorityStatus', True))
        self.assertIn(('ClassSpoof', '__hash__'), hooks)


class OverrideStrSubclasses(unittest.TestCase):
    def test_observed_gap_hooks_run_for_well_behaved_subclass(self):
        outcome, hooks = run_override(HookStr('CLEAN'))
        self.assertEqual(outcome, (APPLICABLE, 'NOT_DETERMINED', 'AuthorityStatus', True))
        self.assertIn(('HookStr', '__hash__'), hooks)

    def test_observed_gap_revoked_laundered_to_genuine_clean(self):
        outcome, hooks = run_override(LyingStr('AUTHORITY_REVOKED'))
        self.assertEqual(outcome, (APPLICABLE, 'NOT_DETERMINED', 'AuthorityStatus', True))
        self.assertIn(('LyingStr', '__hash__'), hooks)

    def test_observed_gap_hash_exception_escapes(self):
        self.assertEqual(run_override(RaisingHashStr('CLEAN')),
                         (('RAISE', 'RuntimeError'), [('RaisingHashStr', '__hash__')]))

    def test_observed_gap_hook_side_effect(self):
        SideEffectStr.touched.clear()
        outcome, _ = run_override(SideEffectStr('AUTHORITY_REVOKED'))
        self.assertEqual(outcome[:2], (NOT_APPLICABLE, 'BLOCKED'))
        self.assertEqual(SideEffectStr.touched, ['touched'])


class MutateScheduleTyping(unittest.TestCase):
    def test_canonical_controls(self):
        self.assertEqual(run_mutation(AuthorityStatus.AUTHORITY_REVOKED), (('BLOCKED', True), []))
        self.assertEqual(run_mutation(None), (('BLOCKED', True), []))
        # Authorized mutation is outside v0.1 scope: CLEAN raises by design.
        self.assertEqual(run_mutation(AuthorityStatus.CLEAN),
                         (('RAISE', 'NotImplementedError', True), []))

    def test_observed_gap_forged_clean_reaches_authorized_branch(self):
        for value in [types.SimpleNamespace(name='CLEAN'), ForeignStatus.CLEAN,
                      StrSaysClean(), HookStr('CLEAN')]:
            with self.subTest(value=type(value).__name__):
                outcome, _ = run_mutation(value)
                self.assertEqual(outcome, ('RAISE', 'NotImplementedError', True))


class RuntimeReachability(unittest.TestCase):
    """Limited static evidence: repository-root *.py files only, by module name.
    Does not cover subdirectories, non-Python callers, dynamic imports or
    external deployments; it does not establish runtime unreachability."""

    def test_no_non_test_reference_in_root_python_modules(self):
        pattern = re.compile(r'phage_principle0_(emergency_override|schedule)_v0_1')
        importers = sorted(
            path.name for path in HERE.glob('*.py')
            if path.name not in ('phage_principle0_emergency_override_v0_1.py',
                                 'phage_principle0_schedule_v0_1.py')
            and not path.name.startswith(('test_', 'repro_'))
            and pattern.search(path.read_text(encoding='utf-8')))
        self.assertEqual(importers, [])


if __name__ == '__main__':
    unittest.main()
