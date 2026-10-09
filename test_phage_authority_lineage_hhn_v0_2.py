"""RED acceptance tests for the v0.2 inspection entry `resolve_policy_change`.

Frozen interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md.
Acceptance IDs: PHAGE_AUTHORITY_RESOLVER_USE_TIME_CONSISTENCY_CONTRACT_v0_1.md
§8, allocated per interface §9. An absent module is surface RED only.

Carried-forward #92 tests keep their expected reason/status/effect. Mechanical
changes required by the frozen interface: fixtures gain `state_epoch`; calls
pass `current_epoch`; result dicts gain `state_epoch`, `snapshot_at`,
`valid_until` (§5.1). `current_epoch` calls are logged separately so #92 call
sequences stay unchanged.
"""
import importlib
import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import fixture_phage_authority_reference_source_v0_1 as fx
from fixture_phage_authority_reference_source_v0_1 import (
    FIELDS, Collider, OpaqueKey, RECORDER, RecDict, RecInt, RecList, RecStr,
    ReferenceSource, base_request, base_snapshot, count_visits, grant,
    replace_key, visit_boundary_snapshot)

MODULE = 'phage_authority_lineage_hhn_v0_2'
HERE = Path(__file__).resolve().parent


def inputs():
    return base_request(), base_snapshot()


def load(testcase):
    try:
        return importlib.import_module(MODULE)
    except ModuleNotFoundError as error:
        if error.name != MODULE:
            raise
        testcase.fail('SURFACE_RED: %s absent; not behavioral evidence' % MODULE)


def denial(reason):
    status = 'VERIFICATION_ERROR' if reason == 'AUTHORITY_VERIFICATION_ERROR' else 'UNVERIFIED'
    return dict(authorization_status=status, reason=reason, effect_path='BLOCKED',
                request_binding=None, snapshot_id=None, state_epoch=None,
                snapshot_at=None, valid_until=None)


def authorized(request, snapshot_id='s1', state_epoch=0, at=10, valid_until=100):
    return dict(authorization_status='AUTHORIZED', reason='POLICY_CHANGE_AUTHORIZED',
                effect_path='NOT_DETERMINED',
                request_binding=tuple(request[k] for k in FIELDS),
                snapshot_id=snapshot_id, state_epoch=state_epoch,
                snapshot_at=at, valid_until=valid_until)


def run_isolated(worker, payload):
    """Disposable subprocess with a wall-clock timeout (#92 N-test pattern)."""
    completed = subprocess.run([sys.executable, '-c', worker], cwd=HERE,
                               input=json.dumps(payload), capture_output=True,
                               text=True, timeout=5)
    if completed.returncode != 0:
        raise AssertionError('isolated worker failed: ' + completed.stderr)
    return json.loads(completed.stdout)


CYCLE_WORKER = """
import json,sys,importlib
m=importlib.import_module('phage_authority_lineage_hhn_v0_2')
r,s=json.load(sys.stdin); seen=[]
def verify(record,at):
    seen.append(record['id'])
    return 'VERIFIED'
result=m.resolve_policy_change(request=r,authenticate=lambda subject:'ESTABLISHED',
    snapshot_provider=lambda:s,current_epoch=lambda:s['state_epoch'],verify_grant=verify)
print(json.dumps(dict(result=result,seen=seen,request=r,state=s)))
"""

SELF_LIST_WORKER = """
import json,sys,importlib
sys.path.insert(0,'.')
import fixture_phage_authority_reference_source_v0_1 as fx
m=importlib.import_module('phage_authority_lineage_hhn_v0_2')
r,s=fx.base_request(),fx.base_snapshot()
t=['policy']; t.append(t); s['grants'][0]['targets']=t
calls=[]
def verify(record,at):
    calls.append('verify'); return 'VERIFIED'
result=m.resolve_policy_change(request=r,authenticate=lambda subject:'ESTABLISHED',
    snapshot_provider=lambda:s,current_epoch=lambda:0,verify_grant=verify)
print(json.dumps(dict(result=result,calls=calls)))
"""


class Harness(unittest.TestCase):
    def setUp(self):
        self.module = load(self)
        self.request, self.state = inputs()
        self.calls = []
        self.epoch_calls = 0

    def resolve(self, authentication='ESTABLISHED', provider=None, verifier=None,
                epoch=None, check_unchanged=True):
        def auth(subject):
            self.calls.append(('auth', subject))
            return authentication

        def snapshot():
            self.calls.append(('snapshot',))
            return self.state

        def verify(record, at):
            self.calls.append(('grant', record['id'], at))
            return 'VERIFIED'

        def current():
            self.epoch_calls += 1
            return self.state['state_epoch']

        before = deepcopy((self.request, self.state)) if check_unchanged else None
        result = self.module.resolve_policy_change(
            request=self.request, authenticate=auth,
            snapshot_provider=provider or snapshot,
            current_epoch=epoch or current, verify_grant=verifier or verify)
        if check_unchanged:
            self.assertEqual((self.request, self.state), before)
        return result

    def denied(self, reason, **kwargs):
        result = self.resolve(**kwargs)
        self.assertEqual(result, denial(reason))
        return result

    def reason(self, **kwargs):
        return self.resolve(**kwargs)['reason']


# ---------------------------------------------------------------------------
# #92 carried forward
# ---------------------------------------------------------------------------

