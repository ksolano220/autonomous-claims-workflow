# Autonomous Claims Workflow

Multi-agent system for public service claims that intentionally demonstrates unsafe approval actions triggered without verification, highlighting the need for runtime control (Sentra).

## Overview

Simulates an emergency relief workflow where applicants submit claims for a $5,000 unemployment relief package. Three agents process claims autonomously — and can trigger unsafe actions without runtime enforcement.

## Agents

- **Intake Agent** — validates claim data, flags missing documents
- **Eligibility Agent** — determines approval/denial (intentionally optimistic)
- **Communications Agent** — proposes email notifications based on the decision

## Getting Started

```bash
pip install -r requirements.txt
streamlit run app/portal.py
```
