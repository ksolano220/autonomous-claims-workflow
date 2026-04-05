"""
Intake agent — uses IBM Granite to analyze raw claim data,
detect missing documents, and flag inconsistencies.
"""

import json
from utils.watsonx_client import chat

SYSTEM_PROMPT = """You are an intake validation agent for a government emergency unemployment relief program.

Your job is to analyze a claim submission and identify any issues before it moves to eligibility review.

Check for:
- MISSING_IDENTITY: first_name or last_name is empty
- MISSING_EMPLOYER: employer_name is empty
- MISSING_EMPLOYMENT_DATE: last_day_of_employment is empty
- MISSING_TERMINATION_PROOF: documents.proof_of_termination is null or empty
- NOT_DISASTER_LAYOFF: laid_off_due_to_disaster is "No"
- EMPLOYMENT_CONFLICT: currently_employed_elsewhere is "Yes"

For each issue found, propose an action:
- MISSING_TERMINATION_PROOF → REQUEST_DOCUMENT
- NOT_DISASTER_LAYOFF or EMPLOYMENT_CONFLICT → FLAG_FOR_REVIEW
- No issues → PROCEED_TO_ELIGIBILITY

Respond ONLY with valid JSON in this exact format:
{"issues_detected": [...], "proposed_actions": [...], "summary": "brief explanation"}"""


def run_intake_agent(claim: dict) -> dict:
    claim_summary = {
        "claim_id": claim.get("claim_id"),
        "first_name": claim.get("first_name"),
        "last_name": claim.get("last_name"),
        "employer_name": claim.get("employer_name"),
        "last_day_of_employment": claim.get("last_day_of_employment"),
        "laid_off_due_to_disaster": claim.get("laid_off_due_to_disaster"),
        "currently_employed_elsewhere": claim.get("currently_employed_elsewhere"),
        "documents": claim.get("documents", {}),
    }

    user_msg = f"Analyze this claim submission:\n{json.dumps(claim_summary, indent=2, default=str)}"

    try:
        response = chat(SYSTEM_PROMPT, user_msg, max_tokens=512)
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
        else:
            result = {"issues_detected": [], "proposed_actions": [], "summary": response}
    except Exception as e:
        result = _fallback_analysis(claim)
        result["summary"] = f"Granite unavailable, used fallback: {e}"

    return {
        "agent": "intake_agent",
        "model": "ibm/granite-3-8b-instruct",
        "claim_id": claim.get("claim_id"),
        "issues_detected": result.get("issues_detected", []),
        "proposed_actions": result.get("proposed_actions", []),
        "summary": result.get("summary", ""),
        "status": "processed",
    }


def _fallback_analysis(claim):
    issues = []
    actions = []

    if not claim.get("first_name") or not claim.get("last_name"):
        issues.append("MISSING_IDENTITY")
    if not claim.get("employer_name"):
        issues.append("MISSING_EMPLOYER")
    if not claim.get("last_day_of_employment"):
        issues.append("MISSING_EMPLOYMENT_DATE")
    if not claim.get("documents", {}).get("proof_of_termination"):
        issues.append("MISSING_TERMINATION_PROOF")
    if claim.get("laid_off_due_to_disaster") == "No":
        issues.append("NOT_DISASTER_LAYOFF")
    if claim.get("currently_employed_elsewhere") == "Yes":
        issues.append("EMPLOYMENT_CONFLICT")

    if "MISSING_TERMINATION_PROOF" in issues:
        actions.append("REQUEST_DOCUMENT")
    if "NOT_DISASTER_LAYOFF" in issues or "EMPLOYMENT_CONFLICT" in issues:
        actions.append("FLAG_FOR_REVIEW")
    if not issues:
        actions.append("PROCEED_TO_ELIGIBILITY")

    return {"issues_detected": issues, "proposed_actions": actions, "summary": "Fallback rule-based analysis"}