class CarriedForwardV01(Harness):
    def test_HP01_HP02_positive_binding_and_order(self):
        result = self.resolve()
        self.assertEqual(result, authorized(self.request))
        self.assertEqual(self.calls, [('auth', 'alice'), ('snapshot',),
                                      ('grant', 'leaf', 10), ('grant', 'root', 10)])

    def test_H01_H02_caller_claims(self):
        for extra in ['authenticated', 'trusted_root', 'new_grant', 'self_authorized']:
            with self.subTest(extra=extra):
                self.request, self.state = inputs(); self.calls = []
                self.request[extra] = True
                self.denied('INVALID_AUTHORITY_INPUT')
                self.assertEqual(self.calls, [])
        self.request, self.state = inputs()
        self.state['grants'] = []
        self.denied('AUTHORITY_UNRESOLVED')

    def test_H03_protected_target(self):
        self.state['policy']['mutable_by_policy_change'] = False
        self.denied('AUTHORITY_SCOPE_VIOLATION')
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def test_A01_authentication_hard_stop(self):
        for outcome, reason in [('NOT_ESTABLISHED', 'AUTHENTICATION_NOT_ESTABLISHED'),
                                ('VERIFICATION_ERROR', 'AUTHORITY_VERIFICATION_ERROR'),
                                (True, 'AUTHORITY_VERIFICATION_ERROR')]:
            with self.subTest(outcome=outcome):
                self.calls = []; self.denied(reason, authentication=outcome)
                self.assertEqual(self.calls, [('auth', 'alice')])
                self.assertEqual(self.epoch_calls, 0)
        def fault(subject):
            raise RuntimeError('fault')
        forbidden = []
        def provider():
            forbidden.append('provider'); return self.state
        def verifier(*args):
            forbidden.append('verifier'); return 'VERIFIED'
        def current():
            forbidden.append('current_epoch'); return 0
        before = deepcopy((self.request, self.state))
        result = self.module.resolve_policy_change(
            request=self.request, authenticate=fault, snapshot_provider=provider,
            current_epoch=current, verify_grant=verifier)
        self.assertEqual(forbidden, [])
        self.assertEqual((self.request, self.state), before)
        self.assertEqual(result, denial('AUTHORITY_VERIFICATION_ERROR'))

    def test_A02_missing_state_and_exact_root(self):
        for case in ['leaf', 'parent', 'root', 'root_digest', 'root_revision', 'revocation']:
            with self.subTest(case=case):
                self.request, self.state = inputs()
                if case == 'leaf': self.state['grants'].pop(0)
                elif case == 'parent': self.state['grants'].pop(1)
                elif case == 'root': self.state['roots'] = {}
                elif case.startswith('root_'): self.state['roots']['root'][case[5:]] = 'other'
                else: self.state['grants'][0]['revoked'] = None
                self.denied('AUTHORITY_UNRESOLVED')

    def test_A03_delegation_attenuation(self):
        for case in ['subject', 'issuer', 'delegation', 'targets', 'start', 'end']:
            with self.subTest(case=case):
                self.request, self.state = inputs()
                leaf, root = self.state['grants']
                if case in ('subject', 'issuer'): leaf[case] = 'wrong'
                elif case == 'delegation': root['can_delegate'] = False
                elif case == 'targets': leaf['targets'].append('extra')
                elif case == 'start': leaf['not_before'] = -1
                else: leaf['expires_at'] = 101
                self.denied('AUTHORITY_SCOPE_VIOLATION')

    def test_A04_revocation_and_time(self):
        for revoked, at, reason in [(True, 10, 'AUTHORITY_REVOKED'),
                                    (False, -1, 'AUTHORITY_NOT_CURRENT'),
                                    (False, 100, 'AUTHORITY_NOT_CURRENT')]:
            with self.subTest(at=at, revoked=revoked):
                self.request, self.state = inputs()
                self.state['grants'][0]['revoked'] = revoked; self.state['at'] = at
                self.denied(reason)
        self.request, self.state = inputs(); self.state['at'] = 0
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_root_and_intermediate_local_validity(self):
        for location in ['root', 'middle']:
            for field, value, reason in [('revoked', True, 'AUTHORITY_REVOKED'),
                                         ('revoked', None, 'AUTHORITY_UNRESOLVED'),
                                         ('not_before', 11, 'AUTHORITY_NOT_CURRENT'),
                                         ('expires_at', 10, 'AUTHORITY_NOT_CURRENT')]:
                with self.subTest(location=location, field=field, value=value):
                    self.request, self.state = inputs(); self.calls = []
                    leaf, root = self.state['grants']
                    middle = grant('middle', 'middle-subject', 'root-subject', 'root')
                    leaf.update(issuer='middle-subject', parent_id='middle')
                    self.state['grants'].insert(1, middle); self.state['max_grants'] = 3
                    self.assertEqual(self.resolve(), authorized(self.request))
                    self.assertEqual([c[1] for c in self.calls if c[0] == 'grant'],
                                     ['leaf', 'middle', 'root'])
                    self.calls = []
                    selected = root if location == 'root' else middle
                    selected[field] = value
                    self.denied(reason)
                    self.assertLessEqual(sum(c[0] == 'grant' for c in self.calls), 3)
        self.request, self.state = inputs()
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_matching_scopes_without_requested_authority(self):
        for field, value in [('operations', []), ('targets', ['other-policy'])]:
            with self.subTest(field=field):
                self.request, self.state = inputs()
                for record in self.state['grants']: record[field] = deepcopy(value)
                self.denied('AUTHORITY_SCOPE_VIOLATION')
        self.request, self.state = inputs()
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_A05_policy_and_request_binding(self):
        for field in ['policy_id', 'expected_revision', 'expected_digest']:
            with self.subTest(field=field):
                self.request, self.state = inputs(); self.request[field] = 'other'
                self.denied('POLICY_STATE_MISMATCH')
        self.request, self.state = inputs()
        previous = self.resolve(); self.request['proposed_digest'] = 'new-content'
        current = self.resolve()
        self.assertNotEqual(previous['request_binding'], current['request_binding'])
        self.assertEqual(previous['request_binding'][5], 'pd2')

    def test_N01_N02_cycles(self):
        for count, prefix in [(1, False), (2, False), (2, True)]:
            with self.subTest(count=count, prefix=prefix):
                self.request, self.state = inputs(); self.calls = []
                nodes = [grant(str(i), 'alice', 'alice', str((i + 1) % count)) for i in range(count)]
                if prefix: nodes.insert(0, grant('prefix', 'alice', 'alice', '0'))
                self.state.update(grants=nodes, roots={}, max_grants=len(nodes))
                self.request['leaf_grant_id'] = nodes[0]['id']
                observed = run_isolated(CYCLE_WORKER, [self.request, self.state])
                self.assertEqual(observed['result'], denial('AUTHORITY_CYCLE_DETECTED'))
                self.assertEqual(observed['request'], self.request)
                self.assertEqual(observed['state'], self.state)
                seen = observed['seen']
                self.assertEqual(len(seen), len(nodes)); self.assertEqual(len(seen), len(set(seen)))

    def test_N03_N04_budget_boundary(self):
        self.state['max_grants'] = 1
        self.denied('AUTHORITY_LIMIT_EXCEEDED')
        self.assertEqual([c[1] for c in self.calls if c[0] == 'grant'], ['leaf'])
        self.state['max_grants'] = 2
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_E01_provider_and_verifier_faults(self):
        def fault(*args): raise RuntimeError('private fault')
        self.denied('AUTHORITY_VERIFICATION_ERROR', provider=fault)
        self.denied('AUTHORITY_UNRESOLVED', provider=lambda: None)
        self.denied('AUTHORITY_VERIFICATION_ERROR', verifier=fault)
        for outcome in [True, 1, None, 'VERIFICATION_ERROR']:
            with self.subTest(outcome=outcome):
                self.denied('AUTHORITY_VERIFICATION_ERROR', verifier=lambda *a: outcome)
        self.denied('AUTHORITY_UNRESOLVED', verifier=lambda *a: 'UNVERIFIED')

    def test_R01_reacquires_state(self):
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')
        self.state['grants'][0]['revoked'] = True
        self.denied('AUTHORITY_REVOKED')
        self.assertEqual(sum(c[0] == 'snapshot' for c in self.calls), 2)
        self.request, self.state = inputs(); self.state['policy']['revision'] = 'p3'
        self.denied('POLICY_STATE_MISMATCH')

    def test_V01_duplicate_and_malformed(self):
        self.state['grants'].append(deepcopy(self.state['grants'][0]))
        self.denied('INVALID_AUTHORITY_INPUT')
        for budget in [0, -1, True, '2']:
            with self.subTest(budget=budget):
                self.request, self.state = inputs(); self.state['max_grants'] = budget
                self.denied('INVALID_AUTHORITY_INPUT')

    def test_missing_malformed_and_extra_state_table(self):
        cases = [
            (('snapshot_id',), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('policy', 'revision'), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('roots', 'root', 'digest'), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('grants', 1, 'revoked'), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('at',), 'set', True, 'INVALID_AUTHORITY_INPUT'),
            (('policy', 'mutable_by_policy_change'), 'set', 1, 'INVALID_AUTHORITY_INPUT'),
            (('roots', 'root'), 'set', [], 'INVALID_AUTHORITY_INPUT'),
            (('roots', 'root', 'extra'), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('policy', 'extra'), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('extra',), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'extra'), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'not_before'), 'set', False, 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'operations'), 'set', ['POLICY_CHANGE', 'extra'], 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'operations'), 'set', ['POLICY_CHANGE'] * 2, 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'targets'), 'set', ['*'], 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'targets'), 'set', ['policy'] * 2, 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'targets'), 'set', [''], 'INVALID_AUTHORITY_INPUT'),
            (('grants',), 'set', {}, 'INVALID_AUTHORITY_INPUT'),
        ]
        for path, action, value, reason in cases:
            with self.subTest(path=path, action=action, value=value):
                self.request, self.state = inputs(); self.calls = []
                target = self.state
                for key in path[:-1]: target = target[key]
                if action == 'delete': del target[path[-1]]
                else: target[path[-1]] = value
                self.denied(reason)
                self.assertFalse(any(c[0] == 'grant' for c in self.calls))
        self.request, self.state = inputs(); self.calls = []
        del self.state['policy']['revision']
        self.state['grants'][1]['operations'] = ['extra']
        self.denied('INVALID_AUTHORITY_INPUT')
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))
        self.request, self.state = inputs()
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_request_and_api_validation_table(self):
        for field, action, value in [('expected_digest', 'delete', None),
                                     ('requester_id', 'set', ''), ('proposed_digest', 'set', 3)]:
            with self.subTest(field=field):
                self.request, self.state = inputs(); self.calls = []
                if action == 'delete': del self.request[field]
                else: self.request[field] = value
                self.denied('INVALID_AUTHORITY_INPUT'); self.assertEqual(self.calls, [])
        self.request, self.state = inputs(); self.request['operation'] = 'extra'
        self.denied('AUTHORITY_SCOPE_VIOLATION')
        class DictSubclass(dict): pass
        for argument, value in [('request', []), ('request', DictSubclass(inputs()[0])),
                                ('authenticate', None), ('snapshot_provider', 1),
                                ('verify_grant', False), ('current_epoch', 'x')]:
            with self.subTest(argument=argument):
                calls = []
                def auth(subject): calls.append('auth'); return 'ESTABLISHED'
                def provider(): calls.append('provider'); return self.state
                def verifier(*args): calls.append('verify'); return 'VERIFIED'
                def current(): calls.append('epoch'); return 0
                kwargs = dict(request=inputs()[0], authenticate=auth, snapshot_provider=provider,
                              current_epoch=current, verify_grant=verifier)
                kwargs[argument] = value
                with self.assertRaises(TypeError): self.module.resolve_policy_change(**kwargs)
                self.assertEqual(calls, [])

    def test_seam_argument_isolation(self):
        def mutate(record, at):
            record['revoked'] = True; record['targets'].clear()
            return 'VERIFIED'
        self.assertEqual(self.resolve(verifier=mutate), authorized(self.request))


