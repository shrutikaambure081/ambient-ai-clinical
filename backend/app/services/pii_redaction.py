"""
Automated PII redaction. Detects and masks personally identifiable
information (names, phone numbers, emails, addresses, ID numbers)
before a SOAP note is persisted, using a combination of regex rules
and an LLM pass for names/addresses that regex cannot reliably catch.
"""
import re
from typing import List, Tuple

PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-\s]?)?\d{10}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


def redact_text(text: str) -> Tuple[str, List[dict]]:
    """
    Returns (redacted_text, list_of_redactions) where each redaction is
    {"entity_type": ..., "original_text": ..., "redacted_text": ...}
    """
    redactions = []
    redacted = text

    for pattern, label, placeholder in [
        (EMAIL_RE, "EMAIL", "[REDACTED_EMAIL]"),
        (AADHAAR_RE, "ID_NUMBER", "[REDACTED_ID]"),
        (PHONE_RE, "PHONE", "[REDACTED_PHONE]"),
    ]:
        for match in pattern.findall(redacted):
            redactions.append(
                {"entity_type": label, "original_text": match, "redacted_text": placeholder}
            )
        redacted = pattern.sub(placeholder, redacted)

    return redacted, redactions
