"""RED acceptance tests for the use-time entry `commit_policy_change`.

Frozen interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md.
Acceptance IDs: PHAGE_AUTHORITY_RESOLVER_USE_TIME_CONSISTENCY_CONTRACT_v0_1.md
§8, allocated per interface §9. An absent module is surface RED only.

`ReferenceSourceModel` tests exercise only the fixture source (O01, O05,
visit figures). They need no product module and are expected to pass now;
they validate the test fixture, not any implementation.
"""
import importlib
import unittest

import fixture_phage_authority_reference_source_v0_1 as fx
from fixture_phage_authority_reference_source_v0_1 import (
    FIELDS, Collider, RECORDER, ReferenceSource, base_request, grant,
    snapshot_containers)

MODULE = 'phage_authority_protected_use_v0_1'


def load(testcase):
    try:
        return importlib.import_module(MODULE)
    except ModuleNotFoundError as error:
        if error.name != MODULE:
            raise
        testcase.fail('SURFACE_RED: %s absent; not behavioral evidence' % MODULE)


def not_committed(reason):
    return dict(commit_status='NOT_COMMITTED', reason=reason, effect_path='BLOCKED',
                request_binding=None, committed_epoch=None)


def commit_error():
    return dict(commit_status='COMMIT_ERROR', reason='AUTHORITY_VERIFICATION_ERROR',
                effect_path='BLOCKED', request_binding=None, committed_epoch=None)


def unknown():
    return dict(commit_status='COMMIT_OUTCOME_UNKNOWN', reason='COMMIT_OUTCOME_UNKNOWN',
                effect_path='NOT_DETERMINED', request_binding=None, committed_epoch=None)


def committed(request, epoch):
    return dict(commit_status='COMMITTED', reason='POLICY_CHANGE_COMMITTED',
                effect_path='EFFECT_APPLIED',
                request_binding=tuple(request[k] for k in FIELDS), committed_epoch=epoch)


def binding(request):
    return tuple(request[k] for k in FIELDS)


class ReferenceSourceModel(unittest.TestCase):
    """Fixture validation; no product module required."""

    def test_visit_reference_figures(self):
        self.assertEqual(fx.reference_figures(), (55, 65536, 65537))

    def test_P8_O01_one_counter_for_three_seams(self):
        src = ReferenceSource()
        e0 = src.current_epoch()
        self.assertEqual(src.snapshot_provider()['state_epoch'], e0)
        src.revoke('leaf')
        self.assertEqual(src.current_epoch(), e0 + 1)
        snap = src.snapshot_provider()
        self.assertEqual(snap['state_epoch'], e0 + 1)
        self.assertTrue(snap['grants'][0]['revoked'])
        b = binding(base_request())
        self.assertEqual(src.commit_if_epoch(expected_epoch=e0, snapshot_at=10,
                                             valid_until=100, binding=b),
                         dict(outcome='EPOCH_MISMATCH', committed_epoch=None))
        self.assertEqual(src.commit_if_epoch(expected_epoch=e0 + 1, snapshot_at=10,
                                             valid_until=100, binding=b),
                         dict(outcome='COMMITTED', committed_epoch=e0 + 2))
        self.assertEqual(src.current_epoch(), e0 + 2)

    def test_P8_O05_detached_snapshot(self):
        src = ReferenceSource()
        snap = src.snapshot_provider()
        self.assertEqual(snapshot_containers(snap) & src.live_containers(), set())
        before = repr(snap)
        src.revoke('leaf'); src.set_policy('p9', 'pd9'); src.touch('other')
        self.assertEqual(repr(snap), before)

    def test_reference_source_rejections_write_nothing(self):
        b = binding(base_request())
        for clock, epoch_shift, outcome in [(9, 0, 'TIME_REGRESSION'),
                                            (10, 1, 'EPOCH_MISMATCH'),
                                            (100, 0, 'NOT_CURRENT')]:
            with self.subTest(outcome=outcome):
                src = ReferenceSource(clock=clock)
                if epoch_shift: src.touch()
                before = src.dump()
                result = src.commit_if_epoch(expected_epoch=0, snapshot_at=10,
                                             valid_until=100, binding=b)
                self.assertEqual(result['outcome'], outcome)
                self.assertEqual((src.dump(), src.writes), (before, 0))


