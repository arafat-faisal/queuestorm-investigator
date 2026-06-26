from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class Transaction(BaseModel):
    transaction_id: str
    timestamp: str
    type: Literal["transfer", "payment", "cash_in", "cash_out", "settlement", "refund"]
    amount: float
    counterparty: str
    status: Literal["completed", "failed", "pending", "reversed"]


class AnalyzeTicketRequest(BaseModel):
    ticket_id: str
    complaint: str
    language: Optional[Literal["en", "bn", "mixed"]] = "en"
    channel: Optional[Literal["in_app_chat", "call_center", "email", "merchant_portal", "field_agent"]] = None
    user_type: Optional[Literal["customer", "merchant", "agent", "unknown"]] = "unknown"
    campaign_context: Optional[str] = None
    transaction_history: Optional[List[Transaction]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalyzeTicketResponse(BaseModel):
    ticket_id: str
    relevant_transaction_id: Optional[str]
    evidence_verdict: Literal["consistent", "inconsistent", "insufficient_data"]
    case_type: Literal[
        "wrong_transfer",
        "payment_failed",
        "refund_request",
        "duplicate_payment",
        "merchant_settlement_delay",
        "agent_cash_in_issue",
        "phishing_or_social_engineering",
        "other"
    ]
    severity: Literal["low", "medium", "high", "critical"]
    department: Literal[
        "customer_support",
        "dispute_resolution",
        "payments_ops",
        "merchant_operations",
        "agent_operations",
        "fraud_risk"
    ]
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: Optional[float] = 0.5
    reason_codes: Optional[List[str]] = Field(default_factory=list)