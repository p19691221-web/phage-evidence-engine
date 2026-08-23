from datetime import datetime, timezone

from phage_lineage_contract_v0_1 import (
    Evidence,
    LineageChecker,
    LineagePolicy,
    LineageStatus,
)

UTC = timezone.utc
CUTOFF = datetime(1914, 7, 29, 23, 59, 59, tzinfo=UTC)


def dt(y, m, d):
    return datetime(y, m, d, 0, 0, 0, tzinfo=UTC)


def run():
    # A — direct future evidence
    store_a = {
        "EV_FUTURE": Evidence(
            evidence_id="EV_FUTURE",
            observed_at=dt(1914, 8, 1),
            available_at=dt(1914, 8, 1),
        )
    }
    a = LineageChecker(store_a).check("EV_FUTURE", CUTOFF)
    assert a.status == LineageStatus.EPISTEMIC_BOUNDARY_VIOLATION

    # B — pre-cutoff artifact derived from future evidence
    store_b = {
        "SUMMARY_0729": Evidence(
            evidence_id="SUMMARY_0729",
            observed_at=dt(1914, 7, 29),
            available_at=dt(1914, 7, 29),
            derived_from=("EV_FUTURE",),
        ),
        "EV_FUTURE": Evidence(
            evidence_id="EV_FUTURE",
            observed_at=dt(1914, 8, 1),
            available_at=dt(1914, 8, 1),
        ),
    }
    b = LineageChecker(store_b).check("SUMMARY_0729", CUTOFF)
    assert b.status == LineageStatus.DERIVATION_BOUNDARY_VIOLATION

    # C — missing ancestor
    store_c = {
        "SUMMARY_0729": Evidence(
            evidence_id="SUMMARY_0729",
            observed_at=dt(1914, 7, 29),
            available_at=dt(1914, 7, 29),
            derived_from=("MISSING_PARENT",),
        )
    }
    c = LineageChecker(store_c).check("SUMMARY_0729", CUTOFF)
    assert c.status == LineageStatus.LINEAGE_UNRESOLVED

    # D — cycle
    store_d = {
        "A": Evidence("A", dt(1914, 7, 28), dt(1914, 7, 28), ("B",)),
        "B": Evidence("B", dt(1914, 7, 28), dt(1914, 7, 28), ("A",)),
    }
    d = LineageChecker(store_d).check("A", CUTOFF)
    assert d.status == LineageStatus.LINEAGE_CYCLE_DETECTED

    # E — clean multi-level lineage
    store_e = {
        "A": Evidence("A", dt(1914, 7, 29), dt(1914, 7, 29), ("B",)),
        "B": Evidence("B", dt(1914, 7, 28), dt(1914, 7, 28), ("C",)),
        "C": Evidence("C", dt(1914, 7, 27), dt(1914, 7, 27), ()),
    }
    e = LineageChecker(store_e, LineagePolicy(max_depth=64)).check("A", CUTOFF)
    assert e.status == LineageStatus.CLEAN

    print("A direct future evidence:", a.status.value)
    print("B future-derived artifact:", b.status.value)
    print("C missing ancestor:", c.status.value)
    print("D cycle:", d.status.value)
    print("E clean lineage:", e.status.value)
    print("ALL TESTS PASS")


if __name__ == "__main__":
    run()
