# HHN schema copy P1 repair

Base: 1098a6ca00d858a92587ba30cf09a28ae6036668.

Request field keys are checked as exact strings before hashing, comparison or lookup; request binding is detached before authentication and provider acquisition. Provider fixed-record keys receive the same check before any lookup. All present schema values are checked as exact builtins before decision use. No deepcopy remains; snapshot and verifier arguments are rebuilt through finite schema slots. Original error codes and malformed-over-missing priority remain unchanged.

The frozen interface has no recursive type definition: request strings; snapshot scalars, policy scalar fields, grant records with scalar scope lists, and root anchors with scalar fields. Malformed deep nesting, cycles and shared nested lists are rejected at a scalar/schema slot without recursive descent or expansion. Valid lists remain exact lists; tuples remain rejected where lists are required by the frozen interface.

Validation: 72 existing tests, 24 prior independent probes, surviving copy-hook reproduction, and 16 new regression probes passed. New hook sentinels are reset after fixture construction and asserted zero outside the resolver.

Boundary: provider execution while producing the snapshot, concurrent mutation, atomic protected use and ABA detection are not established by this repair. They require a separately reviewed consistency contract. No source-specific public error code or telemetry callback is added.

Future resource contract: request and snapshot need separate budgets, counting actual reconstruction visits rather than unique objects. Finite depth does not bound variable-width data. This schema does not recursively expand shared structures, but large valid grant/scope lists can still exhaust memory. Caught MemoryError in snapshot reconstruction follows existing AUTHORITY_VERIFICATION_ERROR; this is not an operating-system OOM containment guarantee. Limits, rejection semantics, and version/lease enforcement including changed-then-restored state require separate review.
