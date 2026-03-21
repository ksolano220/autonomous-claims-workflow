def run_intake_agent(claim: dict) -> dict:
    issues = []
    actions = []

    if not claim.get("first_name") or not claim.get("last_name"):
        issues.append("MISSING_IDENTITY")
    if not claim.get("employer_name"):
        issues.append("MISSING_EMPLOYER")
    if not claim.get("last_day_of_employment"):
        issues.append("MISSING_EMPLOYMENT_DATE")

    proof = claim.get("documents", {}).get("proof_of_termination")
    if not proof:
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

    return {
        "agent": "intake_agent",
        "claim_id": claim.get("claim_id"),
        "issues_detected": issues,
        "proposed_actions": actions,
        "status": "processed"
    }
