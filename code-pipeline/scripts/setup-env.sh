#!/bin/bash
# Automatically set up .env file with defaults if it doesn't exist

set -e

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

if [ -f "$ENV_FILE" ]; then
    echo "✅ .env file already exists"
    exit 0
fi

echo "📝 Creating default .env file..."

# Create .env from template with defaults
cat > "$ENV_FILE" << 'EOF'
# Code Pipeline Environment Configuration
# Auto-generated - edit as needed

# Code Binary
CODE_BINARY_PATH=/usr/local/bin/code

# Working Directory
CODE_WORKING_DIR=/data/code-workspace

# Pipeline Server
PIPELINES_PORT=9099
LOG_LEVEL=info

# LLM Provider API Keys (for Code)
# At least one is required - add your key(s) below
# Get Anthropic key from: https://console.anthropic.com/
# Get OpenAI key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Open WebUI Configuration
WEBUI_NAME=Code WebUI
ENABLE_SIGNUP=true

# Security
SANDBOX_MODE=workspace-write
APPROVAL_POLICY=on-request
EOF

echo "✅ Created .env file with defaults"
echo ""
echo "⚠️  IMPORTANT: Add your API key(s) to the .env file:"
echo "   - Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY"
echo "   - Get Anthropic key from: https://console.anthropic.com/"
echo "   - Get OpenAI key from: https://platform.openai.com/api-keys"
echo ""
echo "Then run: docker compose up -d"
