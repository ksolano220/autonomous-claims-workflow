"""
Disbursement/communications agent — uses IBM Granite to generate
personalized email content based on the eligibility decision.

Proposes a tool call that Sentra will evaluate before execution.
"""

import json
from utils.watsonx_client import chat

SYSTEM_PROMPT = """You are a communications agent for a government emergency unemployment relief program.

Based on the eligibility decision, draft an email to the applicant. The email should be:
- Professional and empathetic
- Clear about the decision and next steps
- Personalized with the applicant's name

For APPROVE: congratulate them, state the $5,000 amount, ask for payment details
For DENY: explain the denial respectfully, suggest contacting support if they disagree
For PENDING: explain the review is ongoing, mention they may need to provide more info

Respond ONLY with valid JSON:
{"subject": "email subject", "message_type": "APPROVAL|REJECTION|REVIEW", "body": "full email body"}"""


def run_disbursement_agent(claim: dict) -> dict:
    eligibility = claim.get("eligibility_analysis", {})
    decision = eligibility.get("decision", "PENDING")
    applicant_name = f"{claim.get('first_name', '')} {claim.get('last_name', '')}".strip()
    applicant_email = claim.get("email", "applicant@example.com")

    user_msg = (
        f"Decision: {decision}\n"
        f"Applicant: {applicant_name}\n"
        f"Email: {applicant_email}\n"
        f"Relief amount: {eligibility.get('relief_amount', 0)}\n"
        f"Reason: {json.dumps(eligibility.get('reason', []))}\n"
        f"Risk factors: {json.dumps(eligibility.get('risk_factors', []))}"
    )

    try:
        response = chat(SYSTEM_PROMPT, user_msg, max_tokens=512)
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            email = json.loads(response[start:end])
        else:
            email = _fallback_email(decision, applicant_name)
    except Exception:
        email = _fallback_email(decision, applicant_name)

    tool_call = {
        "tool_name": "send_email_notification",
        "arguments": {
            "to_email": applicant_email,
            "subject": email.get("subject", "Update on Your Relief Claim"),
            "message_type": email.get("message_type", "REVIEW"),
            "body": email.get("body", ""),
        },
    }

    rationale = []
    if decision == "APPROVE":
        rationale.append("Eligibility agent approved claim — drafting approval notification")
    elif decision == "DENY":
        rationale.append("Eligibility agent denied claim — drafting denial notification")
    else:
        rationale.append("Eligibility decision pending — drafting review notification")

    return {
        "agent": "communications_agent",
        "model": "ibm/granite-3-8b-instruct",
        "claim_id": claim.get("claim_id"),
        "proposed_tool_call": tool_call,
        "rationale": rationale,
        "status": "ready_for_tool_execution",
    }


def _fallback_email(decision, name):
    if decision == "APPROVE":
        return {
            "subject": "Your Emergency Relief Claim Has Been Approved",
            "message_type": "APPROVAL",
            "body": f"Hello {name},\n\nYour claim has been approved for $5,000.\n\nSincerely,\nRelief Claims Team",
        }
    elif decision == "DENY":
        return {
            "subject": "Update on Your Emergency Relief Claim",
            "message_type": "REJECTION",
            "body": f"Hello {name},\n\nWe were unable to approve your claim.\n\nSincerely,\nRelief Claims Team",
        }
    return {
        "subject": "Your Emergency Relief Claim Is Under Review",
        "message_type": "REVIEW",
        "body": f"Hello {name},\n\nYour claim is under review.\n\nSincerely,\nRelief Claims Team",
    }
