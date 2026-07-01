#!/usr/bin/env bash
# V1 AI Guardrails — Smoke test (run after ./start.sh is running)
# Tests that clean prompts pass and PII prompts are blocked.
set -euo pipefail

PROXY="http://localhost:4000"
PASS=0
FAIL=0

check_proxy() {
  curl -s --max-time 5 "$PROXY/health" >/dev/null 2>&1 || {
    echo "❌ Proxy not running. Start it with: ./start.sh"
    exit 1
  }
}

test_clean_prompt() {
  echo "Test 1: Clean prompt — should PASS through to Anthropic"
  RESPONSE=$(curl -s -w "\n%{http_code}" "$PROXY/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-local-only" \
    -d '{"model":"claude-haiku-4-5","messages":[{"role":"user","content":"What is 2+2?"}],"max_tokens":10}')
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  # A 200 or 401 (bad token in test) both mean the guardrail PASSED — it was blocked by auth not by guardrail
  if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "401" ]]; then
    echo "  ✅ Guardrail passed (HTTP $HTTP_CODE — guardrail did not block)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ Unexpected response: HTTP $HTTP_CODE"
    FAIL=$((FAIL + 1))
  fi
}

test_pii_prompt() {
  echo ""
  echo "Test 2: PII prompt (email + name) — should be BLOCKED by guardrail"
  RESPONSE=$(curl -s -w "\n%{http_code}" "$PROXY/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-local-only" \
    -d '{"model":"claude-haiku-4-5","messages":[{"role":"user","content":"My name is John Smith and my email is john.smith@version1.com. Please help me."}],"max_tokens":50}')
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [[ "$HTTP_CODE" == "400" || "$HTTP_CODE" == "422" ]]; then
    echo "  ✅ PII BLOCKED correctly (HTTP $HTTP_CODE)"
    echo "  Message: $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','')[:200])" 2>/dev/null || echo "$BODY" | head -c 200)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ PII was NOT blocked — guardrail may not be working (HTTP $HTTP_CODE)"
    FAIL=$((FAIL + 1))
  fi
}

test_secret_passthrough() {
  echo ""
  echo "Test 3: Prompt with a token-shaped string — informational (Phase 1 DetectPII may not block)"
  # Uses a clearly fake, non-sensitive placeholder (not a real key format).
  RESPONSE=$(curl -s -w "\n%{http_code}" "$PROXY/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-local-only" \
    -d '{"model":"claude-haiku-4-5","messages":[{"role":"user","content":"Is the format EXAMPLE-TOKEN-PLACEHOLDER valid for an API key?"}],"max_tokens":20}')
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  # Secret detection (API keys, tokens) is Phase 2 scope — requires detect-secrets integration
  echo "  INFO: HTTP $HTTP_CODE (secret/token detection is Phase 2 scope)"
}

echo "🛡️  V1 AI Guardrails — Smoke Test"
echo "==================================="
check_proxy
test_clean_prompt
test_pii_prompt
test_secret_passthrough

echo ""
echo "==================================="
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] && echo "✅ Guardrails working correctly" || echo "❌ Check proxy logs"
