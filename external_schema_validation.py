"""Schema-driven validation for synthetic multi-decision snapshots."""

import copy
import re

from external_validation import _validate_input

class SchemaValidationError(RuntimeError):
    def __init__(self, stage, code, failure_record):
        super().__init__(f"{stage}: {code}")
        self.stage = stage
        self.code = code
        self.failure_record = failure_record
        self.persistence_error = None

def _require(condition, message):
    if not condition:
        raise ValueError(message)

def _segments(path, template=False):
    _require(isinstance(path, str) and path.startswith("/"),
             "Expected nonempty JSON Pointer")
    parts = path[1:].split("/")
    for part in parts:
        if template and part == "{record_id}":
            continue
        _require("{" not in part and "}" not in part,
                 "Invalid template variable")
        _require(re.search(r"~(?![01])", part) is None,
                 "Invalid JSON Pointer escape")
    return [part.replace("~1", "/").replace("~0", "~") for part in parts]

MISSING = object()

def _escape(value):
    _require(isinstance(value, str) and value, "Invalid record identity")
    return value.replace("~", "~0").replace("/", "~1")

def _bind(template, record_id):
    _segments(template, template=True)
    return template.replace("{record_id}", _escape(record_id))

def _read(document, path):
    value = document
    for token in _segments(path):
        if isinstance(value, dict):
            if token not in value:
                return MISSING
            value = value[token]
        elif isinstance(value, list):
            _require(re.fullmatch(r"0|[1-9][0-9]*", token) is not None,
                     "Invalid array index")
            index = int(token)
            if index >= len(value):
                return MISSING
            value = value[index]
        else:
            raise ValueError("Path traverses a scalar")
    return value

def _validate_schema(schema):
    _require(isinstance(schema, dict), "Invalid schema")
    _require(isinstance(schema.get("schema_revision"), str) and
             schema["schema_revision"], "Missing schema revision")
    for field in ("registry_path", "canonical_identities_path"):
        _segments(schema.get(field))
    rules = schema.get("rules")
    _require(isinstance(rules, list) and rules, "Missing schema rules")
    identifiers, targets = set(), set()
    selectors = schema.get("selectors")
    kinds = {"adoption", "output", "presentation", "source", "verification"}
    _require(isinstance(selectors, dict) and set(selectors) == kinds,
             "Invalid selector declarations")
    for rule in rules:
        _require(isinstance(rule, dict), "Invalid rule")
        identifier = rule.get("rule_id")
        _require(isinstance(identifier, str) and identifier and
                 identifier not in identifiers, "Invalid or duplicate rule ID")
        identifiers.add(identifier)
        kind = rule.get("kind")
        _require(kind in kinds and rule.get("selector") == kind,
                 "Invalid rule selector or kind")
        target = rule.get("target_template")
        parts = _segments(target, template=True)
        _require(parts.count("{record_id}") == 1,
                 "Template must bind one record ID")
        _require(parts[:2] == ["registry", "{record_id}"],
                 "Target must address the checker registry")
        key = (kind, target)
        _require(key not in targets, "Duplicate expanded target declaration")
        targets.add(key)
        _require(type(rule.get("required_for_checker")) is bool and
                 type(rule.get("nullable")) is bool, "Missing rule policy")
        _require(rule.get("target_type") in {
            "object", "array", "string", "integer", "boolean", "null", "version"
        }, "Invalid target type")
        status = rule.get("mapping_status")
        _require(status in ("MAPPABLE", "UNMAPPABLE"),
                 "Invalid mapping status")
        if status == "MAPPABLE":
            source = rule.get("source_template")
            source_parts = _segments(source, template=True)
            _require(source_parts.count("{record_id}") == 1,
                     "Source template must bind one record ID")
            _require(rule.get("transformation") == "identity",
                     "Unsupported transformation")
        else:
            _require(rule.get("source_template") is None and
                     rule.get("transformation") is None,
                     "Unmappable rule must not invent a source mapping")
            _require(isinstance(rule.get("reason"), str) and rule["reason"],
                     "Missing unmappable reason")
        semantics = rule.get("absence_semantics")
        _require(isinstance(semantics, dict), "Missing absence semantics")
        _require(all(
            semantics.get(key) in ("scoped_evidence", "value")
            for key in ("missing", "null", "empty")
        ), "Invalid absence semantics")
    for kind in kinds:
        root = "/registry/{record_id}"
        _require((kind, root) in targets, "Missing record-root rule")
    inventory = schema.get("inventory")
    _require(isinstance(inventory, dict), "Missing inventory declaration")
    _segments(inventory.get("source_path"))
    for field in ("decision_id_field", "adoption_ref_field"):
        _require(isinstance(inventory.get(field), str) and inventory[field],
                 "Invalid inventory field declaration")
    _validate_selectors(selectors)

