from fastapi import FastAPI, HTTPException
from app.schemas import AnalyzeTicketRequest, AnalyzeTicketResponse
from app.engine import analyze

app = FastAPI(
    title="QueueStorm Investigator",
    version="0.2.0",
    description="Evidence-grounded fintech support ticket investigator API"
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze-ticket", response_model=AnalyzeTicketResponse)
def analyze_ticket(payload: AnalyzeTicketRequest):
    complaint = payload.complaint.strip()

    if not complaint:
        raise HTTPException(status_code=422, detail="Complaint cannot be empty.")

    try:
        return analyze(payload)
    except Exception:
        # Safe controlled fallback. No secrets, no stack traces.
        return AnalyzeTicketResponse(
            ticket_id=payload.ticket_id,
            relevant_transaction_id=None,
            evidence_verdict="insufficient_data",
            case_type="other",
            severity="low",
            department="customer_support",
            agent_summary="The service could not complete detailed reasoning for this ticket and returned a safe fallback.",
            recommended_next_action="Review the ticket manually and verify transaction details before taking action.",
            customer_reply="Thank you for reaching out. We have received your concern and will review it through official support channels. Please do not share your PIN or OTP with anyone.",
            human_review_required=False,
            confidence=0.4,
            reason_codes=["safe_exception_fallback"]
        )