# ---------------------------------------------------------------------------
# P§8 acceptance cases allocated to the inspection entry (interface §9)
# ---------------------------------------------------------------------------

class SourceHarness(Harness):
    """Inspection calls against a ReferenceSource."""

    def resolve_source(self, src, verifier=None, request=None):
        self.verify_calls = []
        def verify(record, at):
            self.verify_calls.append(record['id'])
            return 'VERIFIED'
        return self.module.resolve_policy_change(
            request=request or base_request(), authenticate=lambda s: 'ESTABLISHED',
            snapshot_provider=src.snapshot_provider, current_epoch=src.current_epoch,
            verify_grant=verifier or verify)


class MidChangeAndABA(SourceHarness):
    def test_P8_C01_unrelated_mutation_during_verify(self):
        src = ReferenceSource(max_grants=3)
        def verify(record, at):
            if record['id'] == 'leaf':
                src.touch('other')
            return 'VERIFIED'
        self.assertEqual(self.resolve_source(src, verify), denial('AUTHORITY_STATE_CHANGED'))
        self.assertEqual((src.writes, src.mutations, src.epoch), (0, 1, 1))

    def test_P8_C02_visited_leaf_revoked_during_verify(self):
        src = ReferenceSource(max_grants=3)
        def verify(record, at):
            if record['id'] == 'leaf':
                src.revoke('leaf')
            return 'VERIFIED'
        self.assertEqual(self.resolve_source(src, verify), denial('AUTHORITY_STATE_CHANGED'))

    def test_P8_C05_denial_not_rechecked(self):
        src = ReferenceSource(max_grants=3)
        src.revoke('leaf')
        def verify(record, at):
            src.touch('other')
            return 'VERIFIED'
        self.assertEqual(self.resolve_source(src, verify), denial('AUTHORITY_REVOKED'))
        self.assertEqual([c for c in src.calls if c[0] == 'current_epoch'], [])

    def test_source_positive_control_not_a_P8_id(self):
        src = ReferenceSource(max_grants=3)
        self.assertEqual(self.resolve_source(src), authorized(
            base_request(), snapshot_id='s-0', state_epoch=0, at=10, valid_until=100))
        self.assertEqual([c[0] for c in src.calls],
                         ['snapshot_provider', 'current_epoch'])

    def test_P8_A03_current_epoch_regression_and_faults(self):
        self.state['state_epoch'] = 5
        def fault():
            raise RuntimeError('epoch fault')
        for name, seam in [('less', lambda: 4), ('bool', lambda: True),
                           ('str', lambda: '5'), ('float', lambda: 5.0),
                           ('exception', fault)]:
            with self.subTest(case=name):
                self.denied('AUTHORITY_VERIFICATION_ERROR', epoch=seam)
        self.assertEqual(self.resolve(epoch=lambda: 6), denial('AUTHORITY_STATE_CHANGED'))
        self.assertEqual(self.resolve(epoch=lambda: 5)['authorization_status'], 'AUTHORIZED')

    def test_P8_A04_state_epoch_classification(self):
        del self.state['state_epoch']
        self.denied('AUTHORITY_UNRESOLVED', epoch=lambda: 0)
        for value in [True, -1, '3', 3.0]:
            with self.subTest(value=value):
                self.request, self.state = inputs(); self.state['state_epoch'] = value
                self.denied('INVALID_AUTHORITY_INPUT', epoch=lambda: 0)
        self.request, self.state = inputs(); self.state['state_epoch'] = 2 ** 64
        self.denied('SNAPSHOT_LIMIT_EXCEEDED', epoch=lambda: 2 ** 64)
        self.request, self.state = inputs(); self.state['state_epoch'] = 2 ** 64 - 1
        self.assertEqual(self.resolve(epoch=lambda: 2 ** 64 - 1)['authorization_status'],
                         'AUTHORIZED')