def _validate_selectors(selectors):
    for kind, selector in selectors.items():
        _require(isinstance(selector, dict), "Invalid selector")
        parent = selector.get("from")
        _require(parent == "inventory" or parent in selectors,
                 "Unknown selector parent")
        reference = selector.get("reference")
        if parent == "inventory":
            _require(kind == "adoption", "Invalid inventory selector")
            _require(isinstance(reference, str) and reference and
                     "/" not in reference, "Invalid inventory reference field")
        else:
            _segments(reference)
        member = selector.get("member_reference")
        if member is not None:
            _require(isinstance(member, str) and member and "/" not in member,
                     "Invalid collection reference field")
    _require(selectors["adoption"]["from"] == "inventory",
             "Adoption must resolve from inventory")
    for kind in selectors:
        visited = set()
        current = kind
        while current != "inventory":
            _require(current not in visited, "Cyclic selector dependency")
            visited.add(current)
            current = selectors[current]["from"]

def _selector_order(selectors):
    ordered = []
    pending = set(selectors)
    while pending:
        ready = sorted(
            kind for kind in pending
            if selectors[kind]["from"] == "inventory"
            or selectors[kind]["from"] in ordered
        )
        _require(bool(ready), "Unresolvable selector dependencies")
        ordered.extend(ready)
        pending.difference_update(ready)
    return ordered

def _validate_inventory(snapshot, schema, inventory):
    _require(isinstance(snapshot, dict), "Invalid snapshot")
    _require(isinstance(snapshot.get("snapshot_id"), str) and
             snapshot["snapshot_id"], "Missing snapshot identity")
    payload = snapshot.get("payload")
    _require(isinstance(payload, dict), "Invalid snapshot payload")
    declaration = schema["inventory"]
    exported = _read(payload, declaration["source_path"])
    if inventory is None:
        _require(exported is MISSING or exported is None,
                 "Available inventory must not be silently discarded")
        return None
    _require(isinstance(inventory, dict), "Invalid inventory")
    _require(inventory.get("source_snapshot_id") == snapshot["snapshot_id"],
             "Inventory snapshot mismatch")
    _require(isinstance(inventory.get("inventory_revision"), str) and
             inventory["inventory_revision"], "Missing inventory revision")
    entries = inventory.get("entries")
    _require(isinstance(entries, list) and isinstance(exported, list),
             "Invalid inventory entries")
    _require(inventory.get("coverage") in ("export_only", "scoped_complete"),
             "Invalid inventory coverage")
    _require(isinstance(inventory.get("exclusions"), list) and
             isinstance(inventory.get("evidence_refs"), list),
             "Missing inventory coverage detail")
    _require(len(entries) == len(exported), "Inventory entry count mismatch")
    seen = set()
    for index, entry in enumerate(entries):
        _require(isinstance(entry, dict), "Invalid inventory entry")
        identifier = entry.get("decision_id")
        _require(isinstance(identifier, str) and identifier and
                 identifier not in seen, "Invalid or duplicate decision ID")
        seen.add(identifier)
        source_entry = exported[index]
        _require(isinstance(source_entry, dict), "Invalid source decision")
        _require(source_entry.get(declaration["decision_id_field"]) == identifier,
                 "Decision identity disagrees with source")
        adoption_id = entry.get("adoption_id")
        _escape(adoption_id)
        _require(source_entry.get(declaration["adoption_ref_field"]) == adoption_id,
                 "Adoption reference disagrees with source")
        expected_path = (
            declaration["source_path"] + "/" + str(index) + "/"
            + _escape(declaration["adoption_ref_field"])
        )
        _require(entry.get("source_path") == expected_path,
                 "Invalid adoption reference provenance")
        _require(_read(payload, expected_path) == adoption_id,
                 "Unresolved adoption reference provenance")
    return sorted(entries, key=lambda entry: entry["decision_id"])

