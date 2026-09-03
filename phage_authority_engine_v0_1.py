from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import FrozenSet, Optional


class AuthorityStatus(str, Enum):
    CLEAN = "CLEAN"
    AUTHORITY_UNRESOLVED = "AUTHORITY_UNRESOLVED"
    AUTHORITY_SCOPE_VIOLATION = "AUTHORITY_SCOPE_VIOLATION"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"
    AUTHORITY_EXPIRED = "AUTHORITY_EXPIRED"


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    subject_id: str
    issuer_id: Optional[str]
    authorized_actions: FrozenSet[str]
    authorized_targets: FrozenSet[str]
    issued_at: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime]
    source_ref: Optional[str]


@dataclass(frozen=True)
class AuthorityResult:
    status: AuthorityStatus


class AuthorityValidator:
    def check(
        self,
        *,
        grant: Optional[AuthorityGrant],
        subject_id: str,
        action: str,
        target: str,
        at: datetime,
    ) -> AuthorityResult:
        if grant is None:
            return AuthorityResult(
                status=AuthorityStatus.AUTHORITY_UNRESOLVED
            )

        if not grant.issuer_id or not grant.source_ref:
            return AuthorityResult(
                status=AuthorityStatus.AUTHORITY_UNRESOLVED
            )

        if (
            grant.subject_id != subject_id
            or action not in grant.authorized_actions
            or target not in grant.authorized_targets
        ):
            return AuthorityResult(
                status=AuthorityStatus.AUTHORITY_SCOPE_VIOLATION
            )

        if grant.revoked:
            return AuthorityResult(
                status=AuthorityStatus.AUTHORITY_REVOKED
            )

        if at >= grant.expires_at:
            return AuthorityResult(
                status=AuthorityStatus.AUTHORITY_EXPIRED
            )

        return AuthorityResult(
            status=AuthorityStatus.CLEAN
        )
