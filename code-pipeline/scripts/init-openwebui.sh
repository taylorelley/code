#!/bin/bash
# Auto-configuration script for Open WebUI with Code Pipeline
# This script runs when the Open WebUI container starts

set -e

echo "🚀 Starting Open WebUI auto-configuration..."

# Wait for Open WebUI to be ready
echo "⏳ Waiting for Open WebUI to initialize..."
sleep 5

# The pipelines directory is already mounted, so code_pipeline.py should be available
echo "✅ Code Pipeline is available at http://code-pipeline:9099"

# Set default environment variables if not already set
export OPENAI_API_BASE_URLS=${OPENAI_API_BASE_URLS:-"http://code-pipeline:9099/v1"}
export OPENAI_API_KEYS=${OPENAI_API_KEYS:-"dummy-key"}
export WEBUI_NAME=${WEBUI_NAME:-"Code WebUI"}
export ENABLE_SIGNUP=${ENABLE_SIGNUP:-"true"}

echo "📝 Configuration:"
echo "  - Pipeline URL: $OPENAI_API_BASE_URLS"
echo "  - WebUI Name: $WEBUI_NAME"
echo "  - Signup Enabled: $ENABLE_SIGNUP"

echo "✨ Open WebUI is ready!"
echo "🌐 Access it at http://localhost:3000"
echo ""
echo "💡 Quick Start:"
echo "  1. Sign up/Login at http://localhost:3000"
echo "  2. The Code Pipeline is automatically configured"
echo "  3. Select 'code-pipeline' model from the dropdown"
echo "  4. Start chatting with Claude Code!"
echo ""

# Start the original Open WebUI entrypoint
exec /app/backend/start.sh