def _validate_evidence(evidence, snapshot_id):
    _require(isinstance(evidence, list), "Invalid coverage evidence")
    seen = set()
    for item in evidence:
        _require(isinstance(item, dict), "Invalid evidence entry")
        for field in ("evidence_id", "reference", "asserted_by",
                      "asserted_at", "coverage_scope", "assertion"):
            _require(isinstance(item.get(field), str) and item[field],
                     "Missing evidence field: " + field)
        _require(item["evidence_id"] not in seen, "Duplicate evidence ID")
        seen.add(item["evidence_id"])
        _require(item.get("source_snapshot_id") == snapshot_id,
                 "Evidence snapshot mismatch")
        _segments(item["coverage_scope"])
        _require(type(item.get("includes_descendants")) is bool,
                 "Missing evidence scope policy")

def _coverage_for(evidence, decision_id, path):
    target = _segments(path)
    matched = []
    for item in evidence:
        if item.get("decision_id") not in (None, decision_id):
            continue
        scope = _segments(item["coverage_scope"])
        if target == scope or (
            item["includes_descendants"] and target[:len(scope)] == scope
        ):
            matched.append(item)
    return sorted(matched, key=lambda item: item["evidence_id"])

def _finding(record, decision_id, rule, path, evidence, affected=None):
    if rule["mapping_status"] == "UNMAPPABLE":
        code = "ADAPTER_UNMAPPABLE"
        explanation = "Frozen mapping declares no faithful representation."
        matched = []
    else:
        matched = _coverage_for(evidence, decision_id, path)
        absent = bool(matched) and all(
            item["assertion"] == "source_record_absent" for item in matched
        )
        code = "EXTERNAL_RECORD_ABSENT" if absent else "SOURCE_COVERAGE_UNKNOWN"
        explanation = (
            "Scoped evidence establishes source absence."
            if absent else "Source absence is not established."
        )
    return {
        "code": code, "decision_id": decision_id,
        "rule_id": rule["rule_id"], "target_path": path,
        "source_snapshot_id": record["source_snapshot_id"],
        "schema_revision": record["schema_revision"],
        "inventory_revision": record["inventory_revision"],
        "evidence_refs": [item["evidence_id"] for item in matched],
        "explanation": explanation,
        "affected_targets": affected or [],
    }

def _select_subjects(entry, registry, schema):
    subjects, blockers = {}, {}
    for kind in _selector_order(schema["selectors"]):
        selector = schema["selectors"][kind]
        parent = selector["from"]
        identifiers = []
        blocked_by = None
        if parent == "inventory":
            identifiers = [entry["adoption_id"]]
        else:
            blocked_by = blockers.get(parent)
            for parent_id in subjects[parent]:
                parent_record = registry.get(parent_id, MISSING)
                parent_path = "/registry/" + _escape(parent_id)
                if parent_record is MISSING:
                    blocked_by = blocked_by or parent_path
                    continue
                _require(isinstance(parent_record, dict) and
                         parent_record.get("kind") == parent and
                         parent_record.get("id") == parent_id,
                         "Invalid referenced parent record")
                value = _read(parent_record, selector["reference"])
                if value is MISSING:
                    blocked_by = blocked_by or (
                        parent_path + selector["reference"]
                    )
                    continue
                member = selector.get("member_reference")
                if member is None:
                    if value is not None:
                        _escape(value)
                        identifiers.append(value)
                else:
                    _require(isinstance(value, list),
                             "Selector collection must be an array")
                    for item in value:
                        _require(isinstance(item, dict),
                                 "Invalid selector collection member")
                        reference = item.get(member, MISSING)
                        if reference is MISSING:
                            _require(member == "verification_ref",
                                     "Missing required member reference")
                            continue
                        if reference is not None:
                            _escape(reference)
                            identifiers.append(reference)
        identifiers = sorted(set(identifiers))
        for identifier in identifiers:
            selected = registry.get(identifier, MISSING)
            if selected is not MISSING:
                _require(isinstance(selected, dict) and
                         selected.get("id") == identifier and
                         selected.get("kind") == kind,
                         "Referenced record ID or kind mismatch")
        subjects[kind] = identifiers
        blockers[kind] = blocked_by
    return subjects, blockers

def _record_selections(record, decision_id, subjects, blockers):
    for kind in sorted(subjects):
        blocker = blockers[kind]
        record["selections"].append({
            "decision_id": decision_id,
            "selector": kind,
            "selection_count": len(subjects[kind]),
            "status": "blocked_by_ancestor" if blocker else "resolved",
            "blocked_by": blocker,
        })