class Harness(unittest.TestCase):
    def setUp(self):
        self.module = load(self)
        self.request = base_request()
        self.auth_calls = []
        self.verify_calls = []

    def run_entry(self, src, request=None, commit=None, verifier=None,
                  authentication='ESTABLISHED', provider=None, epoch=None):
        def auth(subject):
            self.auth_calls.append(subject)
            return authentication

        def verify(record, at):
            self.verify_calls.append(record['id'])
            return 'VERIFIED'

        return self.module.commit_policy_change(
            request=request or self.request, authenticate=auth,
            snapshot_provider=provider or src.snapshot_provider,
            current_epoch=epoch or src.current_epoch,
            verify_grant=verifier or verify,
            commit_if_epoch=commit or src.commit_if_epoch)

    def commit_calls(self, src):
        return [c for c in src.calls if c[0] == 'commit_if_epoch']


class MidChangeAndABA(Harness):
    def test_P8_C03_revoked_before_commit(self):
        src = ReferenceSource()
        src.pre_commit_hooks.append(lambda s: s.revoke('leaf'))
        self.assertEqual(self.run_entry(src), not_committed('AUTHORITY_STATE_CHANGED'))
        self.assertEqual(src.dump()['policy']['revision'], 'p1')
        self.assertEqual(src.writes, 0)

    def test_P8_C04_positive_control(self):
        src = ReferenceSource()
        self.assertEqual(self.run_entry(src), committed(self.request, 1))
        calls = self.commit_calls(src)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], dict(expected_epoch=0, snapshot_at=10,
                                           valid_until=100, binding=binding(self.request)))
        self.assertEqual((src.epoch, src.writes), (1, 1))
        self.assertEqual(src.dump()['policy'], dict(policy_id='policy', revision='p2',
                                                    digest='pd2', mutable_by_policy_change=True))
        self.assertEqual([c[0] for c in src.calls],
                         ['snapshot_provider', 'current_epoch', 'commit_if_epoch'])

    def test_P8_A01_policy_ABA(self):
        src = ReferenceSource()
        def aba(s):
            s.set_policy('p2', 'pd-x'); s.set_policy('p1', 'pd1')
        src.pre_commit_hooks.append(aba)
        self.assertEqual(self.run_entry(src), not_committed('AUTHORITY_STATE_CHANGED'))
        self.assertEqual(src.writes, 0)

    def test_P8_A02_revocation_ABA(self):
        src = ReferenceSource()
        def aba(s):
            s.revoke('leaf', True); s.revoke('leaf', False)
        src.pre_commit_hooks.append(aba)
        self.assertEqual(self.run_entry(src), not_committed('AUTHORITY_STATE_CHANGED'))
        self.assertEqual(src.writes, 0)


