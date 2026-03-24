import os
import json
from datetime import datetime
from utils.sentra_client import evaluate_with_sentra

EMAIL_LOG_PATH = "data/email_log.json"


def send_email_notification(
    claim_data: dict,
    to_email: str,
    subject: str,
    message_type: str,
    body: str
) -> dict:
    """
    Sends email only if approved by Sentra.
    Otherwise blocks execution and logs the blocked action.
    """

    evaluation = evaluate_with_sentra(
        claim_data=claim_data,
        tool_name="send_email_notification",
        tool_args={"message_type": message_type}
    )

    if not evaluation["allowed"]:
        blocked_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "to_email": to_email,
            "subject": subject,
            "message_type": message_type,
            "body": body,
            "status": "BLOCKED",
            "reason": evaluation["reason"],
            "risk_score": evaluation["risk_score"]
        }

        _write_log(blocked_record)
        return blocked_record

    email_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "to_email": to_email,
        "subject": subject,
        "message_type": message_type,
        "body": body,
        "status": "SENT"
    }

    _write_log(email_record)
    return email_record


def _write_log(record: dict):
    os.makedirs("data", exist_ok=True)

    existing_logs = []
    if os.path.exists(EMAIL_LOG_PATH):
        with open(EMAIL_LOG_PATH, "r") as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []

    existing_logs.append(record)

    with open(EMAIL_LOG_PATH, "w") as f:
        json.dump(existing_logs, f, indent=2)