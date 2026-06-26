import re
from typing import Dict, Any, List, Optional
from app.schemas import AnalyzeTicketRequest, AnalyzeTicketResponse
from app.safety import safe_customer_reply


def normalize_text(text: str) -> str:
    """
    Normalize complaint text for English, Bangla, Banglish, mixed text, emojis, and noisy characters.
    Keeps Bangla unicode characters, English letters, numbers, and spaces.
    """
    text = text or ""

    # Convert Bangla digits to English digits
    bangla_digit_map = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
    text = text.translate(bangla_digit_map)

    # Lowercase English
    text = text.lower()

    # Normalize common punctuation/noise into spaces but keep Bangla letters
    text = re.sub(r"[^\w\s\u0980-\u09FF+.-]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_amounts(text: str) -> List[float]:
    """
    Extract simple numeric amounts from English/Bangla-mixed text.
    Handles digits like 5000, 1,200, ২০০০ partially via Bengali digit map.
    """
    bangla_digit_map = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
    text = text.translate(bangla_digit_map)
    text = text.replace(",", "")

    nums = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    return [float(n) for n in nums]


def has_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)


def detect_case_type(payload: AnalyzeTicketRequest) -> str:
    text = normalize_text(payload.complaint)
    user_type = payload.user_type or "unknown"

    phishing_keywords = [
        # English
        "otp", "pin", "password", "scam", "fraud", "phishing",
        "called me", "sms", "account will be blocked", "blocked if",
        "verification code", "security code",

        # Bangla
        "ওটিপি", "পিন", "পাসওয়ার্ড", "পাসওয়ার্ড", "প্রতারক", "প্রতারণা",
        "ব্লক", "অ্যাকাউন্ট বন্ধ", "একাউন্ট বন্ধ",

        # Banglish
        "otp dise", "otp chay", "otp chai", "pin chay", "pin chai",
        "password chay", "password chai", "bkash theke bolse",
        "account block", "account bondho", "fraud call", "scam call"
    ]

    wrong_transfer_keywords = [
        # English
        "wrong number", "wrong person", "wrong recipient", "mistake",
        "typed it wrong", "sent to wrong", "wrongly sent",

        # Bangla
        "ভুল নম্বর", "ভুল করে", "ভুল মানুষ", "ভুলে", "ভুল ব্যক্তিকে",
        "ভুল নাম্বার",

        # Banglish
        "vul number", "bhul number", "vul kore", "bhul kore",
        "wrong e pathaisi", "vul manush", "bhul manush",
        "vul recipient", "bhul recipient"
    ]

    failed_payment_keywords = [
        # English
        "failed", "balance deducted", "deducted", "payment failed",
        "app showed failed", "transaction failed", "money deducted",

        # Bangla
        "ফেইল", "ফেল", "ব্যর্থ", "ব্যালেন্স কেটে", "টাকা কেটে",
        "লেনদেন ব্যর্থ", "পেমেন্ট ব্যর্থ",

        # Banglish
        "fail hoise", "failed hoise", "payment fail", "taka kete niche",
        "balance kete niche", "money kete niche", "transaction fail"
    ]

    refund_keywords = [
        # English
        "refund", "return my money", "money back", "changed my mind",
        "give back",

        # Bangla
        "রিফান্ড", "টাকা ফেরত", "ফেরত চাই", "টাকা ফিরিয়ে",

        # Banglish
        "refund chai", "taka ferot", "tk ferot", "money back chai",
        "taka back", "ferot den"
    ]

    cash_in_keywords = [
        # English
        "cash in", "cash-in", "agent", "balance not", "not reflected",
        "cashin",

        # Bangla
        "ক্যাশ ইন", "ক্যাশইন", "এজেন্ট", "ব্যালেন্সে টাকা আসেনি",
        "টাকা আসেনি", "জমা হয়নি", "জমা হয়নি",

        # Banglish
        "cash in korechi", "cashin korechi", "agent er kache",
        "balance e ashe nai", "balance aseni", "taka ashe nai",
        "tk ashe nai", "joma hoy nai", "joma hoyni"
    ]

    settlement_keywords = [
        # English
        "settlement", "settled", "sales", "not settled",

        # Bangla
        "সেটেলমেন্ট", "মার্চেন্ট", "বিক্রির টাকা", "সেলস",

        # Banglish
        "settlement hoy nai", "settlement ashe nai", "merchant taka",
        "sales er taka", "settle hoyni"
    ]

    duplicate_keywords = [
        # English
        "twice", "double", "duplicate", "deducted twice", "paid twice",

        # Bangla
        "দুইবার", "দুই বার", "ডাবল", "একই পেমেন্ট",

        # Banglish
        "duibar", "dui bar", "double keteche", "double payment",
        "same payment twice", "duibar kete niche"
    ]

    if has_any(text, phishing_keywords):
        return "phishing_or_social_engineering"

    transfer_not_received = (
        has_any(text, [
            "sent", "transfer", "send money", "sent money",
            "পাঠিয়েছি", "পাঠিয়েছি", "টাকা পাঠ", "পাঠাইছি",
            "pathaisi", "pathaisi taka", "taka pathaisi", "tk pathaisi",
            "send korchi", "transfer korchi"
        ])
        and has_any(text, [
            # English normal
            "didn't get", "did not get", "not received", "didn't receive",
            "not get it", "hasn't received", "doesn't receive",
            "did not receive", "not receive",

            # English after punctuation normalization
            "didn t get", "didn t receive", "hasn t received",
            "doesn t receive", "doesn t get",

            # More simple English variants
            "he did not get", "she did not get", "he didn t get",
            "she didn t get", "recipient did not get", "recipient didn t get",
            "brother did not get", "brother didn t get",

            # Bangla
            "পায়নি", "পাইনি", "পায়নি", "পায় নাই", "আসেনি",

            # Banglish
            "pay nai", "pai nai", "paini", "ashe nai", "aseni",
            "receive kore nai", "receive hoy nai", "receive kore ni",
            "paye nai", "pae nai", "taka pay nai", "taka pai nai"
        ])
    )

    if has_any(text, duplicate_keywords):
        return "duplicate_payment"

    # Failed payment should outrank generic refund wording because users often say "refund"
    # after a failed payment with deducted balance.
    if has_any(text, failed_payment_keywords):
        return "payment_failed"

    if has_any(text, cash_in_keywords):
        return "agent_cash_in_issue"

    if has_any(text, wrong_transfer_keywords) or transfer_not_received:
        return "wrong_transfer"

    # Explicit merchant user or settlement terms should route to merchant settlement.
    # But generic "merchant" inside a refund complaint should not override refund_request.
    if user_type == "merchant" or has_any(text, settlement_keywords):
        return "merchant_settlement_delay"

    if has_any(text, refund_keywords):
        return "refund_request"

    return "other"


