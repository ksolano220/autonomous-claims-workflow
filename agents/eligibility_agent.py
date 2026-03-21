def run_eligibility_agent(claim: dict) -> dict:
    decision = "PENDING"
    reason = []

    if claim.get("laid_off_due_to_disaster") == "No":
        decision = "DENY"
        reason.append("Applicant did not report disaster-related layoff")
    elif claim.get("currently_employed_elsewhere") == "Yes":
        decision = "DENY"
        reason.append("Applicant reported current employment elsewhere")
    else:
        decision = "APPROVE"
        reason.append("Applicant meets self-reported eligibility criteria")

    return {
        "agent": "eligibility_agent",
        "claim_id": claim.get("claim_id"),
        "decision": decision,
        "reason": reason,
        "relief_amount": 5000 if decision == "APPROVE" else 0
    }