class SingleUse(Harness):
    def test_P8_U01_one_commit_per_snapshot_epoch(self):
        src = ReferenceSource()
        inner = {}
        src.pre_commit_hooks.append(lambda s: inner.setdefault('B', self.run_entry(s)))
        outer = self.run_entry(src)
        self.assertEqual(inner['B'], committed(self.request, 1))
        self.assertEqual(outer, not_committed('AUTHORITY_STATE_CHANGED'))
        self.assertEqual(src.writes, 1)

    def test_P8_U02_identical_request_after_commit(self):
        src = ReferenceSource()
        self.assertEqual(self.run_entry(src), committed(self.request, 1))
        src.calls.clear()
        self.assertEqual(self.run_entry(src), not_committed('POLICY_STATE_MISMATCH'))
        self.assertEqual(self.commit_calls(src), [])

    def test_P8_U03_no_replay_protection_non_claim(self):
        src = ReferenceSource()
        self.assertEqual(self.run_entry(src), committed(self.request, 1))
        src.set_policy('p1', 'pd1')   # independent, separately authorized revert
        self.assertEqual(self.run_entry(src), committed(self.request, 3))
        self.assertEqual(src.writes, 2)

    def test_P8_U04_no_prior_result_parameters(self):
        for keyword in ['prior_result', 'state_epoch', 'snapshot_at', 'valid_until']:
            with self.subTest(keyword=keyword):
                src = ReferenceSource()
                kwargs = dict(request=base_request(), authenticate=lambda s: 'ESTABLISHED',
                              snapshot_provider=src.snapshot_provider,
                              current_epoch=src.current_epoch,
                              verify_grant=lambda r, a: 'VERIFIED',
                              commit_if_epoch=src.commit_if_epoch)
                kwargs[keyword] = 0
                with self.assertRaises(TypeError):
                    self.module.commit_policy_change(**kwargs)
                self.assertEqual(src.calls, [])


class SeamRejections(Harness):
    def rejected(self, src, prepare, expected):
        captured = {}
        def hook(s):
            prepare(s)
            captured['before'] = s.dump()
        src.pre_commit_hooks.append(hook)
        self.assertEqual(self.run_entry(src), expected)
        self.assertEqual(src.dump(), captured['before'])
        self.assertEqual(src.writes, 0)
        self.assertEqual(len(self.commit_calls(src)), 1)

    def test_P8_Z01_each_rejection_writes_nothing(self):
        cases = [
            ('TIME_REGRESSION', lambda s: setattr(s, 'clock', 9), commit_error()),
            ('EPOCH_MISMATCH', lambda s: s.touch(), not_committed('AUTHORITY_STATE_CHANGED')),
            ('NOT_CURRENT', lambda s: setattr(s, 'clock', 100),
             not_committed('AUTHORITY_NOT_CURRENT')),
        ]
        for name, prepare, expected in cases:
            with self.subTest(outcome=name):
                self.rejected(ReferenceSource(), prepare, expected)

    def test_P8_Z02_boundaries_commit(self):
        for clock in [10, 99]:
            with self.subTest(clock=clock):
                src = ReferenceSource()
                src.pre_commit_hooks.append(lambda s, c=clock: setattr(s, 'clock', c))
                self.assertEqual(self.run_entry(src), committed(self.request, 1))

    # Z03 corrected per review 2026-10-09 (RED record §5): the original case
    # required an intermediate expiring before the leaf, which #92 attenuation
    # (child.expires_at <= parent.expires_at) makes unreachable. Semantics of
    # valid_until = min(chain expires_at) and of attenuation are unchanged.
    @staticmethod
    def three_link_source(leaf_expires, middle_expires, root_expires):
        return ReferenceSource(max_grants=3, grants=[
            grant('leaf', 'alice', 'middle-subject', 'middle', expires_at=leaf_expires),
            grant('middle', 'middle-subject', 'root-subject', 'root', expires_at=middle_expires),
            grant('root', 'root-subject', 'external', None, expires_at=root_expires),
            grant('other', 'bob', 'external', None)])

    def test_P8_Z03_chain_minimum_reachable(self):
        src = self.three_link_source(50, 75, 100)
        self.rejected(src, lambda s: setattr(s, 'clock', 60),
                      not_committed('AUTHORITY_NOT_CURRENT'))
        self.assertEqual(self.commit_calls(src)[0][1]['snapshot_at'], 10)
        self.assertEqual(self.commit_calls(src)[0][1]['valid_until'], 50)

    def test_P8_Z03_intermediate_earlier_than_leaf_is_scope_violation(self):
        src = self.three_link_source(100, 50, 100)
        self.assertEqual(self.run_entry(src), not_committed('AUTHORITY_SCOPE_VIOLATION'))
        self.assertEqual(self.commit_calls(src), [])
        self.assertEqual(src.writes, 0)

    def test_P8_P01_epoch_mismatch_and_expired(self):
        def prepare(s):
            s.touch(); s.clock = 100
        self.rejected(ReferenceSource(), prepare, not_committed('AUTHORITY_STATE_CHANGED'))

    def test_P8_P02_time_regression_and_epoch_mismatch(self):
        def prepare(s):
            s.touch(); s.clock = 9
        self.rejected(ReferenceSource(), prepare, commit_error())

    def test_P8_P03_tightest_window(self):
        def tight():
            return ReferenceSource(grants=[
                grant('leaf', 'alice', 'root-subject', 'root', expires_at=11),
                grant('root', 'root-subject', 'external', None),
                grant('other', 'bob', 'external', None)])
        for clock, mismatch, expected in [
                (9, False, commit_error()),
                (11, False, not_committed('AUTHORITY_NOT_CURRENT')),
                (9, True, commit_error()),
                (11, True, not_committed('AUTHORITY_STATE_CHANGED'))]:
            with self.subTest(clock=clock, mismatch=mismatch):
                def prepare(s, c=clock, m=mismatch):
                    if m: s.touch()
                    s.clock = c
                self.rejected(tight(), prepare, expected)
        src = tight()
        self.assertEqual(self.run_entry(src), committed(self.request, 1))
        self.assertEqual(self.commit_calls(src)[0][1]['valid_until'], 11)


