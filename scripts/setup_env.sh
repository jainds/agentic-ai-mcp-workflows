#!/bin/bash

set -e

echo "🔧 Setting up Insurance AI PoC Environment"

# Check if .env file exists
if [ -f .env ]; then
    echo "📋 .env file already exists"
    source .env
    if [ -n "$OPENROUTER_API_KEY" ]; then
        echo "✅ OPENROUTER_API_KEY is already configured (${OPENROUTER_API_KEY:0:10}...)"
        exit 0
    fi
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
fi

# Prompt for API key if not set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo ""
    echo "🔑 OpenRouter API Key Setup"
    echo "You need an OpenRouter API key to use LLM features."
    echo "Get one at: https://openrouter.ai/keys"
    echo ""
    read -p "Enter your OpenRouter API key: " api_key
    
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided. Exiting."
        exit 1
    fi
    
    # Update .env file
    if grep -q "OPENROUTER_API_KEY=" .env; then
        # Replace existing line
        sed -i.bak "s/OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$api_key/" .env
    else
        # Add new line
        echo "OPENROUTER_API_KEY=$api_key" >> .env
    fi
    
    echo "✅ API key saved to .env file"
fi

echo ""
echo "🎯 Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Review your .env file: cat .env"
echo "2. Test LLM integration: python scripts/test_llm_integration.py smoke"
echo "3. Deploy to Kubernetes: ./scripts/deploy_k8s.sh"
echo ""
echo "💡 Tip: Your .env file is git-ignored for security" 