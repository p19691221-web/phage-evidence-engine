"""L/M interface-only stub."""

def issue_decision(*, payload, producer_request):
    raise NotImplementedError("L/M behavior not implemented")

def issue_audit_receipt(*, payload, producer_request):
    raise NotImplementedError("L/M behavior not implemented")

def verify_decision_origin(candidate):
    raise NotImplementedError("L/M behavior not implemented")

def verify_audit_receipt_origin(candidate):
    raise NotImplementedError("L/M behavior not implemented")

def consume_decision(*, candidate, on_verified):
    raise NotImplementedError("L/M behavior not implemented")

def consume_audit_receipt(*, candidate, on_verified):
    raise NotImplementedError("L/M behavior not implemented")

def _issuance_provenance_for_test(artifact):
    raise NotImplementedError("L/M behavior not implemented")

def _issuance_matches_evidence_for_test(artifact, candidate):
    raise NotImplementedError("L/M behavior not implemented")

def _tamper_decision_for_test(artifact, *, payload):
    raise NotImplementedError("L/M behavior not implemented")

def _tamper_audit_receipt_for_test(artifact, *, payload):
    raise NotImplementedError("L/M behavior not implemented")
