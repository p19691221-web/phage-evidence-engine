"""Inspect recorded relationships; no authority or judgment claims."""


def _record(registry, record_id, kind):
    item = registry.get(record_id)
    if item is None:
        return None
    if (type(item) is not dict or item.get("id") != record_id
            or item.get("kind") != kind):
        raise ValueError("Invalid registry record")
    return item


def _same(left, right):
    """Type-sensitive JSON equality: True must not equal version 1."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (left.keys() == right.keys()
                and all(_same(left[k], right[k]) for k in left))
    if type(left) is list:
        return (len(left) == len(right)
                and all(_same(a, b) for a, b in zip(left, right)))
    return left == right


def _output_binding(output):
    return {
        "output_id": output["id"],
        "output_version": output["version"],
        "content": output["content"],
    }


def _finding(condition):
    return "matched" if condition else "mismatch"


def _source_support(citation, registry):
    if citation is None:
        return "not_asserted"
    source = _record(registry, citation["source_id"], "source")
    if source is None:
        return "missing"
    return _finding(
        _same(source["version"], citation["source_version"])
        and _same(source["content"], citation["source_content"]))


def _verification_support(citation, output, registry, identities):
    if citation is None or not citation.get("verification_ref"):
        return "not_asserted"
    verification = _record(
        registry, citation["verification_ref"], "verification")
    if verification is None:
        return "missing"
    source_state = _source_support(citation, registry)
    if source_state != "matched":
        return source_state
    portions = dict(output["content"])
    portion = citation["portion_id"]
    return _finding(
        verification["recorder"] in identities
        and _same(verification["output_binding"],
                  _output_binding(output))
        and verification["portion_id"] == portion
        and portion in portions
        and _same(verification["portion_text"], portions[portion])
        and verification["source_id"] == citation["source_id"]
        and _same(verification["source_version"],
                  citation["source_version"])
        and _same(verification["source_content"],
                  citation["source_content"]))


def inspect_adoption(*, adoption_id, registry, canonical_identities):
    """Inspect synthetic records; never authorize or execute assessment."""
    identities = frozenset(canonical_identities)
    if not all(type(x) is str and x.isascii() and x
               for x in identities):
        raise ValueError("Invalid canonical identities")
    adoption = _record(registry, adoption_id, "adoption")
    if adoption is None:
        raise ValueError("Adoption record missing")
    binding = adoption["output_binding"]
    output = _record(registry, binding["output_id"], "output")
    if output is None:
        raise ValueError("Output record missing")
    portions = dict(output["content"])
    if len(portions) != len(output["content"]):
        raise ValueError("Duplicate portion IDs")
    citations = {}
    for citation in output["citations"]:
        portion = citation["portion_id"]
        if portion in citations:
            raise ValueError("Duplicate citation for portion")
        citations[portion] = citation
    adopted = adoption["adopted_portions"]
    relationships = {
        "A": _finding(
            adoption["decision_maker"] in identities
            and output["producer"] in identities
            and _same(binding, _output_binding(output))
            and all(p in portions for p in adopted)),
        "S": _source_support(citations.get("P1"), registry),
        "V": _verification_support(
            citations.get("P1"), output, registry, identities),
    }
    presentation = _record(
        registry, adoption["presentation_ref"], "presentation")
    if presentation is None:
        relationships.update(P="missing", L="missing", C="missing")
    else:
        same_person_context = (
            presentation["recipient"] == adoption["decision_maker"]
            and presentation["decision_context"]
            == adoption["decision_context"])
        relationships["P"] = _finding(
            presentation["recorder"] in identities
            and presentation["recipient"] in identities
            and same_person_context
            and _same(presentation["output_binding"],
                      _output_binding(output)))
        relationships["L"] = _finding(
            same_person_context
            and _same(binding, presentation["output_binding"]))
        if all(relationships[key] == "matched"
               for key in ("A", "P", "L")):
            relationships["C"] = _finding(
                all(p in presentation["presented_portions"]
                    for p in adopted))
        else:
            relationships["C"] = "not_assessable"
    adopted_support = {}
    for portion in adopted:
        if relationships["A"] != "matched":
            citation_state = verification_state = "not_assessable"
        else:
            citation = citations.get(portion)
            citation_state = _source_support(citation, registry)
            verification_state = _verification_support(
                citation, output, registry, identities)
        adopted_support[portion] = {
            "citation": citation_state,
            "verification": verification_state,
        }
    return {
        "adoption_id": adoption_id,
        "relationships": relationships,
        "adopted_support": adopted_support,
    }
