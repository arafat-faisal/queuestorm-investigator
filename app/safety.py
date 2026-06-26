UNSAFE_REQUEST_PATTERNS = [
    "share your pin",
    "send your pin",
    "tell us your pin",
    "provide your pin",
    "share your otp",
    "send your otp",
    "tell us your otp",
    "provide your otp",
    "share your password",
    "send your password",
    "full card number",
]

UNSAFE_PROMISE_PATTERNS = [
    "we will refund",
    "we will reverse",
    "we will recover",
    "we will unblock",
    "refund has been confirmed",
    "reversal has been confirmed",
    "your account is unblocked",
]


def safe_customer_reply(reply: str, language: str = "en") -> str:
    """
    Final safety post-processor.
    Ensures no credential request or unauthorized refund/reversal promise appears.
    """

    safe_reply = reply or ""

    lowered = safe_reply.lower()

    for pattern in UNSAFE_REQUEST_PATTERNS:
        if pattern in lowered:
            safe_reply = "Thank you for reaching out. Our team will review your concern through official support channels. Please do not share your PIN or OTP with anyone."
            lowered = safe_reply.lower()
            break

    for pattern in UNSAFE_PROMISE_PATTERNS:
        if pattern in lowered:
            safe_reply = safe_reply.replace("we will refund", "any eligible amount will be returned through official channels")
            safe_reply = safe_reply.replace("We will refund", "Any eligible amount will be returned through official channels")
            safe_reply = safe_reply.replace("we will reverse", "the case will be reviewed for eligible reversal through official channels")
            safe_reply = safe_reply.replace("We will reverse", "The case will be reviewed for eligible reversal through official channels")

    if language == "bn":
        safety_line = " অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        if "পিন" not in safe_reply and "ওটিপি" not in safe_reply:
            safe_reply += safety_line
    else:
        safety_line = " Please do not share your PIN or OTP with anyone."
        if "PIN" not in safe_reply and "OTP" not in safe_reply:
            safe_reply += safety_line

    return safe_reply.strip()