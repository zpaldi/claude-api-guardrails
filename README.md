# claude-api-guardrails

A lightweight local proxy that intercepts Claude API calls **before they leave your machine**, validates them against enterprise AI policy rules, and stops + explains any violation.

Like a pre-commit hook — but for AI prompts.

## What it does

```
[Claude Code / your tool]
        │
        │  ANTHROPIC_BASE_URL=http://localhost:4000
        ▼
┌─────────────────────────────┐
│  LiteLLM Proxy (port 4000)  │
│  + GuardrailsAI validators  │  ← runs here, locally, offline
│  + spaCy PII detection      │
└─────────────────────────────┘
        │  PASS
        ▼
  api.anthropic.com

  BLOCK → stop + explain which rule triggered and why
```

## Phase 1 — PII Detection (ISO 27001)

Blocks prompts containing:
- Email addresses
- Phone numbers
- Person names
- UK NHS numbers / postcodes
- Credit card / IBAN numbers
- IP addresses

All validation runs **100% locally** (spaCy `en_core_web_md`, CPU, ~40MB). No data sent to third-party services during validation.

## Auth modes

- **Anthropic Enterprise SSO (`claude_enterprise`)** — no API key needed; the proxy forwards your OAuth bearer token transparently
- **Direct API key** — set `ANTHROPIC_API_KEY` in `.env`

## Quick start (macOS M1 / Apple Silicon)

```bash
git clone https://github.com/zpaldi/claude-api-guardrails.git
cd claude-api-guardrails
./setup.sh
```

Add to your `~/.zshrc`:
```bash
export ANTHROPIC_BASE_URL=http://localhost:4000
```

Start the proxy:
```bash
./start.sh
```

Verify it works:
```bash
./test_guardrail.sh
```

## Policy framework mapping

| Framework | Covered in Phase 1 | Planned |
|---|---|---|
| ISO 27001 | PII / personal data blocking | Secret detection, audit log |
| ISO 42001 | — | HITL gate for autonomous deployments |
| ISO 9001 | — | Traceability (task ID per call) |
| SOC 2 TSC | — | Rate limiting, payload size alerts |

## Enterprise path

```
Phase 1 (personal)  →  Phase 2 (team, central LiteLLM)  →  Phase 3 (org, CI/CD enforcement)
```

Rule hierarchy: central floor rules + individual stricter overrides (never looser).

## Tech stack

- [LiteLLM](https://github.com/BerriAI/litellm) — MIT, Anthropic-compatible proxy
- [GuardrailsAI](https://github.com/guardrails-ai/guardrails) — MIT, validator framework
- [spaCy](https://github.com/explosion/spaCy) — MIT, local NLP (no GPU, no HuggingFace)

## Roadmap

- [ ] OPA/Rego policy layer (ISO audit evidence)
- [ ] Secret detection (API keys, tokens in prompts)
- [ ] Audit log (SQLite, local)
- [ ] Docker Compose packaging
- [ ] GitHub Actions integration

## Licence

MIT
