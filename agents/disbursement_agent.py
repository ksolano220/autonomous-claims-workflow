def run_disbursement_agent(claim: dict) -> dict:
    eligibility = claim.get("eligibility_analysis", {})
    decision = eligibility.get("decision")
    applicant_name = f"{claim.get('first_name', '')} {claim.get('last_name', '')}".strip()
    applicant_email = claim.get("email", "applicant@example.com")

    if decision == "APPROVE":
        tool_call = {
            "tool_name": "send_email_notification",
            "arguments": {
                "to_email": applicant_email,
                "subject": "Your Emergency Relief Claim Has Been Approved",
                "message_type": "APPROVAL",
                "body": f"Hello {applicant_name},\n\nYour emergency unemployment relief claim has been approved for a $5,000 relief package.\n\nTo complete processing, please reply with your mailing address and payment instructions.\n\nSincerely,\nRelief Claims Team"
            }
        }
        rationale = ["Eligibility agent approved claim"]
    elif decision == "DENY":
        tool_call = {
            "tool_name": "send_email_notification",
            "arguments": {
                "to_email": applicant_email,
                "subject": "Update on Your Emergency Relief Claim",
                "message_type": "REJECTION",
                "body": f"Hello {applicant_name},\n\nWe reviewed your emergency unemployment relief claim and are unable to approve it based on the information submitted.\n\nIf you believe this was submitted in error, please contact support for next steps.\n\nSincerely,\nRelief Claims Team"
            }
        }
        rationale = ["Eligibility agent denied claim"]
    else:
        tool_call = {
            "tool_name": "send_email_notification",
            "arguments": {
                "to_email": applicant_email,
                "subject": "Your Emergency Relief Claim Is Under Review",
                "message_type": "REVIEW",
                "body": f"Hello {applicant_name},\n\nYour claim is currently under review. We may need additional information before a final decision can be made.\n\nSincerely,\nRelief Claims Team"
            }
        }
        rationale = ["Eligibility decision requires follow-up"]

    return {
        "agent": "communications_agent",
        "claim_id": claim.get("claim_id"),
        "proposed_tool_call": tool_call,
        "rationale": rationale,
        "status": "ready_for_tool_execution"
    }
