"""
Client for the Sentra runtime control layer.

Translates claims workflow actions into Sentra's AgentAction format
and calls the /agent-action endpoint for policy evaluation.
"""

import requests

SENTRA_URL = "http://127.0.0.1:8000"


def evaluate_with_sentra(claim_data: dict, tool_name: str, tool_args: dict) -> dict:
    message_type = tool_args.get("message_type", "UNKNOWN").lower()
    has_proof = bool(claim_data.get("documents", {}).get("proof_of_termination"))

    payload = {
        "agent_id": "claims_workflow_agent",
        "action_type": "SEND_NOTIFICATION",
        "target": tool_args.get("to_email", "unknown"),
        "notification_type": message_type,
        "policy_context": {
            "claim_id": claim_data.get("claim_id"),
            "tool_name": tool_name,
            "message_type": message_type,
            "approval_requires_verified_eligibility": True,
            "eligibility_verified": has_proof,
            "required_documents_present": has_proof,
        },
    }

    try:
        response = requests.post(f"{SENTRA_URL}/agent-action", json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        decision = result.get("decision", "Blocked")

        return {
            "allowed": decision == "Allowed",
            "reason": result.get("reason", "Unknown Sentra response"),
            "risk_score": result.get("risk", 0),
            "raw": result,
        }

    except Exception as e:
        return {
            "allowed": False,
            "reason": f"Sentra error: {str(e)}",
            "risk_score": 100,
            "raw": None,
        }
