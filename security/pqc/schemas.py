"""
PHAGE v6 — Post-Quantum Cryptographic Identity Layer

NIST PQC Standards implemented:
- ML-KEM (CRYSTALS-Kyber) — Key Encapsulation Mechanism (FIPS 203)
- ML-DSA (CRYSTALS-Dilithium) — Digital Signature Algorithm (FIPS 204)

Every agent identity is cryptographically bound to:
1. Origin    — hardware ID (PUF-based for industrial deployments)
2. Authority — scope of allowed autonomous actions
3. Policy    — pre-defined governance constraints

This makes agent identity:
- Non-repudiable: agent cannot deny its actions
- Quantum-safe: resistant to Shor's algorithm attacks
- Verifiable: every action signed, every signature checkable
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid
import hashlib
import hmac
import base64
import json


class PQCAlgorithm(str, Enum):
    ML_KEM_512  = "ML-KEM-512"    # FIPS 203 — lightweight
    ML_KEM_768  = "ML-KEM-768"    # FIPS 203 — balanced (recommended)
    ML_KEM_1024 = "ML-KEM-1024"   # FIPS 203 — maximum security
    ML_DSA_44   = "ML-DSA-44"     # FIPS 204 — lightweight
    ML_DSA_65   = "ML-DSA-65"     # FIPS 204 — balanced (recommended)
    ML_DSA_87   = "ML-DSA-87"     # FIPS 204 — maximum security


class HardwareOrigin(str, Enum):
    SOFTWARE   = "software"        # Standard software agent
    EDGE_DEVICE = "edge_device"    # Industrial edge (Moxa, etc.)
    SECURE_ENCLAVE = "secure_enclave"  # TEE/HSM-backed
    PUF_BOUND  = "puf_bound"       # Physically Unclonable Function
class AgentIdentityClaim(BaseModel):
    """
    Cryptographically bound agent identity.
    Not just a username/password — a verifiable attribute set.
    """

    # Core identity
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    principal_id: str
    name: str

    # Origin binding
    hardware_origin: HardwareOrigin = HardwareOrigin.SOFTWARE
    hardware_id: Optional[str] = None
    hardware_fingerprint: Optional[str] = None

    # Authority scope
    authorized_actions: List[str] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)
    max_autonomy_level: int = Field(default=1, ge=0, le=5)
    # 0=fully supervised, 1=low autonomy, 3=standard, 5=fully autonomous

    # Governance policy binding
    policy_ids: List[str] = Field(default_factory=list)
    governance_constraints: Dict[str, Any] = Field(default_factory=dict)

    # PQC key material
    kem_algorithm: PQCAlgorithm = PQCAlgorithm.ML_KEM_768
    dsa_algorithm: PQCAlgorithm = PQCAlgorithm.ML_DSA_65
    public_key_kem: Optional[str] = None
    public_key_dsa: Optional[str] = None
    key_fingerprint: Optional[str] = None

    # Lifecycle
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True

    # Attestation
    issuer_id: str = "phage-identity-service"
    attestation_signature: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
    class PQCHandshake(BaseModel):
    """
    Result of a PQC identity handshake between PHAGE and an agent.
    Non-repudiable proof that the agent was authenticated.
    """

    handshake_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    principal_id: str

    # Handshake parameters
    kem_algorithm: PQCAlgorithm
    dsa_algorithm: PQCAlgorithm
    challenge: str
    response: str
    shared_secret_hash: str

    # Verification result
    verified: bool
    verification_timestamp: datetime = Field(default_factory=datetime.utcnow)
    failure_reason: Optional[str] = None

    # Session binding
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_expires_at: Optional[datetime] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
    class ActionSignature(BaseModel):
    """
    Every agent action is signed with ML-DSA.
    Non-repudiation: the agent cannot deny having taken this action.
    """

    signature_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    principal_id: str
    session_id: str

    # What was signed
    action: str
    resource: str
    payload_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # The signature
    algorithm: PQCAlgorithm = PQCAlgorithm.ML_DSA_65
    signature: str
    signing_key_fingerprint: str

    # Verification
    verified: bool = False
    verified_at: Optional[datetime] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
    class PQCSessionToken(BaseModel):
    """
    Session token established after successful PQC handshake.
    Used for all subsequent action authorizations in the session.
    """

    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    principal_id: str
    handshake_id: str

    # Token material (quantum-safe)
    token_hash: str
    algorithm: PQCAlgorithm = PQCAlgorithm.ML_KEM_768

    # Scope
    authorized_actions: List[str] = Field(default_factory=list)
    autonomy_level: int = 1

    # Lifecycle
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    use_count: int = 0
    max_uses: Optional[int] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
