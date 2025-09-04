import re
from typing import Tuple

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # ssn
    r"\b\d{10}\b",             # 10-digit phone-ish
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"  # emails
]

def contains_pii(text: str) -> bool:
    for p in PII_PATTERNS:
        if re.search(p, text):
            return True
    return False

def sanitize_output(text: str) -> str:
    # Basic sanitizer: redact emails/ssn/phone numbers
    out = re.sub(r"\b(\d{3}-\d{2}-\d{4})\b", "[REDACTED-SSN]", text)
    out = re.sub(r"\b(\d{10})\b", "[REDACTED-PHONE]", out)
    out = re.sub(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", "[REDACTED-EMAIL]", out)
    return out
