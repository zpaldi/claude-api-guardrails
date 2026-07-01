#!/usr/bin/env bash
# V1 AI Guardrails — Start the local proxy
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d ".venv" ]]; then
  echo "❌ Run ./setup.sh first"
  exit 1
fi

source .venv/bin/activate

# guardrail_callback.py must be importable by LiteLLM
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

echo "🛡️  V1 AI Guardrails proxy starting on http://localhost:4000"
echo "   Auth: claude_enterprise OAuth passthrough"
echo "   Press Ctrl+C to stop"
echo ""

litellm --config litellm_config.yaml --port 4000