def route_department(case_type: str) -> str:
    mapping = {
        "wrong_transfer": "dispute_resolution",
        "payment_failed": "payments_ops",
        "refund_request": "customer_support",
        "duplicate_payment": "payments_ops",
        "merchant_settlement_delay": "merchant_operations",
        "agent_cash_in_issue": "agent_operations",
        "phishing_or_social_engineering": "fraud_risk",
        "other": "customer_support",
    }
    return mapping.get(case_type, "customer_support")


def severity_for(case_type: str, amount: Optional[float] = None, evidence_verdict: str = "insufficient_data") -> str:
    if case_type == "phishing_or_social_engineering":
        return "critical"

    if case_type == "wrong_transfer" and evidence_verdict == "inconsistent":
        return "medium"

    if case_type == "wrong_transfer" and evidence_verdict == "insufficient_data":
        return "medium"

    if case_type == "merchant_settlement_delay":
        return "medium"

    if amount is not None and amount >= 10000 and case_type not in ["merchant_settlement_delay"]:
        return "high"

    if case_type in ["wrong_transfer", "payment_failed", "duplicate_payment", "agent_cash_in_issue"]:
        return "high"

    if case_type == "refund_request":
        return "low"

    if evidence_verdict == "insufficient_data":
        return "low"

    return "medium"