class EntryArguments(Harness):
    def test_P8_U04_no_prior_result_parameters(self):
        for keyword in ['prior_result', 'state_epoch', 'snapshot_at', 'valid_until']:
            with self.subTest(keyword=keyword):
                calls = []
                kwargs = dict(request=base_request(),
                              authenticate=lambda s: calls.append('auth') or 'ESTABLISHED',
                              snapshot_provider=lambda: calls.append('snapshot') or base_snapshot(),
                              current_epoch=lambda: calls.append('epoch') or 0,
                              verify_grant=lambda r, a: calls.append('verify') or 'VERIFIED')
                kwargs[keyword] = 0
                with self.assertRaises(TypeError):
                    self.module.resolve_policy_change(**kwargs)
                self.assertEqual(calls, [])


class NoOpRequest(Harness):
    def test_P8_V01_both_unchanged(self):
        self.request.update(proposed_revision='p1', proposed_digest='pd1')
        self.denied('INVALID_AUTHORITY_INPUT')
        self.assertEqual((self.calls, self.epoch_calls), ([], 0))

    def test_P8_V02_one_unchanged_positive_control(self):
        for revision, digest in [('p1', 'pd2'), ('p2', 'pd1')]:
            with self.subTest(revision=revision, digest=digest):
                self.request, self.state = inputs()
                self.request.update(proposed_revision=revision, proposed_digest=digest)
                self.assertEqual(self.resolve(), authorized(self.request))

    def test_P8_V03_precedes_authentication(self):
        self.request.update(proposed_revision='p1', proposed_digest='pd1')
        for outcome in ['NOT_ESTABLISHED', 'VERIFICATION_ERROR']:
            with self.subTest(outcome=outcome):
                self.calls = []; self.epoch_calls = 0
                self.denied('INVALID_AUTHORITY_INPUT', authentication=outcome)
                self.assertEqual((self.calls, self.epoch_calls), ([], 0))


