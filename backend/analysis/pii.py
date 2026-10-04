import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
ORDER_NUM_RE = re.compile(r"\b(order|confirmation|reservation)\s*#?\s*\d{3,}\b", re.IGNORECASE)
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def redact_pii(text: str) -> str:
    """
    Best-effort regex redaction of emails, phone numbers, order/confirmation
    numbers, and card-like number sequences. This is pattern matching, not a
    guarantee - it won't catch every way a person might share identifying
    info in free text. Treat it as a safety net, not a compliance control.
    """
    redacted = EMAIL_RE.sub("[email redacted]", text)
    redacted = PHONE_RE.sub("[phone redacted]", redacted)
    redacted = ORDER_NUM_RE.sub("[order # redacted]", redacted)
    redacted = CREDIT_CARD_RE.sub("[number redacted]", redacted)
    return redacted