class SeamFailures(Harness):
    def wrap(self, src, behaviour):
        self.wrapper_calls = 0
        self.calls_at_commit = None
        def commit(**kwargs):
            self.wrapper_calls += 1
            self.calls_at_commit = len(src.calls)
            return behaviour(src, kwargs)
        return commit

    def assert_no_calls_after(self, src):
        self.assertEqual(self.wrapper_calls, 1)
        self.assertEqual(len(src.calls), self.calls_at_commit)

    def test_P8_X01_raise_after_write(self):
        src = ReferenceSource()
        def behaviour(s, kwargs):
            s.commit_if_epoch(**kwargs)
            raise RuntimeError('after write')
        self.assertEqual(self.run_entry(src, commit=self.wrap(src, behaviour)), unknown())
        self.assertEqual((src.epoch, src.writes), (1, 1))
        self.assertEqual(src.dump()['policy']['revision'], 'p2')
        # the inner reference call is logged before the wrapper returns
        self.assertEqual(self.wrapper_calls, 1)
        self.assertEqual(len(src.calls), self.calls_at_commit + 1)

    def test_P8_X02_raise_before_write(self):
        src = ReferenceSource()
        before = src.dump()
        def behaviour(s, kwargs):
            raise RuntimeError('before write')
        self.assertEqual(self.run_entry(src, commit=self.wrap(src, behaviour)), unknown())
        self.assertEqual((src.dump(), src.writes), (before, 0))
        self.assert_no_calls_after(src)

    def test_P8_X03_malformed_returns(self):
        class DictSubclass(dict):
            pass
        returns = [
            ('non-dict', 'COMMITTED'),
            ('list', []),
            ('dict subclass', DictSubclass(outcome='COMMITTED', committed_epoch=1)),
            ('extra key', dict(outcome='COMMITTED', committed_epoch=1, x=1)),
            ('missing key', dict(outcome='COMMITTED')),
            ('unknown outcome', dict(outcome='DONE', committed_epoch=None)),
            ('committed None', dict(outcome='COMMITTED', committed_epoch=None)),
            ('committed expected', dict(outcome='COMMITTED', committed_epoch=0)),
            ('committed expected-1', dict(outcome='COMMITTED', committed_epoch=-1)),
            ('committed bool', dict(outcome='COMMITTED', committed_epoch=True)),
            ('committed str', dict(outcome='COMMITTED', committed_epoch='6')),
            ('mismatch with epoch', dict(outcome='EPOCH_MISMATCH', committed_epoch=1)),
        ]
        for name, value in returns:
            with self.subTest(case=name):
                src = ReferenceSource()
                commit = self.wrap(src, lambda s, kwargs, v=value: v)
                self.assertEqual(self.run_entry(src, commit=commit), unknown())
                self.assert_no_calls_after(src)

    def test_P8_X04_no_calls_after_commit_seam(self):
        # X04 is asserted inside X01-X03; this case adds the positive path.
        src = ReferenceSource()
        commit = self.wrap(src, lambda s, kwargs: s.commit_if_epoch(**kwargs))
        self.assertEqual(self.run_entry(src, commit=commit), committed(self.request, 1))
        self.assertEqual(self.wrapper_calls, 1)
        self.assertEqual(len(src.calls), self.calls_at_commit + 1)

    def test_P8_T04_seam_return_hash_collision(self):
        src = ReferenceSource()
        value = {Collider('outcome'): 'COMMITTED', 'committed_epoch': 1}
        self.assertEqual(len(value), 2)
        RECORDER.clear()
        self.assertFalse('outcome' in value)
        self.assertGreaterEqual(len(RECORDER), 1, 'fixture defect: control lookup not detected')
        RECORDER.clear()
        commit = self.wrap(src, lambda s, kwargs: value)
        self.assertEqual(self.run_entry(src, commit=commit), unknown())
        self.assertEqual(RECORDER, [])


