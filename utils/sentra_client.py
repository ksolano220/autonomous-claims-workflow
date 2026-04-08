"""
Sentra integration for the claims workflow.

Uses the Sentra SDK — same client any developer would use.
"""

import sys
import os

# Add Sentra repo to path if available locally
SENTRA_PATH = os.getenv("SENTRA_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "sentra"))
if os.path.exists(SENTRA_PATH):
    sys.path.insert(0, SENTRA_PATH)

try:
    from sdk.client import Sentra
except ImportError:
    # Fallback: inline minimal client if SDK not available
    import requests
    from dataclasses import dataclass
    from typing import Optional, Dict, Any

    @dataclass
    class SentraResult:
        allowed: bool
        decision: str
        reason: str
        risk_score: int
        raw: Optional[Dict[str, Any]] = None

    class Sentra:
        def __init__(self, url="http://127.0.0.1:8000"):
            self.url = url.rstrip("/")

        def evaluate(self, agent_id, action, context=None, target=None, notification_type=None):
            try:
                resp = requests.post(f"{self.url}/agent-action", json={
                    "agent_id": agent_id, "action_type": action,
                    "target": target or "", "notification_type": notification_type or "",
                    "policy_context": context or {},
                }, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                decision = data.get("decision", "Blocked")
                return SentraResult(decision == "Allowed", decision, data.get("reason", ""), data.get("risk", 0), data)
            except Exception as e:
                return SentraResult(False, "Blocked", f"Sentra error: {e}", 100)


sentra = Sentra()


def evaluate_with_sentra(claim_data: dict, tool_name: str, tool_args: dict) -> dict:
    message_type = tool_args.get("message_type", "UNKNOWN").lower()
    has_proof = bool(claim_data.get("documents", {}).get("proof_of_termination"))

    result = sentra.evaluate(
        agent_id="claims_workflow_agent",
        action="SEND_NOTIFICATION",
        target=tool_args.get("to_email", ""),
        notification_type=message_type,
        context={
            "claim_id": claim_data.get("claim_id"),
            "tool_name": tool_name,
            "message_type": message_type,
            "approval_requires_verified_eligibility": True,
            "eligibility_verified": has_proof,
            "required_documents_present": has_proof,
        },
    )

    return {
        "allowed": result.allowed,
        "reason": result.reason,
        "risk_score": result.risk_score,
        "raw": result.raw,
    }