def _expansion_row(record, decision_id, rule, identifier,
                   status="resolved", blocked_by=None):
    source = rule["source_template"]
    return {
        "schema_revision": record["schema_revision"],
        "source_snapshot_id": record["source_snapshot_id"],
        "inventory_revision": record["inventory_revision"],
        "decision_id": decision_id,
        "rule_id": rule["rule_id"],
        "record_id": identifier,
        "source_path": _bind(source, identifier) if source is not None else None,
        "target_path": _bind(rule["target_template"], identifier),
        "status": status,
        "blocked_by": blocked_by,
    }

def _affected_target(rule, identifier):
    return {
        "rule_id": rule["rule_id"],
        "target_path": _bind(rule["target_template"], identifier),
        "required_for_checker": rule["required_for_checker"],
    }

def _expand_missing_root(record, decision_id, rules, identifier, evidence):
    root_path = "/registry/" + _escape(identifier)
    root_rule = next(
        rule for rule in rules
        if _bind(rule["target_template"], identifier) == root_path
    )
    primary = _finding(
        record, decision_id, root_rule, root_path, evidence
    )
    blocked = False
    for rule in rules:
        path = _bind(rule["target_template"], identifier)
        is_root = path == root_path
        record["expansion"].append(_expansion_row(
            record, decision_id, rule, identifier,
            status="missing_root" if is_root else "blocked_by_ancestor",
            blocked_by=None if is_root else root_path,
        ))
        blocked = blocked or rule["required_for_checker"]
        if is_root:
            continue
        child = _finding(record, decision_id, rule, path, evidence)
        same_basis = (
            child["code"] == primary["code"]
            and child["evidence_refs"] == primary["evidence_refs"]
        )
        if same_basis:
            primary["affected_targets"].append(
                _affected_target(rule, identifier)
            )
        else:
            record["findings"].append(child)
    record["findings"].append(primary)
    return blocked

def _validate_value(value, rule):
    if value is None and rule["nullable"]:
        return
    kind = rule["target_type"]
    valid = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": type(value) is int,
        "boolean": type(value) is bool,
        "null": value is None,
        "version": type(value) is int or (
            isinstance(value, str) and bool(value)
        ),
    }
    _require(valid[kind], "Source field type disagrees with schema")

def _expand_present(record, decision_id, rules, identifier,
                    payload, evidence):
    blocked = False
    for rule in rules:
        row = _expansion_row(record, decision_id, rule, identifier)
        record["expansion"].append(row)
        if rule["mapping_status"] == "UNMAPPABLE":
            row["status"] = "unmappable"
            record["findings"].append(_finding(
                record, decision_id, rule, row["target_path"], evidence
            ))
            blocked = blocked or rule["required_for_checker"]
            continue
        value = _read(payload, row["source_path"])
        absence_kind = (
            "missing" if value is MISSING else
            "null" if value is None else
            "empty" if value == "" or value == [] or value == {} else None
        )
        missing = value is MISSING or (
            absence_kind is not None
            and rule["absence_semantics"][absence_kind] != "value"
        )
        if missing:
            row["status"] = "missing_field"
            record["findings"].append(_finding(
                record, decision_id, rule, row["target_path"], evidence
            ))
            blocked = blocked or rule["required_for_checker"]
        else:
            _validate_value(value, rule)
    return blocked

def _expand_decision(record, entry, schema, payload, registry, evidence):
    decision_id = entry["decision_id"]
    subjects, blockers = _select_subjects(entry, registry, schema)
    _record_selections(record, decision_id, subjects, blockers)
    blocked = False
    for kind in sorted(subjects):
        rules = sorted(
            (rule for rule in schema["rules"] if rule["kind"] == kind),
            key=lambda rule: rule["rule_id"],
        )
        for identifier in subjects[kind]:
            if identifier not in registry:
                affected = _expand_missing_root(
                    record, decision_id, rules, identifier, evidence
                )
            else:
                affected = _expand_present(
                    record, decision_id, rules, identifier, payload, evidence
                )
            blocked = blocked or affected
    return subjects, blocked

def _checker_input(entry, subjects, schema, payload, registry):
    selected = {
        identifier
        for identifiers in subjects.values()
        for identifier in identifiers
        if identifier in registry
    }
    inputs = {
        "adoption_id": entry["adoption_id"],
        "registry": {},
        "canonical_identities": copy.deepcopy(
            _read(payload, schema["canonical_identities_path"])
        ),
    }
    for kind, identifiers in subjects.items():
        root_rule = next(
            rule for rule in schema["rules"]
            if rule["kind"] == kind and
            rule["target_template"] == "/registry/{record_id}"
        )
        if root_rule["mapping_status"] == "UNMAPPABLE":
            continue
        for identifier in identifiers:
            if identifier not in selected:
                continue
            source_path = _bind(root_rule["source_template"], identifier)
            source = _read(payload, source_path)
            _require(source is not MISSING, "Mapped record root unavailable")
            inputs["registry"][identifier] = copy.deepcopy(source)
    _validate_input(inputs)
    return inputs