def filler(index, **overrides):
    return grant('f%d' % index, 'filler', 'external', None, **overrides)


class Budgets(Harness):
    def assert_limit(self, code, **kwargs):
        self.assertEqual(self.resolve(**kwargs), denial(code))

    def assert_not_limit(self, code, **kwargs):
        self.assertNotEqual(self.resolve(**kwargs)['reason'], code)

    def test_P8_B01_request_key_cap_no_iteration(self):
        key = OpaqueKey()
        for i in range(8):
            self.request['extra%d' % i] = 'x'
        self.request[key] = 'x'
        self.assertEqual(len(self.request), 17)
        RECORDER.clear()
        result = self.resolve(check_unchanged=False)
        self.assertEqual(result, denial('REQUEST_LIMIT_EXCEEDED'))
        self.assertEqual((RECORDER, self.calls, self.epoch_calls), ([], [], 0))
        self.request, self.state = inputs(); self.request['extra'] = 'x'
        self.denied('INVALID_AUTHORITY_INPUT')

    def test_P8_B02_request_string_cap(self):
        self.request['proposed_digest'] = 'x' * 256
        self.assertEqual(self.resolve(), authorized(self.request))
        self.request['proposed_digest'] = 'x' * 257; self.calls = []
        self.assert_limit('REQUEST_LIMIT_EXCEEDED'); self.assertEqual(self.calls, [])
        self.request, self.state = inputs(); self.request['k' * 256] = 'x'
        self.denied('INVALID_AUTHORITY_INPUT')
        self.request, self.state = inputs(); self.request['k' * 257] = 'x'
        self.assert_limit('REQUEST_LIMIT_EXCEEDED')

    def test_P8_B03_grant_count_preempts_malformed_and_missing(self):
        for position in ['before', 'after']:
            with self.subTest(position=position):
                self.request, self.state = inputs(); self.calls = []
                self.state['grants'] += [filler(i) for i in range(1023)]
                self.assertEqual(len(self.state['grants']), 1025)
                bad = 0 if position == 'before' else 1024
                self.state['grants'][bad]['revoked'] = 'x'
                del self.state['grants'][5]['digest']
                self.assert_limit('SNAPSHOT_LIMIT_EXCEEDED')
                self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def test_P8_B04_visit_cap(self):
        self.assertEqual(fx.reference_figures(), (55, 65536, 65537))
        self.state = visit_boundary_snapshot(28)
        self.assertEqual(count_visits(self.state), 65536)
        self.assert_not_limit('SNAPSHOT_LIMIT_EXCEEDED')
        self.state = visit_boundary_snapshot(29); self.calls = []
        self.assertEqual(count_visits(self.state), 65537)
        self.assert_limit('SNAPSHOT_LIMIT_EXCEEDED')
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def test_P8_B05_every_cap_at_limit_and_plus_one(self):
        LIMIT_R, LIMIT_S = 'REQUEST_LIMIT_EXCEEDED', 'SNAPSHOT_LIMIT_EXCEEDED'

        def request_keys(n):
            r = base_request()
            for i in range(n - 8): r['extra%d' % i] = 'x'
            return r

        def request_value(n):
            return base_request(proposed_digest='x' * n)

        def request_key(n):
            r = base_request(); r['k' * n] = 'x'; return r

        def grants(n):
            s = base_snapshot(); s['grants'] += [filler(i) for i in range(n - 2)]; return s

        def roots(n):
            s = base_snapshot()
            for i in range(n - 1): s['roots']['x%d' % i] = dict(revision='r', digest='d')
            return s

        def record_keys(n):
            s = base_snapshot()
            for i in range(n - 12): s['grants'][0]['x%d' % i] = 'x'
            return s

        def targets(n):
            s = base_snapshot()
            s['grants'][1]['targets'] = ['policy'] + ['t%d' % i for i in range(n - 1)]
            return s

        def operations(n):
            s = base_snapshot(); s['grants'][1]['operations'] = ['POLICY_CHANGE'] * n; return s

        def snapshot_value(n):
            return base_snapshot(snapshot_id='x' * n)

        def snapshot_key(n):
            s = base_snapshot(); s['grants'][0]['k' * n] = 'x'; return s

        rows = [
            ('REQUEST_MAX_KEYS', LIMIT_R, 'request', request_keys, 16),
            ('REQUEST_MAX_STRING_CHARS value', LIMIT_R, 'request', request_value, 256),
            ('REQUEST_MAX_STRING_CHARS key', LIMIT_R, 'request', request_key, 256),
            ('SNAPSHOT_MAX_GRANTS', LIMIT_S, 'snapshot', grants, 1024),
            ('SNAPSHOT_MAX_ROOTS', LIMIT_S, 'snapshot', roots, 64),
            ('SNAPSHOT_MAX_RECORD_KEYS', LIMIT_S, 'snapshot', record_keys, 32),
            ('SNAPSHOT_MAX_SCOPE_ITEMS targets', LIMIT_S, 'snapshot', targets, 64),
            ('SNAPSHOT_MAX_SCOPE_ITEMS operations', LIMIT_S, 'snapshot', operations, 64),
            ('SNAPSHOT_MAX_STRING_CHARS value', LIMIT_S, 'snapshot', snapshot_value, 256),
            ('SNAPSHOT_MAX_STRING_CHARS key', LIMIT_S, 'snapshot', snapshot_key, 256),
        ]
        for name, code, side, build, cap in rows:
            for n, expect_limit in [(cap, False), (cap + 1, True)]:
                with self.subTest(row=name, n=n):
                    if side == 'request':
                        self.request, self.state = build(n), base_snapshot()
                    else:
                        self.request, self.state = base_request(), build(n)
                    if expect_limit:
                        self.assert_limit(code)
                    else:
                        self.assert_not_limit(code)
        for field in ['at', 'max_grants', 'state_epoch', 'not_before', 'expires_at']:
            for value, expect_limit in [(2 ** 64 - 1, False), (2 ** 64, True)]:
                with self.subTest(row='SNAPSHOT_MAX_INT_BITS', field=field, value=value):
                    self.request, self.state = inputs()
                    target = self.state['grants'][0] if field in ('not_before', 'expires_at') else self.state
                    target[field] = value
                    epoch = (lambda v=value: v) if field == 'state_epoch' else None
                    if expect_limit:
                        self.assert_limit(LIMIT_S, epoch=epoch)
                    else:
                        self.assert_not_limit(LIMIT_S, epoch=epoch)
        self.request, self.state = base_request(), visit_boundary_snapshot(28)
        self.assert_not_limit(LIMIT_S)
        self.request, self.state = base_request(), visit_boundary_snapshot(29)
        self.assert_limit(LIMIT_S)

    def test_P8_B06_request_limit_before_snapshot(self):
        for i in range(9): self.request['extra%d' % i] = 'x'
        self.state['grants'] += [filler(i) for i in range(1023)]
        self.assert_limit('REQUEST_LIMIT_EXCEEDED')
        self.assertEqual((self.calls, self.epoch_calls), ([], 0))

    def test_P8_B07_traversal_budget_unchanged(self):
        self.state['max_grants'] = 1
        self.assert_limit('AUTHORITY_LIMIT_EXCEEDED')
        self.state['max_grants'] = 2
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_P8_B08_snapshot_limit_preempts_traversal_limit(self):
        self.state['grants'] += [filler(i) for i in range(1023)]
        self.state['max_grants'] = 1
        self.assert_limit('SNAPSHOT_LIMIT_EXCEEDED')
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def test_P8_B09_unreachable_oversize(self):
        self.state['grants'] += [filler(i) for i in range(1023)]
        self.state[OpaqueKey()] = 'x'
        RECORDER.clear()
        self.assertEqual(self.resolve(check_unchanged=False), denial('INVALID_AUTHORITY_INPUT'))
        self.assertEqual(RECORDER, [])
        self.request, self.state = inputs()
        self.state['grants'] += [filler(i) for i in range(1023)]
        self.assert_limit('SNAPSHOT_LIMIT_EXCEEDED')

    def test_P8_B10_sibling_reachability(self):
        for order in ['A_first', 'B_first']:
            for b_targets, expected in [(64, 'INVALID_AUTHORITY_INPUT'),
                                        (65, 'SNAPSHOT_LIMIT_EXCEEDED')]:
                with self.subTest(order=order, b_targets=b_targets):
                    self.request, self.state = inputs()
                    a = filler(0, targets=['t%d' % i for i in range(65)])
                    a[OpaqueKey()] = 'x'
                    b = filler(1, targets=['t%d' % i for i in range(b_targets)])
                    pair = [a, b] if order == 'A_first' else [b, a]
                    self.state['grants'] += pair
                    RECORDER.clear()
                    self.assertEqual(self.resolve(check_unchanged=False), denial(expected))
                    self.assertEqual(RECORDER, [])


