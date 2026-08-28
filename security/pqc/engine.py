"""
PHAGE PQC Engine

Production note:
Real ML-KEM and ML-DSA implementations require:
  pip install pqcrypto    (liboqs Python bindings)
  pip install pyoqs       (Open Quantum Safe)

This engine provides:
1. Real SHA3-256/SHA3-512 hashing (NIST standard)
2. Real HMAC-SHA3 for integrity verification
3. Simulated ML-KEM key exchange (structure-correct)
4. Simulated ML-DSA signatures (structure-correct)
5. Full PQC handshake protocol
6. Action signing and verification
7. PUF hardware binding simulation

In production: replace _simulate_* methods with liboqs calls.
The API surface is identical — swap the implementation, not the interface.
"""

import hashlib
import hmac
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from .schemas import (
    AgentIdentityClaim, PQCHandshake, ActionSignature,
    PQCSessionToken, PQCAlgorithm, HardwareOrigin
)


class PQCEngine:
    """
    PHAGE Post-Quantum Cryptographic Engine.
    Implements the identity handshake protocol for agent authentication.
    """

    def __init__(self, phage_secret: str):
        self.phage_secret = phage_secret
        self._key_store: Dict[str, Dict] = {}
        self._session_store: Dict[str, PQCSessionToken] = {}

    # ── KEY GENERATION ──

    def generate_agent_keypair(
        self,
        agent_id: str,
        kem_algorithm: PQCAlgorithm = PQCAlgorithm.ML_KEM_768,
        dsa_algorithm: PQCAlgorithm = PQCAlgorithm.ML_DSA_65,
    ) -> Dict[str, str]:
        """
        Generate ML-KEM and ML-DSA keypairs for an agent.

        Production: replace with liboqs key generation
        oqs.KeyEncapsulation(kem_algorithm).generate_keypair()
        oqs.Signature(dsa_algorithm).generate_keypair()
        """
        # Simulated keypair generation — structure correct
        # In production: call liboqs here
        kem_seed = secrets.token_bytes(32)
        dsa_seed = secrets.token_bytes(32)

        # Derive public/private keys via SHA3 (simulated)
        kem_private = hashlib.sha3_256(kem_seed + b":kem:private").digest()
        kem_public = hashlib.sha3_256(kem_seed + b":kem:public").digest()
        dsa_private = hashlib.sha3_512(dsa_seed + b":dsa:private").digest()
        dsa_public = hashlib.sha3_512(dsa_seed + b":dsa:public").digest()

        # Key fingerprint = SHA3-256(kem_public || dsa_public)
        fingerprint = hashlib.sha3_256(kem_public + dsa_public).hexdigest()

        keypair = {
            "agent_id": agent_id,
            "kem_algorithm": kem_algorithm,
            "dsa_algorithm": dsa_algorithm,
            "kem_private_key": base64.b64encode(kem_private).decode(),
            "kem_public_key": base64.b64encode(kem_public).decode(),
            "dsa_private_key": base64.b64encode(dsa_private).decode(),
            "dsa_public_key": base64.b64encode(dsa_public).decode(),
            "key_fingerprint": fingerprint,
            "generated_at": datetime.utcnow().isoformat(),
        }

        self._key_store[agent_id] = keypair
        return keypair
          # ── PQC HANDSHAKE ──

    def initiate_handshake(self, agent_id: str) -> Tuple[str, str]:
        """
        PHAGE issues a challenge to the agent.
        Returns: (challenge, challenge_signature)
        """
        challenge = secrets.token_hex(32)
        # PHAGE signs the challenge with its own key
        challenge_sig = hmac.new(
            self.phage_secret.encode(),
            challenge.encode(),
            "sha3_256"
        ).hexdigest()
        return challenge, challenge_sig

    def complete_handshake(
        self,
        identity: AgentIdentityClaim,
        challenge: str,
        agent_response: str,
    ) -> PQCHandshake:
        """
        Verify the agent's response to the challenge.
        Establishes a quantum-safe shared secret.

        Production: use ML-KEM encapsulation/decapsulation
        kem = oqs.KeyEncapsulation(identity.kem_algorithm)
        ciphertext, shared_secret = kem.encap_secret(public_key)
        """
        # Retrieve agent's key material
        keypair = self._key_store.get(identity.agent_id)

        if not keypair:
            return PQCHandshake(
                agent_id=identity.agent_id,
                principal_id=identity.principal_id,
                kem_algorithm=identity.kem_algorithm,
                dsa_algorithm=identity.dsa_algorithm,
                challenge=challenge,
                response=agent_response,
                shared_secret_hash="",
                verified=False,
                failure_reason="No key material found for agent"
            )

        # Verify the agent's signed response
        # Agent should have signed: SHA3-256(challenge + agent_id)
        expected_response = hashlib.sha3_256(
            f"{challenge}:{identity.agent_id}".encode()
        ).hexdigest()

        # In production: verify ML-DSA signature
        # sig = oqs.Signature(dsa_algorithm)
        # verified = sig.verify(message, signature, public_key)
        verified = hmac.compare_digest(
            agent_response[:64],
            expected_response[:64]
        )

        # Establish shared secret via simulated KEM
        # Production: ML-KEM encapsulation
        shared_secret = hashlib.sha3_256(
            f"{challenge}:{identity.agent_id}:{self.phage_secret}".encode()
        ).digest()
        shared_secret_hash = hashlib.sha3_256(shared_secret).hexdigest()

        handshake = PQCHandshake(
            agent_id=identity.agent_id,
            principal_id=identity.principal_id,
            kem_algorithm=identity.kem_algorithm,
            dsa_algorithm=identity.dsa_algorithm,
            challenge=challenge,
            response=agent_response,
            shared_secret_hash=shared_secret_hash,
            verified=verified,
            failure_reason=None if verified else "Signature verification failed",
            session_expires_at=datetime.utcnow() + timedelta(hours=8),
        )

        if verified:
            # Issue session token
            self._issue_session_token(identity, handshake, shared_secret)

        return handshake
          def _issue_session_token(
        self,
        identity: AgentIdentityClaim,
        handshake: PQCHandshake,
        shared_secret: bytes,
    ) -> PQCSessionToken:
        """Issue a session token after successful handshake."""
        token_plaintext = secrets.token_bytes(32)
        token_hash = hashlib.sha3_256(
            token_plaintext + shared_secret
        ).hexdigest()

        token = PQCSessionToken(
            agent_id=identity.agent_id,
            principal_id=identity.principal_id,
            handshake_id=handshake.handshake_id,
            token_hash=token_hash,
            algorithm=identity.kem_algorithm,
            authorized_actions=identity.authorized_actions,
            autonomy_level=identity.max_autonomy_level,
            expires_at=handshake.session_expires_at,
        )
        self._session_store[identity.agent_id] = token
        return token

    # ── ACTION SIGNING ──

    def sign_action(
        self,
        agent_id: str,
        principal_id: str,
        session_id: str,
        action: str,
        resource: str,
        payload: Dict[str, Any],
    ) -> ActionSignature:
        """
        Sign an agent action with ML-DSA.
        Creates non-repudiable proof the agent took this action.

        Production: replace with liboqs ML-DSA signing
        signer = oqs.Signature(ML_DSA_65)
        signature = signer.sign(message, private_key)
        """
        keypair = self._key_store.get(agent_id)
        if not keypair:
            raise ValueError(f"No key material for agent {agent_id}")

        # Payload hash
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha3_256(payload_str.encode()).hexdigest()

        # Message to sign = action + resource + payload_hash + timestamp
        timestamp = datetime.utcnow()
        message = f"{agent_id}:{action}:{resource}:{payload_hash}:{timestamp.isoformat()}"

        # Simulated ML-DSA signature
        # Production: oqs.Signature(ML_DSA_65).sign(message.encode(), private_key)
        dsa_private = base64.b64decode(keypair["dsa_private_key"])
        signature_bytes = hmac.new(
            dsa_private,
            message.encode(),
            "sha3_512"
        ).digest()
        signature_b64 = base64.b64encode(signature_bytes).decode()

        return ActionSignature(
            agent_id=agent_id,
            principal_id=principal_id,
            session_id=session_id,
            action=action,
            resource=resource,
            payload_hash=payload_hash,
            timestamp=timestamp,
            algorithm=PQCAlgorithm.ML_DSA_65,
            signature=signature_b64,
            signing_key_fingerprint=keypair["key_fingerprint"],
            verified=False,
        )

    def verify_action_signature(self, sig: ActionSignature) -> bool:
        """
        Verify an action signature.
        Production: oqs.Signature(ML_DSA_65).verify(message, signature, public_key)
        """
        keypair = self._key_store.get(sig.agent_id)
        if not keypair:
            return False

        message = f"{sig.agent_id}:{sig.action}:{sig.resource}:{sig.payload_hash}:{sig.timestamp.isoformat()}"
        dsa_private = base64.b64decode(keypair["dsa_private_key"])

        expected_bytes = hmac.new(
            dsa_private,
            message.encode(),
            "sha3_512"
        ).digest()
        expected_b64 = base64.b64encode(expected_bytes).decode()

        verified = hmac.compare_digest(sig.signature, expected_b64)
        if verified:
            sig.verified = True
            sig.verified_at = datetime.utcnow()
        return verified
          # ── HARDWARE BINDING (PUF simulation) ──

    def bind_hardware_identity(
        self,
        agent_id: str,
        hardware_id: str,
        hardware_type: HardwareOrigin = HardwareOrigin.EDGE_DEVICE,
    ) -> str:
        """
        Bind agent identity to physical hardware.
        In production: PUF challenge-response proves physical presence.

        PUF (Physically Unclonable Function):
        - Every chip has unique manufacturing variations
        - These produce a unique, unclonable fingerprint
        - Cannot be extracted or cloned — physically bound

        Moxa industrial edge devices with PUF support:
        - Agent running on Moxa X hardware gets hardware-bound identity
        - Identity cannot be transferred to another device
        - Even if firmware is compromised, identity cannot be replicated
        """
        # Simulated PUF response
        # Production: query hardware PUF via manufacturer API
        puf_challenge = hashlib.sha3_256(
            f"{hardware_id}:puf:challenge".encode()
        ).hexdigest()

        # PUF response is deterministic for same hardware, unique per device
        puf_response = hashlib.sha3_256(
            f"{hardware_id}:{puf_challenge}:{self.phage_secret}".encode()
        ).hexdigest()

        # Hardware fingerprint binds agent to device
        hardware_fingerprint = hashlib.sha3_256(
            f"{agent_id}:{hardware_id}:{puf_response}".encode()
        ).hexdigest()

        # Update key store with hardware binding
        if agent_id in self._key_store:
            self._key_store[agent_id]["hardware_id"] = hardware_id
            self._key_store[agent_id]["hardware_type"] = hardware_type
            self._key_store[agent_id]["hardware_fingerprint"] = hardware_fingerprint
            self._key_store[agent_id]["puf_response_hash"] = hashlib.sha3_256(
                puf_response.encode()
            ).hexdigest()

        return hardware_fingerprint

    def verify_hardware_binding(self, agent_id: str, hardware_id: str) -> bool:
        """Verify an agent is running on its registered hardware."""
        keypair = self._key_store.get(agent_id)
        if not keypair:
            return False
        if "hardware_id" not in keypair:
            return False
        return hmac.compare_digest(
            keypair.get("hardware_id", ""),
            hardware_id
        )
          # ── SESSION VALIDATION ──

    def validate_session(
        self,
        agent_id: str,
        action: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate an active PQC session and optionally check action scope.
        """
        token = self._session_store.get(agent_id)

        if not token:
            return False, "No active session"

        if not token.is_active:
            return False, "Session inactive"

        if token.expires_at and datetime.utcnow() > token.expires_at:
            token.is_active = False
            return False, "Session expired"

        if token.max_uses is not None and token.use_count >= token.max_uses:
            token.is_active = False
            return False, "Session use limit exceeded"

        if action and action not in token.authorized_actions:
            return False, f"Action '{action}' not authorized in session"

        token.use_count += 1
        return True, "Session valid"

    # ── AGENT CHALLENGE RESPONSE ──

    @staticmethod
    def create_agent_response(challenge: str, agent_id: str) -> str:
        """
        Helper for agent-side challenge response.

        In production the agent signs the challenge with ML-DSA.
        Current prototype derives a deterministic SHA3 response.
        """
        return hashlib.sha3_256(
            f"{challenge}:{agent_id}".encode()
        ).hexdigest()
