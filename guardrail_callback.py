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
from typing import Optional
from litellm.integrations.custom_logger import CustomLogger

# --- PII entity types to block (spaCy + GuardrailsAI built-in) ---
# Extend this list as V1 policy is clarified
BLOCKED_PII_ENTITIES = [
    "EMAIL_ADDRESS",        # ISO 27001 — personal contact data
    "PHONE_NUMBER",         # ISO 27001 — personal contact data
    "PERSON",               # ISO 27001 — individual identifiers
    "UK_NHS",               # ISO 27001 — sensitive health data
    "UK_POSTCODE",          # ISO 27001 — location data
    "CREDIT_CARD",          # PCI DSS / SOC 2 — financial data
    "IBAN_CODE",            # PCI DSS / SOC 2 — financial data
    "IP_ADDRESS",           # ISO 27001 — network identifiers
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
    except ImportError as e:
        raise RuntimeError(
            "guardrails-ai not installed. Run: pip install guardrails-ai && "
            "guardrails hub install hub://guardrails/detect_pii"
        ) from e


class V1PolicyGuardrail(CustomLogger):
    """
    LiteLLM custom callback that enforces V1 IMS AI Policy.
    Registered in litellm_config.yaml under litellm_settings.callbacks.
    """

    def __init__(self):
        self._guard = None  # lazy-load on first call

    @property
    def guard(self):
        if self._guard is None:
            self._guard = _build_guard()
        return self._guard

    def _extract_text(self, messages: list) -> list[str]:
        """Pull string content from all message roles."""
        texts = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                texts.append(content)
            elif isinstance(content, list):
                # Multi-modal messages — extract text parts only
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
        return texts

    def _violation_message(self, detail: str, entity_hint: str = "") -> str:
        hint = f"\n  Detected:  {entity_hint}" if entity_hint else ""
        return (
            "\n"
            "🛑  V1 AI POLICY VIOLATION — PROMPT BLOCKED\n"
            "=" * 55 + "\n"
            "  Reason:    Prompt contains personal or sensitive data\n"
            "             that must not be sent to external AI services.\n"
            f"{hint}\n"
            "  Policy:    ISO 27001 — A.8.2 Information Classification\n"
            "  Action:    Anonymise or remove the flagged content,\n"
            "             then retry your request.\n"
            "  Detail:    " + detail + "\n"
            "=" * 55 + "\n"
        )

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        """Async hook — runs before every API call in the proxy."""
        messages = data.get("messages", [])
        texts = self._extract_text(messages)

        for text in texts:
            try:
                self.guard.validate(text)
            except Exception as e:
                raise ValueError(self._violation_message(str(e))) from None

    def pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        """Sync fallback hook."""
        messages = data.get("messages", [])
        texts = self._extract_text(messages)

        for text in texts:
            try:
                self.guard.validate(text)
            except Exception as e:
                raise ValueError(self._violation_message(str(e))) from None


# LiteLLM loads this instance via config: callbacks: ["guardrail_callback.v1_guardrail"]
v1_guardrail = V1PolicyGuardrail()