def set_path(container, path, value):
    for key in path[:-1]:
        container = container[key]
    container[path[-1]] = value


SNAPSHOT_VALUE_POSITIONS = [
    (('snapshot_id',), RecStr), (('policy',), RecDict),
    (('policy', 'policy_id'), RecStr), (('policy', 'revision'), RecStr),
    (('policy', 'digest'), RecStr), (('grants',), RecList), (('grants', 0), RecDict),
] + [(('grants', 0, f), RecStr) for f in ('id', 'revision', 'digest', 'subject',
                                         'issuer', 'parent_id')] + [
    (('grants', 0, 'operations'), RecList), (('grants', 0, 'operations', 0), RecStr),
    (('grants', 0, 'targets'), RecList), (('grants', 0, 'targets', 0), RecStr),
    (('grants', 0, 'not_before'), RecInt), (('grants', 0, 'expires_at'), RecInt),
    (('roots',), RecDict), (('roots', 'root'), RecDict),
    (('roots', 'root', 'revision'), RecStr), (('roots', 'root', 'digest'), RecStr),
    (('at',), RecInt), (('max_grants',), RecInt), (('state_epoch',), RecInt),
]

SNAPSHOT_KEY_POSITIONS = [(), ('policy',), ('grants', 0), ('roots',), ('roots', 'root')]


