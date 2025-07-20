#!/bin/bash

# Slack Daily Agent Startup Script (Python Version)
# This script starts the agent and keeps it running

echo "🤖 Starting Slack Daily Agent (Python)..."
echo "📡 Agent will send jokes/trivia to #random daily at 9:00 AM"
echo "🔧 Using MCP Slack integration"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Slack Agent..."
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Check if Python dependencies are installed
if [ ! -f ".venv/bin/activate" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "📦 Installing Python dependencies..."
    pip install -e .
else
    echo "🐍 Activating Python virtual environment..."
    source .venv/bin/activate
fi

# Make the script executable
chmod +x slack_agent.py

# Start the agent
echo "🚀 Agent started! Press Ctrl+C to stop."
echo "📝 Logs will appear below:"
echo "==========================================="

python3 slack_agent.py

# Deactivate virtual environment on exit
deactivate