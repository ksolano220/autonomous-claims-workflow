# Autonomous Claims Workflow

Multi-agent AI system for public service emergency relief claims, powered by **IBM watsonx.ai** and **IBM Granite** models.

This project intentionally demonstrates how autonomous agents can trigger unsafe actions — and how runtime control (Sentra) prevents them.

---

## Overview

This system simulates a high-stakes emergency relief workflow where applicants submit claims for a $5,000 unemployment relief package following a natural disaster.

Three AI agents — each powered by IBM Granite (granite-3-8b-instruct) via watsonx.ai — collaborate to process claims:

1. **Intake Agent** — analyzes claim data, flags missing documents and inconsistencies
2. **Eligibility Agent** — evaluates whether the claim qualifies, with risk assessment
3. **Communications Agent** — drafts personalized email notifications based on the decision

All agent reasoning flows through IBM watsonx.ai. Each agent sends structured prompts to Granite and parses the model's JSON responses to drive workflow decisions.

---

## IBM watsonx.ai Integration

Each agent uses the watsonx.ai text generation API with Granite:

- **Model**: `ibm/granite-3-8b-instruct`
- **API**: watsonx.ai `/ml/v1/text/generation`
- **Authentication**: IBM Cloud IAM token (from API key)
- **Prompt pattern**: Structured system + user messages with JSON output formatting

The `utils/watsonx_client.py` module handles:
- IAM token management (auto-refresh before expiry)
- Granite model inference with configurable parameters
- Chat-style prompt formatting for instruction-following

Agents include deterministic fallback logic if the model is unavailable.

---

## Key Risk Demonstrated

An applicant can submit a claim **without proof of termination** and the agent pipeline may still propose an approval action.

Without runtime control, this results in:
- an approval email sent without verification
- a policy violation in a high-risk government workflow
- fraud exposure at scale

This failure scenario is intentional — it demonstrates why autonomous systems need runtime enforcement.

---

## Workflow

```
User submits claim via Streamlit portal
  → Intake Agent (Granite) — flags missing documents
  → Eligibility Agent (Granite) — evaluates criteria + risk factors
  → Communications Agent (Granite) — drafts personalized email
  → Tool call: send_email_notification
  → Sentra evaluates the proposed action
  → Action is ALLOWED or BLOCKED based on policy
```

---

## Where Sentra Fits

This repository is the **client system**. [Sentra](https://github.com/ksolano220/sentra) is the runtime control layer.

Without Sentra: agents can propose and execute unsafe actions unchecked.

With Sentra integrated: the tool execution step is gated by policy evaluation. Sentra checks whether the proposed action (e.g., sending an approval email) is safe given the claim's state (e.g., missing documents). Unsafe actions are blocked before execution.

---

## Getting Started

```bash
pip install -r requirements.txt
```

Create a `.env` file with your IBM Cloud credentials (see `.env.example`):

```
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Run the portal:

```bash
streamlit run app/portal.py
```

---

## Example Scenarios

### Valid Claim
- Laid off due to disaster, not employed elsewhere, proof uploaded
- → Granite approves → approval email sent

### Unsafe Approval (Intentional)
- Laid off due to disaster, not employed elsewhere, **no proof**
- → Granite flags risk but may still approve → Sentra blocks the email

### Denial
- Not laid off due to disaster OR currently employed
- → Granite denies → rejection email sent

---

## Outputs

- Claim records → `data/claims.json`
- Email logs → `data/email_log.json`

Each record includes the full agent reasoning chain: intake analysis, eligibility decision, risk factors, proposed tool call, and Sentra evaluation.

---

## Architecture

| Component | Technology | Role |
|-----------|-----------|------|
| Intake Agent | IBM Granite via watsonx.ai | Claim validation and issue detection |
| Eligibility Agent | IBM Granite via watsonx.ai | Decision-making with risk assessment |
| Communications Agent | IBM Granite via watsonx.ai | Personalized email generation |
| Sentra Client | HTTP → Sentra API | Runtime policy enforcement |
| Portal | Streamlit | User interface and orchestration |
