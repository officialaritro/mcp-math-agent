import logging
from guardrails import Guard
import os

logger = logging.getLogger(__name__)
GUARDRAILS_CONFIG = os.getenv("GUARDRAILS_CONFIG", "agentturing/guardrails/policies/math_guardrails.yml")

def make_input_guard():
    # Example: uses guardrails yaml config
    try:
        guard = Guard.from_path(GUARDRAILS_CONFIG)
        return guard
    except Exception as e:
        logger.exception("Failed to load guardrails config: %s", e)
        return None