class ConsistencyObligations(Harness):
    """O02/O03 are positive non-claim tests: O1 violations in these directions
    are undetectable by the resolver (interface §2.2)."""

    def test_P8_O02_lagging_content_commits(self):
        src = ReferenceSource()
        stale = src.snapshot_provider()          # E0, leaf unrevoked
        src.revoke('leaf')                       # E1
        def lagging():
            out = dict(stale); out['state_epoch'] = src.epoch
            return out
        self.assertEqual(self.run_entry(src, provider=lagging), committed(self.request, 2))

    def test_P8_O03_torn_content_commits(self):
        src = ReferenceSource()
        old = src.snapshot_provider()            # E0
        src.revoke('leaf')                       # E1
        def torn():
            new = src.snapshot_provider()
            new['grants'] = old['grants']
            return new
        self.assertEqual(self.run_entry(src, provider=torn), committed(self.request, 2))

    def test_P8_O04_leading_content_fails_closed(self):
        src = ReferenceSource()
        def leading():
            new = src.snapshot_provider()
            label = src.epoch
            src.touch()                          # content stays authorizable
            fresh = src.snapshot_provider()
            fresh['state_epoch'] = label         # content E+1, label E
            return fresh
        self.assertEqual(self.run_entry(src, provider=leading),
                         not_committed('AUTHORITY_STATE_CHANGED'))
        self.assertEqual(self.commit_calls(src), [])


class NoOpRequest(Harness):
    def test_P8_V01_both_unchanged(self):
        src = ReferenceSource()
        self.request.update(proposed_revision='p1', proposed_digest='pd1')
        self.assertEqual(self.run_entry(src), not_committed('INVALID_AUTHORITY_INPUT'))
        self.assertEqual((self.auth_calls, self.verify_calls, src.calls), ([], [], []))

    def test_P8_V02_one_unchanged_positive_control(self):
        for revision, digest in [('p1', 'pd2'), ('p2', 'pd1')]:
            with self.subTest(revision=revision, digest=digest):
                src = ReferenceSource()
                self.request = base_request(proposed_revision=revision, proposed_digest=digest)
                self.assertEqual(self.run_entry(src), committed(self.request, 1))

    def test_P8_V03_precedes_authentication(self):
        for outcome in ['NOT_ESTABLISHED', 'VERIFICATION_ERROR']:
            with self.subTest(outcome=outcome):
                src = ReferenceSource(); self.auth_calls = []; self.verify_calls = []
                self.request = base_request(proposed_revision='p1', proposed_digest='pd1')
                self.assertEqual(self.run_entry(src, authentication=outcome),
                                 not_committed('INVALID_AUTHORITY_INPUT'))
                self.assertEqual((self.auth_calls, self.verify_calls, src.calls), ([], [], []))


if __name__ == '__main__':
    unittest.main()
