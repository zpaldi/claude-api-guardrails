#!/usr/bin/env bash
# V1 AI Guardrails — Start the local proxy
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d ".venv" ]]; then
  echo "❌ Run ./setup.sh first"
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

# guardrail_callback.py must be importable by LiteLLM
PYTHONPATH="$(pwd):${PYTHONPATH:-}"
export PYTHONPATH

echo "🛡️  V1 AI Guardrails proxy starting on http://localhost:4000"
echo "   Auth: claude_enterprise OAuth passthrough"
echo "   Press Ctrl+C to stop"
echo ""

# --host 127.0.0.1 restricts the proxy to loopback only — never expose on 0.0.0.0
litellm --config litellm_config.yaml --port 4000 --host 127.0.0.1
