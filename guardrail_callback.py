"""
V1 AI Policy Guardrail — Phase 1 (PII / Data Classification)

Intercepts every outbound Claude API call via LiteLLM proxy.
Blocks prompts containing PII before they leave the machine.

Policy alignment:
  ISO 27001  — A.8.2 Information Classification & Protection
  ISO 42001  — 6.1.2 AI Risk Assessment
  SOC 2 TSC  — CC6.1 Logical & Physical Access Controls

No HuggingFace models, no internet calls during validation.
spaCy en_core_web_md only (CPU, ~40MB, offline).
"""
import logging
import os
import threading
from datetime import datetime, timezone

from litellm.integrations.custom_logger import CustomLogger

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
_log = logging.getLogger("v1-guardrail")

# Configurable via env: V1_BLOCKED_PII_ENTITIES=EMAIL_ADDRESS,PHONE_NUMBER,...
_DEFAULT_PII_ENTITIES = [
    "EMAIL_ADDRESS",  # ISO 27001 — personal contact data
    "PHONE_NUMBER",   # ISO 27001 — personal contact data
    "PERSON",         # ISO 27001 — individual identifiers
    "UK_NHS",         # ISO 27001 — sensitive health data
    "UK_POSTCODE",    # ISO 27001 — location data
    "CREDIT_CARD",    # PCI DSS / SOC 2 — financial data
    "IBAN_CODE",      # PCI DSS / SOC 2 — financial data
    "IP_ADDRESS",     # ISO 27001 — network identifiers
]

BLOCKED_PII_ENTITIES: list[str] = [
    e.strip()
    for e in os.environ.get("V1_BLOCKED_PII_ENTITIES", ",".join(_DEFAULT_PII_ENTITIES)).split(",")
    if e.strip()
]


def _build_guard():
    """Lazy-load Guard to avoid import errors if guardrails-ai not installed."""
    try:
        from guardrails import Guard
        from guardrails.hub import DetectPII

        return Guard().use(
            DetectPII,
            pii_entities=BLOCKED_PII_ENTITIES,
            on_fail="exception",
        )
    except ImportError as exc:
        raise RuntimeError(
            "guardrails-ai not installed. Run: pip install guardrails-ai && "
            "guardrails hub install hub://guardrails/detect_pii"
        ) from exc


class V1PolicyGuardrail(CustomLogger):
    """
    LiteLLM custom callback that enforces V1 IMS AI Policy.
    Registered in litellm_config.yaml under litellm_settings.callbacks.
    """

    def __init__(self) -> None:
        self._guard = None
        self._lock = threading.Lock()  # guard lazy-init is thread-safe

    @property
    def guard(self):
        if self._guard is None:
            with self._lock:
                if self._guard is None:  # double-checked locking
                    self._guard = _build_guard()
        return self._guard

    def _extract_text(self, messages: list) -> list[str]:
        texts: list[str] = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                texts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
        return texts

    def _violation_message(self, detail: str) -> str:
        return (
            "\n"
            "[V1 AI POLICY VIOLATION - PROMPT BLOCKED]\n"
            "=" * 55 + "\n"
            "  Reason:    Prompt contains personal or sensitive data\n"
            "             that must not be sent to external AI services.\n"
            "  Policy:    ISO 27001 - A.8.2 Information Classification\n"
            "  Action:    Anonymise or remove the flagged content,\n"
            "             then retry your request.\n"
            "  Detail:    " + detail + "\n"
            "=" * 55 + "\n"
        )

    def _validate_messages(self, data: dict) -> None:
        """Shared validation logic for sync and async hooks."""
        messages = data.get("messages", [])
        texts = self._extract_text(messages)
        for text in texts:
            try:
                self.guard.validate(text)
            except Exception as exc:
                msg = self._violation_message(str(exc))
                # Audit trail — written to stderr/log regardless of caller
                _log.warning(
                    "V1 guardrail BLOCKED call | ts=%s | model=%s | reason=%s",
                    datetime.now(timezone.utc).isoformat(),
                    data.get("model", "unknown"),
                    str(exc)[:200],
                )
                raise ValueError(msg) from None

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        self._validate_messages(data)

    def pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        self._validate_messages(data)


# LiteLLM loads this instance via config: callbacks: ["guardrail_callback.v1_guardrail"]
v1_guardrail = V1PolicyGuardrail()
