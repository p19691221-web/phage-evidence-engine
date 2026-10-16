"""Synthetic external-shaped validation boundary."""

import copy

MISSING = object()

class ExternalValidationError(RuntimeError):
    def __init__(self, stage, code, failure_record):
        super().__init__(f"{stage}: {code}")
        self.stage = stage
        self.code = code
        self.failure_record = failure_record
        self.persistence_error = None

def _pointer(document, path):
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("Expected nonempty JSON Pointer")
    value = document
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            if token not in value:
                return MISSING
            value = value[token]
        elif isinstance(value, list):
            if not token.isdigit() or (len(token) > 1 and token[0] == "0"):
                raise ValueError("Invalid array index")
            index = int(token)
            if index >= len(value):
                return MISSING
            value = value[index]
        else:
            raise ValueError("Source path traverses a scalar")
    return value

def _require(condition, message):
    if not condition:
        raise ValueError(message)

def _validate_manifest(snapshot, manifest):
    _require(isinstance(snapshot, dict), "Snapshot must be an object")
    _require(isinstance(manifest, dict), "Manifest must be an object")
    for key in ("manifest_revision", "source_snapshot_id",
                "reviewed_by", "reviewed_at"):
        _require(isinstance(manifest.get(key), str) and manifest[key],
                 f"Missing manifest field: {key}")
    _require(manifest["source_snapshot_id"] == snapshot.get("snapshot_id"),
             "Snapshot identity mismatch")
    _require(isinstance(snapshot.get("payload"), dict), "Invalid payload")
    mappings = manifest.get("mappings")
    evidence = manifest.get("evidence")
    _require(isinstance(mappings, list) and mappings, "Missing mappings")
    _require(isinstance(evidence, list), "Invalid evidence list")
    evidence_by_id = {}
    for item in evidence:
        _require(isinstance(item, dict), "Invalid evidence entry")
        for key in ("evidence_id", "reference", "asserted_by",
                    "asserted_at", "coverage_scope", "assertion"):
            _require(isinstance(item.get(key), str) and item[key],
                     f"Missing evidence field: {key}")
        identifier = item["evidence_id"]
        _require(identifier not in evidence_by_id, "Duplicate evidence ID")
        _require(type(item.get("includes_descendants")) is bool,
                 "Missing evidence scope policy")
        evidence_by_id[identifier] = item
    targets = set()
    for mapping in mappings:
        _require(isinstance(mapping, dict), "Invalid mapping")
        path = mapping.get("target_path")
        _require(isinstance(path, str) and path.startswith("/"),
                 "Invalid target path")
        _require(path not in targets, "Duplicate target path")
        targets.add(path)
        _require(type(mapping.get("required_for_checker")) is bool,
                 "Missing required-target policy")
        status = mapping.get("mapping_status")
        _require(status in ("MAPPABLE", "UNMAPPABLE"), "Invalid mapping status")
        _require(mapping.get("target_type") in
                 ("object", "array", "string", "integer", "null", "boolean"),
                 "Invalid target type")
        _require(mapping.get("coverage_scope") == path,
                 "Mapping coverage must identify its target")
        _require(isinstance(mapping.get("exclusions"), list),
                 "Missing exclusions")
        semantics = mapping.get("absence_semantics")
        _require(isinstance(semantics, dict), "Missing absence semantics")
        for kind in ("missing", "null", "empty"):
            _require(semantics.get(kind) in ("unknown", "source_absent", "value"),
                     "Invalid absence semantics")
        refs = mapping.get("coverage_evidence_refs")
        _require(isinstance(refs, list) and
                 all(isinstance(ref, str) for ref in refs),
                 "Invalid evidence references")
        _require(len(refs) == len(set(refs)), "Duplicate evidence reference")
        _require(all(ref in evidence_by_id for ref in refs),
                 "Unresolved evidence reference")
        if status == "MAPPABLE":
            source_path = mapping.get("source_path")
            _require(isinstance(source_path, str) and
                     source_path.startswith("/"), "Invalid source path")
            _require(mapping.get("transformation") == "identity",
                     "Unsupported transformation")
        else:
            _require(isinstance(mapping.get("reason"), str) and
                     mapping["reason"], "Missing unmappable reason")
            _require(mapping.get("source_path") is None and
                     mapping.get("transformation") is None,
                     "Unmappable target must not invent a source mapping")
    _require("/adoption_id" in targets and
             "/canonical_identities" in targets,
             "Missing checker argument mappings")
    return evidence_by_id

