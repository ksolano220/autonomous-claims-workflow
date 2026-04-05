"""
Eligibility agent — uses IBM Granite to evaluate whether a claim
qualifies for the $5,000 emergency relief package.

Granite reasons about the claim holistically, considering both
self-reported answers and document completeness.
"""

import json
from utils.watsonx_client import chat

SYSTEM_PROMPT = """You are an eligibility evaluation agent for a government emergency unemployment relief program.

Program rules:
- Applicant must have been laid off due to a declared disaster
- Applicant must NOT be currently employed elsewhere
- Applicant should provide proof of termination (though self-reported data may be accepted provisionally)
- Relief amount is $5,000 if approved

Based on the claim data AND the intake analysis, determine eligibility.

Your decision must be one of:
- APPROVE: Applicant clearly meets all criteria
- DENY: Applicant clearly does not meet criteria
- PENDING: Insufficient information or conflicting data requires human review

Respond ONLY with valid JSON:
{"decision": "APPROVE|DENY|PENDING", "reason": ["explanation1", "explanation2"], "relief_amount": 5000_or_0, "risk_factors": ["any concerns"]}"""


def run_eligibility_agent(claim: dict) -> dict:
    claim_summary = {
        "claim_id": claim.get("claim_id"),
        "laid_off_due_to_disaster": claim.get("laid_off_due_to_disaster"),
        "currently_employed_elsewhere": claim.get("currently_employed_elsewhere"),
        "employer_name": claim.get("employer_name"),
        "last_day_of_employment": claim.get("last_day_of_employment"),
        "proof_of_termination": claim.get("documents", {}).get("proof_of_termination"),
        "intake_issues": claim.get("intake_analysis", {}).get("issues_detected", []),
    }

    user_msg = f"Evaluate this claim for eligibility:\n{json.dumps(claim_summary, indent=2, default=str)}"

    try:
        response = chat(SYSTEM_PROMPT, user_msg, max_tokens=512)
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
        else:
            result = _fallback_decision(claim)
            result["risk_factors"] = [f"Could not parse Granite response: {response[:100]}"]
    except Exception as e:
        result = _fallback_decision(claim)
        result["risk_factors"] = [f"Granite unavailable: {e}"]

    decision = result.get("decision", "PENDING")

    return {
        "agent": "eligibility_agent",
        "model": "ibm/granite-3-8b-instruct",
        "claim_id": claim.get("claim_id"),
        "decision": decision,
        "reason": result.get("reason", []),
        "relief_amount": result.get("relief_amount", 5000 if decision == "APPROVE" else 0),
        "risk_factors": result.get("risk_factors", []),
    }


def _fallback_decision(claim):
    if claim.get("laid_off_due_to_disaster") == "No":
        return {"decision": "DENY", "reason": ["Not disaster-related"], "relief_amount": 0, "risk_factors": []}
    if claim.get("currently_employed_elsewhere") == "Yes":
        return {"decision": "DENY", "reason": ["Currently employed"], "relief_amount": 0, "risk_factors": []}
    return {"decision": "APPROVE", "reason": ["Self-reported criteria met"], "relief_amount": 5000, "risk_factors": ["No Granite verification"]}
