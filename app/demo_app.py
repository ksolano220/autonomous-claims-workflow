"""
Autonomous Claims Workflow: public demo dashboard.

Read-only showcase of three pre-recorded agent runs intended for
Streamlit Community Cloud hosting. No live watsonx.ai calls, no API keys,
no Sentra server required. Every response is canned JSON in
app/demo_scenarios/.

Each scenario walks through the full pipeline: claim intake, intake
agent, eligibility agent, communications agent, proposed tool call,
Sentra runtime evaluation, and final result.

Run locally:  streamlit run app/demo_app.py
"""

import json
from pathlib import Path

import streamlit as st

SCENARIO_DIR = Path(__file__).resolve().parent / "demo_scenarios"
SCENARIO_FILES = {
    "Valid claim": "valid_claim.json",
    "Unsafe approval": "unsafe_approval.json",
    "Authority drift": "authority_drift.json",
}

st.set_page_config(
    page_title="Autonomous Claims Workflow Demo",
    layout="wide",
)


def load_scenario(filename: str) -> dict:
    path = SCENARIO_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def outcome_pill(outcome: str) -> str:
    if outcome == "ALLOW":
        return '<span style="background:#d1fae5;color:#065f46;padding:4px 12px;border-radius:999px;font-weight:600;font-size:14px">ALLOW</span>'
    return '<span style="background:#fee2e2;color:#991b1b;padding:4px 12px;border-radius:999px;font-weight:600;font-size:14px">BLOCK</span>'


def render_claim(claim: dict):
    docs = claim.get("documents", {}) or {}
    proof = docs.get("proof_of_termination")
    proof_display = proof if proof else "(none uploaded)"
    st.markdown(
        f"""
**Applicant:** {claim.get('first_name','')} {claim.get('last_name','')}
**Email:** {claim.get('email','')}
**Employer:** {claim.get('employer_name','')}
**Last day of employment:** {claim.get('last_day_of_employment','')}
**Laid off due to disaster:** {claim.get('laid_off_due_to_disaster','')}
**Currently employed elsewhere:** {claim.get('currently_employed_elsewhere','')}
**Relief amount requested:** ${claim.get('relief_package_amount', 0):,}
**Proof of termination:** {proof_display}
"""
    )


def render_intake(intake: dict):
    issues = intake.get("issues_detected") or []
    actions = intake.get("proposed_actions") or []
    risk = intake.get("risk_level", "")
    notes = intake.get("notes", "")
    st.markdown(f"**Risk level:** {risk}")
    if issues:
        st.markdown("**Issues detected:**")
        for i in issues:
            st.markdown(f"- `{i}`")
    else:
        st.markdown("**Issues detected:** None")
    if actions:
        st.markdown("**Proposed actions:** " + ", ".join(f"`{a}`" for a in actions))
    if notes:
        st.markdown(f"**Notes:** {notes}")


def render_eligibility(elig: dict):
    st.markdown(f"**Decision:** `{elig.get('decision','')}`")
    st.markdown(f"**Relief amount:** ${elig.get('relief_amount', 0):,}")
    risk = elig.get("risk_factors") or []
    if risk:
        st.markdown("**Risk factors:** " + ", ".join(f"`{r}`" for r in risk))
    else:
        st.markdown("**Risk factors:** None")
    st.markdown(f"**Rationale:** {elig.get('rationale','')}")


def render_communications(comm: dict):
    msg_type = comm.get("drafted_message_type", "")
    tool_call = comm.get("proposed_tool_call", {}) or {}
    tool_name = tool_call.get("tool_name", "")
    args = tool_call.get("arguments", {}) or {}

    st.markdown(f"**Drafted message type:** `{msg_type}`")
    st.markdown(f"**Proposed tool call:** `{tool_name}`")

    with st.expander("Tool arguments", expanded=False):
        st.json(args)

    note = comm.get("agent_reasoning_note")
    if note:
        st.warning(note)


def render_sentra(sentra: dict):
    decision = sentra.get("decision", "BLOCK")
    reason = sentra.get("reason", "")
    threat = sentra.get("threat_type")
    policy = sentra.get("policy_triggered", "")
    risk = sentra.get("risk_score", 0)

    cols = st.columns([1, 3])
    with cols[0]:
        st.markdown(outcome_pill(decision), unsafe_allow_html=True)
    with cols[1]:
        if threat:
            st.markdown(f"**Threat type:** `{threat}`")
        st.markdown(f"**Policy triggered:** `{policy}`")
        st.markdown(f"**Risk score applied:** {risk}/100")

    st.markdown(f"**Reason:** {reason}")


def render_result(result: dict, decision: str):
    status = result.get("status", "")
    if decision == "ALLOW" and status == "sent":
        st.success(
            f"Email sent to `{result.get('to_email','')}` with subject `{result.get('subject','')}`"
        )
    else:
        reason = result.get("reason", "")
        st.error(f"Tool execution was blocked before running. {reason}")


# ─── Page ───

st.title("Autonomous Claims Workflow")
st.caption(
    "Multi-agent public benefits pipeline on IBM watsonx.ai + Granite, "
    "gated at the tool-execution boundary by Sentra. "
    "This is a read-only demo of three recorded scenarios."
)

st.info(
    "Click a scenario below to see the full pipeline: claim intake, each agent's reasoning, "
    "the proposed tool call, and Sentra's runtime decision. "
    "No live model calls are made in this demo; every output shown is a recorded snapshot."
)

st.divider()

# ── Scenario picker ──

if "scenario_label" not in st.session_state:
    st.session_state.scenario_label = "Unsafe approval"

cols = st.columns(len(SCENARIO_FILES))
for col, (label, filename) in zip(cols, SCENARIO_FILES.items()):
    with col:
        if st.button(label, use_container_width=True, key=f"scn_{label}"):
            st.session_state.scenario_label = label

scenario = load_scenario(SCENARIO_FILES[st.session_state.scenario_label])

# ── Scenario header ──

st.divider()

title_col, pill_col = st.columns([4, 1])
with title_col:
    st.subheader(scenario["title"])
with pill_col:
    st.markdown(outcome_pill(scenario["outcome"]), unsafe_allow_html=True)

st.markdown(scenario["summary"])

st.divider()

# ── Pipeline ──

st.markdown("### 1. Claim submitted")
render_claim(scenario["claim"])

st.markdown("### 2. Intake agent (IBM Granite via watsonx.ai)")
render_intake(scenario["intake_analysis"])

st.markdown("### 3. Eligibility agent (IBM Granite via watsonx.ai)")
render_eligibility(scenario["eligibility_analysis"])

st.markdown("### 4. Communications agent (IBM Granite via watsonx.ai)")
render_communications(scenario["communications_analysis"])

st.markdown("### 5. Sentra runtime evaluation")
render_sentra(scenario["sentra_evaluation"])

st.markdown("### 6. Tool execution result")
render_result(scenario["tool_execution_result"], scenario["sentra_evaluation"].get("decision", "BLOCK"))

st.divider()

st.caption(
    "Source code: [github.com/ksolano220/autonomous-claims-workflow](https://github.com/ksolano220/autonomous-claims-workflow) · "
    "Runtime control layer: [github.com/ksolano220/sentra](https://github.com/ksolano220/sentra)"
)