class SafeTraversal(Harness):
    def call(self, **kwargs):
        RECORDER.clear()
        result = self.resolve(check_unchanged=False, **kwargs)
        return result, list(RECORDER)

    def test_P8_T01_subclass_at_every_position(self):
        for path, cls in SNAPSHOT_VALUE_POSITIONS:
            with self.subTest(position='value', path=path):
                self.request, self.state = inputs(); self.calls = []
                target = self.state
                for key in path[:-1]: target = target[key]
                target[path[-1]] = cls(target[path[-1]])
                result, recorded = self.call()
                self.assertEqual(result, denial('INVALID_AUTHORITY_INPUT'))
                self.assertEqual(recorded, [])
                self.assertFalse(any(c[0] == 'grant' for c in self.calls))
        for path in SNAPSHOT_KEY_POSITIONS:
            with self.subTest(position='key', path=path):
                self.request, self.state = inputs()
                parent = self.state
                for key in path: parent = parent[key]
                first = next(iter(parent))
                rebuilt = replace_key(parent, first, RecStr(first))
                if path:
                    set_path(self.state, path, rebuilt)
                else:
                    self.state = rebuilt
                result, recorded = self.call()
                self.assertEqual(result, denial('INVALID_AUTHORITY_INPUT'))
                self.assertEqual(recorded, [])
        self.request, self.state = inputs()
        self.state = RecDict(self.state)
        result, recorded = self.call()
        self.assertEqual((result, recorded), (denial('INVALID_AUTHORITY_INPUT'), []))
        for field in FIELDS:
            with self.subTest(position='request value', field=field):
                self.request, self.state = inputs(); self.calls = []
                self.request[field] = RecStr(self.request[field])
                result, recorded = self.call()
                self.assertEqual((result, recorded, self.calls),
                                 (denial('INVALID_AUTHORITY_INPUT'), [], []))
            with self.subTest(position='request key', field=field):
                self.request, self.state = inputs(); self.calls = []
                self.request = replace_key(self.request, field, RecStr(field))
                result, recorded = self.call()
                self.assertEqual((result, recorded, self.calls),
                                 (denial('INVALID_AUTHORITY_INPUT'), [], []))

    def test_P8_T02_huge_list_subclass(self):
        self.state['grants'] = RecList([self.state['grants'][0]] * 10 ** 6)
        result, recorded = self.call()
        self.assertEqual((result, recorded), (denial('INVALID_AUTHORITY_INPUT'), []))

    def test_P8_T03_non_str_key(self):
        self.state['grants'][0][OpaqueKey()] = 'x'
        result, recorded = self.call()
        self.assertEqual((result, recorded), (denial('INVALID_AUTHORITY_INPUT'), []))
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def collision_rows(self):
        return [
            ('request', None, 'requester_id'),
            ('snapshot', (), 'snapshot_id'),
            ('policy', ('policy',), 'policy_id'),
            ('grant', ('grants', 0), 'id'),
            ('roots', ('roots',), 'root'),
            ('anchor', ('roots', 'root'), 'revision'),
        ]

    def build_collision(self, row, extra_key=None):
        name, path, field = row
        self.request, self.state = inputs(); self.calls = []
        collider = Collider(field)
        if name == 'request':
            self.request = replace_key(self.request, field, collider)
            if extra_key: self.request[extra_key] = 'x'
            return self.request, field
        parent = self.state
        for key in path: parent = parent[key]
        rebuilt = replace_key(parent, field, collider)
        if extra_key: rebuilt[extra_key] = 'x'
        if path:
            set_path(self.state, path, rebuilt)
        else:
            self.state = rebuilt
        return rebuilt, field

    def test_P8_T04_hash_collision_whole_dict_gate(self):
        for row in self.collision_rows():
            with self.subTest(row=row[0]):
                target, field = self.build_collision(row)
                RECORDER.clear()
                self.assertFalse(field in target)
                self.assertGreaterEqual(len(RECORDER), 1,
                                        'fixture defect: control lookup not detected')
                result, recorded = self.call()
                self.assertEqual(result, denial('INVALID_AUTHORITY_INPUT'))
                self.assertEqual(recorded, [])
                if row[0] == 'request':
                    self.assertEqual((self.calls, self.epoch_calls), ([], 0))
                else:
                    self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def test_P8_T05_collision_plus_overlong_key(self):
        for row, code in [(self.collision_rows()[3], 'SNAPSHOT_LIMIT_EXCEEDED'),
                          (self.collision_rows()[0], 'REQUEST_LIMIT_EXCEEDED')]:
            with self.subTest(row=row[0]):
                self.build_collision(row, extra_key='k' * 257)
                result, recorded = self.call()
                self.assertEqual((result, recorded), (denial(code), []))


