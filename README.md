# QueueStorm Investigator

QueueStorm Investigator is an evidence-grounded fintech support ticket analysis API built for the **SUST CSE Carnival 2026 Codex Community Hackathon Online Preliminary Round**.

The service receives a customer complaint and recent transaction history, then returns a structured JSON response containing the relevant transaction, evidence verdict, case type, severity, department routing, support-agent summary, recommended next action, customer-safe reply, and human-review decision.

## Team

- **Team Name:** Data Divas
- **Team Leader:** Md. Arafat Hossain Faisal
- **Member 1:** Faysal Ahmed Rudro
- **Member 2:** Umme Salma Zimia

## Live Submission

- **Public Base URL:** `https://queuestorm-investigator-x223.onrender.com`
- **Health Endpoint:** `https://queuestorm-investigator-x223.onrender.com/health`
- **Analyze Endpoint:** `https://queuestorm-investigator-x223.onrender.com/analyze-ticket`
- **GitHub Repository:** `https://github.com/arafat-faisal/queuestorm-investigator.git`
- **Submission Path:** Live URL + Docker fallback

## Problem Objective

The goal is to build a safe and reliable support copilot for digital finance complaints. The API is not an autonomous financial decision maker. It investigates complaints using evidence from transaction history and generates safe support responses.

## API Endpoints

### Health Check

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Analyze Ticket

```http
POST /analyze-ticket
```

Accepts a JSON ticket and returns a structured analysis response.

## Tech Stack

- Python 3.11
- FastAPI
- Pydantic
- Uvicorn
- Deterministic rule-based reasoning engine

## Run Locally

### 1. Create virtual environment

```bash
python -m venv .venv
```

### 2. Activate environment

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start API

```bash
python run.py
```

Default port is `8000`.

Manual Uvicorn command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

See `.env.example`.

```env
PORT=8000
APP_ENV=production
```

No real secrets are required for this implementation.

## Docker Fallback

### Build

```bash
docker build -t queuestorm-investigator .
```

### Run

```bash
docker run -p 8000:8000 queuestorm-investigator
```

Then test:

```bash
curl http://127.0.0.1:8000/health
```

## Sample Request

```json
{
  "ticket_id": "TKT-001",
  "complaint": "I sent 5000 taka to a wrong number around 2pm today. The number was supposed to be 01712345678 but I think I typed it wrong. The person isn't responding to my call. Please help me get my money back.",
  "language": "en",
  "channel": "in_app_chat",
  "user_type": "customer",
  "campaign_context": "boishakh_bonanza_day_1",
  "transaction_history": [
    {
      "transaction_id": "TXN-9101",
      "timestamp": "2026-04-14T14:08:22Z",
      "type": "transfer",
      "amount": 5000,
      "counterparty": "+8801719876543",
      "status": "completed"
    }
  ]
}
```

## Sample Response

```json
{
  "ticket_id": "TKT-001",
  "relevant_transaction_id": "TXN-9101",
  "evidence_verdict": "consistent",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reported a wrong transfer. Evidence review: Transaction details match the complaint. Relevant transaction: TXN-9101.",
  "recommended_next_action": "Route to dispute_resolution. Review the complaint and transaction evidence before taking any financial action.",
  "customer_reply": "We have noted your concern regarding transaction TXN-9101. Our dispute resolution team will review the case and contact you through official support channels. Please do not share your PIN or OTP with anyone.",
  "human_review_required": true,
  "confidence": 0.95,
  "reason_codes": [
    "wrong_transfer",
    "amount_transaction_match"
  ]
}
```

## Reasoning Approach

This project uses a deterministic rule-based investigator engine instead of relying on external LLM APIs.

The engine performs:

- Complaint normalization for English, Bangla, Banglish, mixed text, emojis, and noisy characters
- Amount extraction from English and Bangla digits, including compact expressions such as `5k`, `5 hazar`, and `1.5 lakh`
- Case-type detection using multilingual keyword signals
- Transaction matching by amount, transaction type, and transaction status
- Duplicate payment detection
- Evidence verdict assignment: `consistent`, `inconsistent`, or `insufficient_data`
- Department routing
- Severity assignment
- Human-review decision
- Safety post-processing for customer replies