def _covers(evidence, path):
    scope = evidence["coverage_scope"]
    return path == scope or (
        evidence["includes_descendants"] and path.startswith(scope + "/")
    )

def _absence_established(mapping, evidence_by_id, kind):
    if mapping["absence_semantics"][kind] != "source_absent":
        return False
    if mapping["exclusions"]:
        return False
    referenced = [
        evidence_by_id[ref] for ref in mapping["coverage_evidence_refs"]
    ]
    scoped = [item for item in referenced
              if _covers(item, mapping["target_path"])]
    return bool(scoped) and all(
        item["assertion"] == "source_record_absent" for item in scoped
    )

def _preflight(snapshot, manifest, evidence_by_id):
    explanations = {
        "EXTERNAL_RECORD_ABSENT": "Scoped evidence establishes source absence.",
        "ADAPTER_UNMAPPABLE": "Frozen mapping declares no faithful representation.",
        "SOURCE_COVERAGE_UNKNOWN": "Source absence is not established.",
    }
    findings = []
    blocked = False
    for mapping in manifest["mappings"]:
        code = None
        if mapping["mapping_status"] == "UNMAPPABLE":
            code = "ADAPTER_UNMAPPABLE"
        else:
            value = _pointer(snapshot["payload"], mapping["source_path"])
            kind = (
                "missing" if value is MISSING else
                "null" if value is None else
                "empty" if value == "" or value == [] or value == {} else None
            )
            if kind is not None:
                semantics = mapping["absence_semantics"][kind]
                if kind == "missing" or semantics != "value":
                    code = (
                        "EXTERNAL_RECORD_ABSENT"
                        if _absence_established(mapping, evidence_by_id, kind)
                        else "SOURCE_COVERAGE_UNKNOWN"
                    )
        if code is not None:
            findings.append({
                "code": code, "target_path": mapping["target_path"],
                "source_snapshot_id": snapshot["snapshot_id"],
                "manifest_revision": manifest["manifest_revision"],
                "evidence_refs": list(mapping["coverage_evidence_refs"]),
                "explanation": explanations[code],
            })
            blocked = blocked or mapping["required_for_checker"]
    findings.sort(key=lambda item: item["target_path"])
    return findings, blocked

def _text(value):
    return isinstance(value, str) and bool(value)

def _validate_input(inputs):
    _require(isinstance(inputs, dict), "Adapter must return an object")
    _require(set(inputs) == {
        "adoption_id", "registry", "canonical_identities"
    }, "Invalid checker arguments")
    _require(_text(inputs["adoption_id"]), "Invalid adoption ID")
    identities = inputs["canonical_identities"]
    _require(isinstance(identities, list) and identities and
             all(_text(item) and item.isascii() for item in identities),
             "Invalid canonical identities")
    _require(len(identities) == len(set(identities)),
             "Duplicate canonical identities")
    registry = inputs["registry"]
    _require(isinstance(registry, dict), "Invalid registry")
    kinds = {"adoption", "output", "presentation", "source", "verification"}
    for identifier, record in registry.items():
        _require(_text(identifier) and isinstance(record, dict),
                 "Invalid registry entry")
        _require(record.get("id") == identifier, "Registry ID mismatch")
        _require(record.get("kind") in kinds, "Invalid registry kind")
    adoption = registry.get(inputs["adoption_id"])
    _require(isinstance(adoption, dict) and
             adoption["kind"] == "adoption", "Invalid adoption root")
    binding = adoption.get("output_binding")
    _validate_binding(binding)
    output = registry.get(binding["output_id"])
    _require(isinstance(output, dict) and
             output["kind"] == "output", "Invalid output root")
    for record in registry.values():
        _validate_record(record)

def _validate_content(content):
    _require(isinstance(content, list), "Content must be an array")
    identifiers = []
    for portion in content:
        _require(isinstance(portion, list) and len(portion) == 2,
                 "Invalid portion pair")
        _require(_text(portion[0]) and isinstance(portion[1], str),
                 "Invalid portion ID or text")
        identifiers.append(portion[0])
    _require(len(identifiers) == len(set(identifiers)),
             "Duplicate portion IDs")

def _validate_version(version):
    _require(type(version) is int or _text(version),
             "Invalid version identity")

def _validate_binding(binding):
    _require(isinstance(binding, dict), "Invalid output binding")
    _require(_text(binding.get("output_id")), "Invalid bound output ID")
    _validate_version(binding.get("output_version"))
    _validate_content(binding.get("content"))

