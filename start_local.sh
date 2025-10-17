#!/bin/bash
# Local Development Startup Script for Aspen Grade Monitor

echo "🚀 Starting Aspen Grade Monitor - Local Development"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📋 Please create a .env file with your configuration:"
    echo "   cp env.example .env"
    echo "   # Then edit .env with your TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Run tests
echo "🧪 Running local tests..."
python test_local.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests passed! Starting bot..."
    echo "📱 Open Telegram and find your bot"
    echo "💬 Send /start to begin testing"
    echo ""
    echo "🛑 Press Ctrl+C to stop the bot"
    echo ""

    # Start the bot
    python main.py
else
    echo "❌ Tests failed. Please fix the issues before running the bot."
    exit 1
fi
