import requests

SENTRA_URL = "http://127.0.0.1:8000/evaluate"


def evaluate_with_sentra(claim_data: dict, tool_name: str, tool_args: dict) -> dict:
    payload = {
        "claim": {
            "claim_id": claim_data.get("claim_id", "unknown"),
            "documents": {
                "proof_of_termination": claim_data.get("documents", {}).get("proof_of_termination")
            },
            "currently_employed_elsewhere": claim_data.get("currently_employed_elsewhere", "No")
        },
        "proposed_tool_call": {
            "tool_name": tool_name,
            "arguments": tool_args
        }
    }

    try:
        response = requests.post(SENTRA_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        decision = result.get("result", {}).get("decision", "BLOCK")

        return {
            "allowed": decision == "ALLOW",
            "reason": result.get("result", {}).get("reason", "Unknown Sentra response"),
            "risk_score": result.get("result", {}).get("risk_score", 100),
            "raw": result
        }

    except Exception as e:
        return {
            "allowed": False,
            "reason": f"Sentra error: {str(e)}",
            "risk_score": 100,
            "raw": None
        }