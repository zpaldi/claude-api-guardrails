# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| main    | Yes       |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately via GitHub's [Security Advisories](https://github.com/zpaldi/claude-api-guardrails/security/advisories/new).

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (optional)

We aim to respond within 5 business days.

## Threat Model

This tool runs **locally** on a developer's machine as a pre-call interceptor.
Key trust assumptions:

| Boundary | Trust level | Notes |
|---|---|---|
| Local loopback (127.0.0.1:4000) | Trusted | Proxy only listens on localhost |
| Anthropic API (api.anthropic.com) | Trusted | TLS enforced |
| guardrails-ai hub | External | One-time install; hash not pinned |
| spaCy model (en_core_web_md) | External | One-time download via spacy CLI |

## Known Limitations (Phase 1)

- PII detection uses probabilistic NER (spaCy) — false negatives possible.
- No audit log — violations raise an error but are not persisted.
- No rate limiting on the proxy itself.
- GuardrailsAI hub packages are downloaded without hash verification.
