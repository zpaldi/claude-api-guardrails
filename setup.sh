#!/usr/bin/env bash
# V1 AI Guardrails — One-shot setup (macOS M1, claude_enterprise OAuth)
set -euo pipefail

echo "🛡️  V1 AI Guardrails — Phase 1 Setup"
echo "======================================"
echo "Auth mode: claude_enterprise (OAuth — no API key needed)"
echo ""

# --- Prerequisites check ---
command -v python3 >/dev/null || { echo "❌ Python 3 required (brew install python)"; exit 1; }
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python $PYTHON_VERSION"

# --- Virtual environment ---
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
  echo "✓ Created .venv"
else
  echo "✓ .venv already exists"
fi

source .venv/bin/activate

# --- Python dependencies ---
echo ""
echo "Installing dependencies (this may take a minute)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ litellm + guardrails-ai installed"

# --- spaCy model (CPU, ARM64 native, ~40MB, offline after download) ---
echo ""
echo "Downloading spaCy en_core_web_md model (~40MB, one-time)..."
python -m spacy download en_core_web_md -q
echo "✓ spaCy model ready"

# --- GuardrailsAI PII validator ---
echo ""
echo "Installing GuardrailsAI DetectPII validator..."
guardrails hub install hub://guardrails/detect_pii --quiet
echo "✓ DetectPII validator installed"

# --- Shell hook instructions ---
echo ""
echo "======================================"
echo "✅ Setup complete!"
echo ""
echo "Next: add this to your ~/.zshrc (or ~/.zprofile):"
echo ""
echo "  # V1 AI Guardrails — redirect Claude Code through local policy proxy"
echo "  export ANTHROPIC_BASE_URL=http://localhost:4000"
echo ""
echo "Then start the proxy in a new terminal:"
echo "  cd $(pwd) && ./start.sh"
echo ""
echo "Verify it works:"
echo "  ./test_guardrail.sh"
echo ""
echo "To disable temporarily (e.g. for debugging):"
echo "  unset ANTHROPIC_BASE_URL"
echo "======================================"