def _sort_record(record):
    record["expansion"].sort(key=lambda row: (
        row["decision_id"], row["rule_id"], row["target_path"]
    ))
    record["selections"].sort(key=lambda row: (
        row["decision_id"], row["selector"]
    ))
    record["findings"].sort(key=lambda row: (
        row["decision_id"] or "", row["target_path"], row["rule_id"]
    ))

def _fail(record, stage, code, cause, failure_sink, decision_id=None):
    _sort_record(record)
    failure = copy.deepcopy(record)
    failure.update({
        "stage": stage,
        "code": code,
        "failed_decision_id": decision_id,
        "cause_type": type(cause).__name__,
        "cause_message": str(cause),
    })
    error = SchemaValidationError(stage, code, failure)
    try:
        failure_sink(failure)
    except Exception as persistence_error:
        error.persistence_error = persistence_error
    raise error from cause

def _new_record(snapshot, schema, inventory):
    return {
        "schema_revision": (
            schema.get("schema_revision") if isinstance(schema, dict) else None
        ),
        "source_snapshot_id": (
            snapshot.get("snapshot_id") if isinstance(snapshot, dict) else None
        ),
        "inventory_revision": (
            inventory.get("inventory_revision")
            if isinstance(inventory, dict) else None
        ),
        "inventory_coverage": (
            {key: copy.deepcopy(inventory.get(key))
             for key in ("coverage", "exclusions", "evidence_refs")}
            if isinstance(inventory, dict) else None
        ),
        "expansion": [], "selections": [],
        "findings": [], "decisions": [],
    }

def run_schema_validation(*, source_snapshot, schema, inventory,
                          coverage_evidence, checker, failure_sink):
    record = _new_record(source_snapshot, schema, inventory)
    try:
        schema = copy.deepcopy(schema)
        _validate_schema(schema)
    except Exception as cause:
        _fail(record, "schema_validation", "SCHEMA_INVALID",
              cause, failure_sink)
    try:
        snapshot = copy.deepcopy(source_snapshot)
        inventory = copy.deepcopy(inventory)
        evidence = copy.deepcopy(coverage_evidence)
        entries = _validate_inventory(snapshot, schema, inventory)
        _validate_evidence(evidence, snapshot["snapshot_id"])
    except Exception as cause:
        _fail(record, "input_validation", "ADAPTED_INPUT_INVALID",
              cause, failure_sink)
    if entries is None:
        path = schema["inventory"]["source_path"]
        rule = {
            "rule_id": "inventory",
            "mapping_status": "MAPPABLE",
        }
        record["findings"].append(_finding(
            record, None, rule, path, evidence
        ))
        return record
    record["decisions"] = [
        {
            "decision_id": entry["decision_id"],
            "status": "not_executed",
            "checker_invoked": False,
            "checker_result": None,
        }
        for entry in entries
    ]
    try:
        payload = snapshot["payload"]
        registry = _read(payload, schema["registry_path"])
        _require(isinstance(registry, dict), "Invalid source registry")
    except Exception as cause:
        _fail(record, "input_validation", "ADAPTED_INPUT_INVALID",
              cause, failure_sink)
    for entry, decision in zip(entries, record["decisions"]):
        identifier = entry["decision_id"]
        try:
            subjects, blocked = _expand_decision(
                record, entry, schema, payload, registry, evidence
            )
            if blocked:
                decision["status"] = "blocked"
                continue
            inputs = _checker_input(
                entry, subjects, schema, payload, registry
            )
        except Exception as cause:
            decision["status"] = "execution_error"
            _fail(record, "input_validation", "ADAPTED_INPUT_INVALID",
                  cause, failure_sink, identifier)
        decision["checker_invoked"] = True
        try:
            decision["checker_result"] = checker(**copy.deepcopy(inputs))
            decision["status"] = "evaluated"
        except Exception as cause:
            decision["status"] = "execution_error"
            _fail(record, "checker_execution", "CHECKER_EXECUTION_ERROR",
                  cause, failure_sink, identifier)
    _sort_record(record)
    return record