class SharedReferences(Harness):
    def test_P8_S01_shared_targets_same_result(self):
        unaliased = self.resolve()
        self.request, self.state = inputs()
        shared = ['policy']
        for record in self.state['grants']: record['targets'] = shared
        aliased = self.resolve()
        self.assertEqual(aliased, unaliased)
        # Strengthened (test revision 2026-10-09): equality alone passes under
        # any constant result; both must be the positive control.
        self.assertEqual(unaliased, authorized(self.request))
        self.assertEqual(aliased, authorized(self.request))

    def test_P8_S02_verify_mutation_does_not_leak_through_alias(self):
        shared = ['policy']
        for record in self.state['grants']: record['targets'] = shared
        seen = {}
        def verify(record, at):
            seen[record['id']] = list(record['targets'])
            record['targets'].clear()
            return 'VERIFIED'
        self.assertEqual(self.resolve(verifier=verify), authorized(self.request))
        self.assertEqual(seen, {'leaf': ['policy'], 'root': ['policy']})
        self.assertEqual(shared, ['policy'])
        self.assertIs(self.state['grants'][0]['targets'], shared)

    def test_P8_S03_expansion_charged_per_reference(self):
        shared = ['t%d' % i for i in range(64)]
        for count, expect_limit in [(808, False), (809, True)]:
            with self.subTest(count=count):
                self.request = base_request()
                self.state = base_snapshot(grants=[
                    grant('g%d' % i, 's', 'i', None, targets=shared) for i in range(count)])
                self.assertEqual(count_visits(self.state), 19 + 81 * count)
                reason = self.resolve()['reason']
                if expect_limit:
                    self.assertEqual(reason, 'SNAPSHOT_LIMIT_EXCEEDED')
                else:
                    self.assertNotEqual(reason, 'SNAPSHOT_LIMIT_EXCEEDED')

    def test_P8_S04_shared_anchor_legal_and_charged_twice(self):
        anchor = dict(revision='r1', digest='d-root')
        self.state['roots'] = {'root': anchor, 'root2': anchor}
        self.assertEqual(self.resolve(), authorized(self.request))
        for last, expect_limit in [(24, False), (25, True)]:
            with self.subTest(last_targets=last):
                self.request = base_request()
                self.state = visit_boundary_snapshot(last, roots={'root': anchor, 'root2': anchor})
                self.assertEqual(count_visits(self.state), 65512 + last)
                reason = self.resolve()['reason']
                if expect_limit:
                    self.assertEqual(reason, 'SNAPSHOT_LIMIT_EXCEEDED')
                else:
                    self.assertNotEqual(reason, 'SNAPSHOT_LIMIT_EXCEEDED')

    def test_P8_S05_self_containing_list(self):
        observed = run_isolated(SELF_LIST_WORKER, None)
        self.assertEqual(observed['result'], denial('INVALID_AUTHORITY_INPUT'))
        self.assertEqual(observed['calls'], [])


# ---------------------------------------------------------------------------
# Supplementary cases, outside P§8 (test revision 2026-10-09).
# E4: errata E4 rows 1-3 (scalar size scope in snapshot preflight).
# ---------------------------------------------------------------------------

class SupplementaryE4ScalarScope(Harness):
    def check(self, mutate, at_limit, over_limit, opaque=False):
        for value, expected in [(at_limit, 'INVALID_AUTHORITY_INPUT'),
                                (over_limit, 'SNAPSHOT_LIMIT_EXCEEDED')]:
            with self.subTest(value=repr(value)[:24], expected=expected):
                self.request, self.state = inputs(); self.calls = []
                mutate(self.state['grants'][0], value)
                RECORDER.clear()
                result = self.resolve(check_unchanged=not opaque)
                self.assertEqual(result, denial(expected))
                self.assertFalse(any(c[0] == 'grant' for c in self.calls))
                self.assertEqual(self.epoch_calls, 0)
                if opaque:
                    self.assertEqual(RECORDER, [])

    def test_SUPP_E4_1_extra_field_overlong_str(self):
        self.check(lambda g, v: g.__setitem__('extra', v), 'x' * 256, 'x' * 257)

    def test_SUPP_E4_2_extra_field_65_bit_int(self):
        self.check(lambda g, v: g.__setitem__('extra', v), 2 ** 64 - 1, 2 ** 64)

    def test_SUPP_E4_3_key_gate_failed_dict_overlong_scalar(self):
        self.check(lambda g, v: g.__setitem__(OpaqueKey(), v), 'x' * 256, 'x' * 257,
                   opaque=True)


if __name__ == '__main__':
    unittest.main()