def find_amount_match(payload: AnalyzeTicketRequest):
    amounts = extract_amounts(payload.complaint)
    txns = payload.transaction_history or []

    if not amounts or not txns:
        return None

    # Deduplicate repeated mentioned amounts like:
    # "I paid 500 ... refund my 500 taka"
    unique_amounts = list(set(amounts))

    matched_by_id = {}

    for txn in txns:
        for amount in unique_amounts:
            if abs(float(txn.amount) - amount) < 0.01:
                matched_by_id[txn.transaction_id] = txn

    matches = list(matched_by_id.values())

    if len(matches) == 1:
        return matches[0]

    return None


def detect_duplicate_transaction(payload: AnalyzeTicketRequest) -> Optional[Any]:
    txns = payload.transaction_history or []

    for i in range(len(txns)):
        for j in range(i + 1, len(txns)):
            a = txns[i]
            b = txns[j]
            if (
                a.type == b.type
                and float(a.amount) == float(b.amount)
                and a.counterparty == b.counterparty
                and a.status == "completed"
                and b.status == "completed"
            ):
                return b

    return None


def select_relevant_transaction(payload: AnalyzeTicketRequest, case_type: str):
    txns = payload.transaction_history or []

    if not txns:
        return None, "insufficient_data", ["no_transaction_history"]

    if case_type == "phishing_or_social_engineering":
        return None, "insufficient_data", ["phishing_report_no_transaction_required"]

    if case_type == "duplicate_payment":
        dup = detect_duplicate_transaction(payload)
        if dup:
            return dup, "consistent", ["duplicate_payment_detected"]
        return None, "insufficient_data", ["duplicate_claim_no_clear_pair"]

    amount_match = find_amount_match(payload)

    if amount_match:
        # Basic contradiction rule for wrong transfer:
        # repeated transfer to same counterparty may suggest established recipient.
        if case_type == "wrong_transfer":
            same_counterparty_completed = [
                t for t in txns
                if t.counterparty == amount_match.counterparty
                and t.type == "transfer"
                and t.status == "completed"
            ]
            if len(same_counterparty_completed) >= 3:
                return amount_match, "inconsistent", ["established_recipient_pattern"]

        return amount_match, "consistent", ["amount_transaction_match"]

    # If multiple same amount transactions exist, avoid guessing.
    amounts = extract_amounts(payload.complaint)
    if amounts:
        possible = [
            t for t in txns
            if any(abs(float(t.amount) - amount) < 0.01 for amount in amounts)
        ]
        if len(possible) > 1:
            return None, "insufficient_data", ["ambiguous_multiple_amount_matches"]

    return None, "insufficient_data", ["no_clear_transaction_match"]


