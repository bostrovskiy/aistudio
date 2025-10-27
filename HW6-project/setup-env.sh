#!/bin/bash

# OpenAI API Key Setup Script
# This script helps you set up your OpenAI API key securely

echo "🚀 OpenAI API Key Setup"
echo "======================="

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📁 .env file already exists"
    if grep -q "your_openai_api_key_here" .env; then
        echo "🔧 Updating existing .env file..."
    else
        echo "⚠️  .env file already has an API key. Do you want to overwrite it? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "❌ Setup cancelled"
            exit 0
        fi
    fi
else
    echo "📁 Creating .env file from template..."
    cp env.example .env
fi

# Get API key from user
echo ""
echo "🔑 Please enter your OpenAI API key:"
echo "   (You can find this at https://platform.openai.com/api-keys)"
read -p "API Key: " api_key

# Validate API key format
if [[ $api_key == sk-* && ${#api_key} -ge 20 ]]; then
    # Update .env file
    sed -i.bak "s/your_openai_api_key_here/$api_key/" .env
    rm .env.bak 2>/dev/null || true
    
    echo ""
    echo "✅ Setup complete!"
    echo "📁 Your API key has been saved to .env"
    echo "🔒 The .env file is excluded from git for security"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Open index.html in your browser"
    echo "   2. The app will automatically detect your API key"
    echo "   3. Start chatting with AI-powered recommendations!"
    echo ""
else
    echo ""
    echo "❌ Invalid API key format. Please ensure your key starts with 'sk-' and is at least 20 characters long."
    echo "   No changes were made to your .env file."
    echo ""
    exit 1
fi
