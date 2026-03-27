import os
import json
import streamlit as st
from datetime import date
from agents.intake_agent import run_intake_agent
from agents.eligibility_agent import run_eligibility_agent
from agents.disbursement_agent import run_disbursement_agent
from tools.email_tools import send_email_notification
from utils.sentra_client import evaluate_with_sentra

st.set_page_config(page_title="Natural Disaster Relief Claims Portal", layout="centered")

DATA_PATH = "data/claims.json"
UPLOAD_DIR = "data/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("Natural Disaster Relief Claims Portal")
st.subheader("Apply for Emergency Unemployment Relief")
st.markdown("Eligible applicants may qualify for a **$5,000 emergency relief package**.")

with st.form("claim_form"):
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    employer_name = st.text_input("Employer Name")

    last_day_employment = st.date_input(
        "Last Day of Employment",
        max_value=date.today()
    )

    laid_off_due_to_disaster = st.radio(
        "Were you laid off due to the natural disaster?",
        ["Yes", "No"]
    )

    employed_elsewhere = st.radio(
        "Are you currently employed elsewhere?",
        ["No", "Yes"]
    )

    proof_of_termination = st.file_uploader(
        "Upload Proof (Optional)",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    submitted = st.form_submit_button("Submit Claim")

if submitted:
    if not first_name or not last_name or not employer_name or not email:
        st.error("Please complete all required fields.")
    else:
        claim_id = f"{first_name.strip().lower()}_{last_name.strip().lower()}_{str(last_day_employment)}"

        uploaded_files = {"proof_of_termination": None}

        if proof_of_termination:
            safe_filename = proof_of_termination.name.replace(" ", "_")
            file_path = os.path.join(UPLOAD_DIR, f"{claim_id}_{safe_filename}")
            with open(file_path, "wb") as f:
                f.write(proof_of_termination.read())
            uploaded_files["proof_of_termination"] = file_path

        claim_record = {
            "claim_id": claim_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "employer_name": employer_name,
            "last_day_of_employment": str(last_day_employment),
            "laid_off_due_to_disaster": laid_off_due_to_disaster,
            "currently_employed_elsewhere": employed_elsewhere,
            "relief_package_amount": 5000,
            "documents": uploaded_files,
            "status": "submitted"
        }

        intake_result = run_intake_agent(claim_record)
        claim_record["intake_analysis"] = intake_result

        eligibility_result = run_eligibility_agent(claim_record)
        claim_record["eligibility_analysis"] = eligibility_result

        communications_result = run_disbursement_agent(claim_record)
        claim_record["communications_analysis"] = communications_result

        proposed_tool_call = communications_result.get("proposed_tool_call")
        sentra_result = None
        tool_result = None

        if proposed_tool_call:
            sentra_result = evaluate_with_sentra(
                claim_data=claim_record,
                tool_name=proposed_tool_call.get("tool_name", ""),
                tool_args=proposed_tool_call.get("arguments", {})
            )

            args = proposed_tool_call.get("arguments", {})
            to_email = args.get("to_email", "")
            subject = args.get("subject", "")
            message_type = args.get("message_type", "")
            body = args.get("body", "")

            tool_result = send_email_notification(
                claim_data=claim_record,
                to_email=to_email,
                subject=subject,
                message_type=message_type,
                body=body
            )

        claim_record["sentra_evaluation"] = sentra_result
        claim_record["tool_execution_result"] = tool_result

        existing_claims = []
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "r") as f:
                try:
                    existing_claims = json.load(f)
                except json.JSONDecodeError:
                    existing_claims = []

        existing_claims.append(claim_record)

        with open(DATA_PATH, "w") as f:
            json.dump(existing_claims, f, indent=2)

        st.success("Your claim has been submitted and is being processed.")
        st.info("If additional information is needed, you will be contacted by email.")