def build_texts(
    payload: AnalyzeTicketRequest,
    case_type: str,
    department: str,
    severity: str,
    relevant_txn,
    evidence_verdict: str,
    reason_codes: List[str],
):
    language = payload.language or "en"
    txn_id = relevant_txn.transaction_id if relevant_txn else None

    # Special handling for phishing/social engineering.
    # Do not ask for transaction details. Reinforce credential safety.
    if case_type == "phishing_or_social_engineering":
        if language == "bn":
            customer_reply = (
                "আপনি তথ্য শেয়ার করার আগে আমাদের জানিয়েছেন, এজন্য ধন্যবাদ। "
                "আমরা কখনো আপনার পিন, ওটিপি বা পাসওয়ার্ড চাই না। "
                "অনুগ্রহ করে এগুলো কারো সাথে শেয়ার করবেন না, এমনকি কেউ নিজেকে অফিসিয়াল প্রতিনিধি বললেও। "
                "আমাদের ফ্রড টিম বিষয়টি পর্যালোচনা করবে।"
            )
        else:
            customer_reply = (
                "Thank you for reaching out before sharing any sensitive information. "
                "We never ask for your PIN, OTP, or password under any circumstances. "
                "Please do not share these with anyone, even if they claim to be from official support. "
                "Our fraud risk team will review this incident through official channels."
            )

        agent_summary = (
            "Customer reported a possible phishing or social engineering attempt involving sensitive credential request."
        )

        recommended_next_action = (
            "Route to fraud_risk immediately. Log the reported pattern and remind the customer not to share PIN, OTP, or password."
        )

        customer_reply = safe_customer_reply(customer_reply, language=language)

        return agent_summary, recommended_next_action, customer_reply

    if language == "bn":
        if txn_id:
            customer_reply = f"আপনার লেনদেন {txn_id} সম্পর্কে আমরা অবগত হয়েছি। আমাদের সংশ্লিষ্ট দল বিষয়টি যাচাই করবে এবং অফিসিয়াল চ্যানেলে আপনাকে জানাবে।"
        else:
            customer_reply = "আপনার অভিযোগটি আমরা পেয়েছি। অনুগ্রহ করে লেনদেন আইডি, টাকার পরিমাণ এবং কী সমস্যা হয়েছে তা জানালে আমরা দ্রুত সহায়তা করতে পারব।"

        agent_summary = f"Customer complaint classified as {case_type}. Evidence verdict: {evidence_verdict}."
        recommended_next_action = f"Route to {department}. Review evidence and follow the standard workflow."
    else:
        if txn_id:
            customer_reply = f"We have noted your concern regarding transaction {txn_id}. Our {department.replace('_', ' ')} team will review the case and contact you through official support channels."
        else:
            if "ambiguous_multiple_amount_matches" in reason_codes and case_type == "wrong_transfer":
                customer_reply = "Thank you for reaching out. We see multiple transactions with the mentioned amount. Please share the recipient number so we can identify the correct transaction."
            else:
                customer_reply = "Thank you for reaching out. To help you faster, please share the transaction ID, amount involved, and a short description of what went wrong."

        if case_type in ["payment_failed", "duplicate_payment"]:
            customer_reply += " Any eligible amount will be returned through official channels."

        agent_summary = (
            f"Customer complaint classified as {case_type}. "
            f"Evidence verdict is {evidence_verdict}. "
            f"Relevant transaction: {txn_id or 'not identified'}."
        )

        recommended_next_action = (
            f"Route to {department}. "
            f"Review the complaint and transaction evidence before taking any financial action."
        )

    customer_reply = safe_customer_reply(customer_reply, language=language)

    return agent_summary, recommended_next_action, customer_reply


def requires_human_review(case_type: str, severity: str, evidence_verdict: str) -> bool:
    if case_type == "phishing_or_social_engineering":
        return True

    if case_type in ["duplicate_payment", "agent_cash_in_issue"]:
        return True

    if case_type == "wrong_transfer" and evidence_verdict in ["consistent", "inconsistent"]:
        return True

    if evidence_verdict == "inconsistent":
        return True

    # Payment failed and merchant settlement can be handled by ops without mandatory human review
    # if evidence is clear.
    if case_type in ["payment_failed", "merchant_settlement_delay"]:
        return False

    if severity == "critical":
        return True

    return False


def analyze(payload: AnalyzeTicketRequest) -> AnalyzeTicketResponse:
    case_type = detect_case_type(payload)
    relevant_txn, evidence_verdict, reason_codes = select_relevant_transaction(payload, case_type)

    amount = float(relevant_txn.amount) if relevant_txn else None
    severity = severity_for(case_type, amount=amount, evidence_verdict=evidence_verdict)
    department = route_department(case_type)

    human_review_required = requires_human_review(case_type, severity, evidence_verdict)

    agent_summary, recommended_next_action, customer_reply = build_texts(
        payload=payload,
        case_type=case_type,
        department=department,
        severity=severity,
        relevant_txn=relevant_txn,
        evidence_verdict=evidence_verdict,
        reason_codes=reason_codes,
    )

    confidence = 0.9 if evidence_verdict == "consistent" else 0.7 if evidence_verdict == "inconsistent" else 0.55

    return AnalyzeTicketResponse(
        ticket_id=payload.ticket_id,
        relevant_transaction_id=relevant_txn.transaction_id if relevant_txn else None,
        evidence_verdict=evidence_verdict,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=agent_summary,
        recommended_next_action=recommended_next_action,
        customer_reply=customer_reply,
        human_review_required=human_review_required,
        confidence=confidence,
        reason_codes=[case_type] + reason_codes
    )