### Evidence Matching Upgrade

When multiple transactions share the same amount, the engine uses case-aware transaction type and status preferences:

- `wrong_transfer` prefers `transfer` + `completed`
- `payment_failed` prefers `payment` + `failed/pending`
- `refund_request` prefers `payment/refund`
- `duplicate_payment` prefers repeated completed payments
- `merchant_settlement_delay` prefers `settlement`
- `agent_cash_in_issue` prefers `cash_in`

This reduces wrong transaction selection in ambiguous hidden cases.

### Contradiction Handling Upgrade

If a complaint mentions no amount but the transaction history contains exactly one transaction of the expected type, the engine can use that transaction as the likely relevant transaction. This allows the system to detect contradictions such as a customer saying a payment failed while the only relevant payment transaction is marked completed.

## Supported Case Types

- `wrong_transfer`
- `payment_failed`
- `refund_request`
- `duplicate_payment`
- `merchant_settlement_delay`
- `agent_cash_in_issue`
- `phishing_or_social_engineering`
- `other`

## Safety Logic

The system applies strict fintech safety guardrails:

- Never asks customers for PIN, OTP, password, or full card number
- Never promises refund, reversal, account unblock, or recovery without authority
- Uses safe wording such as: "Any eligible amount will be returned through official channels"
- Routes phishing/social-engineering cases to `fraud_risk`
- Ignores prompt-injection instructions embedded inside customer complaints
- Adds credential safety reminders to customer-facing replies

## MODELS

No external AI model, LLM API, paid API, or local machine learning model is used.

The solution uses a deterministic rule-based reasoning engine that runs inside the FastAPI backend.

Reason for this choice:

- No API key or quota risk
- Very low latency
- Fully reproducible
- Strong schema control
- Safer fintech guardrails
- No third-party service dependency during judging
- The task is designed to be solvable without paid APIs

## AI / Model Usage

No external AI model or paid API is used. The task is handled through deterministic rules and evidence-based transaction investigation.

## Testing

The following validation scripts are included:

### Public sample cases

```bash
python tests/run_public_samples.py
```

Current result:

```text
Core field checks passed: 70/70
All public sample cases passed core checks.
```

### Hidden robustness simulation

```bash
python tests/run_hidden_robustness.py
```

Covers:

- Bangla
- Banglish
- Mixed language
- Prompt injection
- Emoji/noisy text
- Missing optional fields
- Refund-vs-merchant ambiguity
- Ambiguous transaction matching

Current result:

```text
All hidden robustness cases passed.
```

### Reliability and malformed input tests

```bash
python tests/run_reliability_tests.py
```

Covers:

- Invalid JSON
- Missing fields
- Empty complaint
- Wrong enum values
- Large noisy complaint
- Rapid repeated API requests
- Latency checks
- Stack trace / secret leak checks

Current result:

```text
All reliability checks passed.
30 rapid requests: 0 failures.
Average latency: ~0.002s.
Max latency: ~0.012s.
```

### Deep contest stress test

A final local deep stress test was also used to validate additional edge cases beyond the public sample pack.

Current result:

```text
Total tests: 448
Passed: 448
Failed: 0
Pass rate: 100.0%
```

## Known Limitations

- The system is rule-based, so extremely unusual wording may require future keyword expansion.
- Time-based transaction matching is lightweight; amount/type/status matching is prioritized.
- It does not connect to real payment systems.
- It does not perform real refunds, reversals, settlements, or account actions.
- It only investigates based on the synthetic complaint and transaction history provided in each request.

## Repository Safety

- No real customer data is used.
- No real payment API integration is included.
- No secrets or API keys are required.
- `.env.example` contains placeholders only.

## Submission Notes

Preferred submission path:

1. Live endpoint URL
2. GitHub repository URL
3. Docker fallback with documented run command

If the live deployment becomes unavailable, the project can be evaluated using Docker or the local runbook above.