def _validate_text_fields(record, fields):
    for field in fields:
        _require(_text(record.get(field)), f"Invalid field: {field}")

def _validate_portion_ids(value):
    _require(isinstance(value, list) and all(_text(item) for item in value),
             "Invalid portion ID array")
    _require(len(value) == len(set(value)), "Duplicate portion references")

def _validate_record(record):
    kind = record["kind"]
    if kind == "adoption":
        _validate_text_fields(record, ("decision_maker", "decision_context"))
        _validate_binding(record.get("output_binding"))
        _validate_portion_ids(record.get("adopted_portions"))
        reference = record.get("presentation_ref")
        _require(reference is None or _text(reference),
                 "Invalid presentation reference")
    elif kind == "presentation":
        _validate_text_fields(
            record, ("recorder", "recipient", "decision_context")
        )
        _validate_binding(record.get("output_binding"))
        _validate_portion_ids(record.get("presented_portions"))
    elif kind == "output":
        _validate_text_fields(record, ("producer",))
        _validate_version(record.get("version"))
        _validate_content(record.get("content"))
        citations = record.get("citations")
        _require(isinstance(citations, list), "Invalid citations")
        portions = []
        for citation in citations:
            _require(isinstance(citation, dict), "Invalid citation")
            _validate_text_fields(citation, ("portion_id", "source_id"))
            _validate_version(citation.get("source_version"))
            _require(isinstance(citation.get("source_content"), str),
                     "Invalid cited source content")
            reference = citation.get("verification_ref")
            _require(reference is None or _text(reference),
                     "Invalid verification reference")
            portions.append(citation["portion_id"])
        _require(len(portions) == len(set(portions)),
                 "Duplicate citation for portion")
    elif kind == "source":
        _validate_version(record.get("version"))
        _require(isinstance(record.get("content"), str),
                 "Invalid source content")
    elif kind == "verification":
        _validate_text_fields(record, ("recorder", "portion_id", "source_id"))
        _validate_binding(record.get("output_binding"))
        _validate_version(record.get("source_version"))
        _require(isinstance(record.get("portion_text"), str),
                 "Invalid verified portion text")
        _require(isinstance(record.get("source_content"), str),
                 "Invalid verified source content")

def _raise_failure(stage, code, record, cause, failure_sink):
    failure_record = copy.deepcopy(record)
    failure_record.update({
        "stage": stage,
        "code": code,
        "cause_type": type(cause).__name__,
        "cause_message": str(cause),
    })
    error = ExternalValidationError(stage, code, failure_record)
    try:
        failure_sink(failure_record)
    except Exception as persistence_error:
        error.persistence_error = persistence_error
    raise error from cause

def run_external_validation(*, source_snapshot, manifest,
                            adapter, checker, failure_sink):
    record = {
        "manifest_revision": (
            manifest.get("manifest_revision") if isinstance(manifest, dict)
            else None
        ),
        "source_snapshot_id": (
            source_snapshot.get("snapshot_id")
            if isinstance(source_snapshot, dict) else None
        ),
        "findings": [],
        "checker_invoked": False,
        "checker_result": None,
    }
    try:
        snapshot_copy = copy.deepcopy(source_snapshot)
        manifest_copy = copy.deepcopy(manifest)
        evidence = _validate_manifest(snapshot_copy, manifest_copy)
    except Exception as cause:
        _raise_failure("manifest_validation", "MANIFEST_INVALID",
                       record, cause, failure_sink)
    try:
        findings, blocked = _preflight(
            snapshot_copy, manifest_copy, evidence
        )
        record["findings"] = findings
    except Exception as cause:
        _raise_failure("adaptation", "ADAPTER_EXECUTION_ERROR",
                       record, cause, failure_sink)
    if blocked:
        return record
    try:
        adapted = adapter(
            copy.deepcopy(snapshot_copy), copy.deepcopy(manifest_copy)
        )
    except Exception as cause:
        _raise_failure("adaptation", "ADAPTER_EXECUTION_ERROR",
                       record, cause, failure_sink)
    try:
        _validate_input(adapted)
    except Exception as cause:
        _raise_failure("input_validation", "ADAPTED_INPUT_INVALID",
                       record, cause, failure_sink)
    record["checker_invoked"] = True
    try:
        record["checker_result"] = checker(**copy.deepcopy(adapted))
    except Exception as cause:
        _raise_failure("checker_execution", "CHECKER_EXECUTION_ERROR",
                       record, cause, failure_sink)
    return record
